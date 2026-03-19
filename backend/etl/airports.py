"""Airport ETL - downloads and upserts airport, runway, and frequency data from OurAirports."""
import csv
import io
import logging

import requests

from backend.etl.base import (
    get_db_connection,
    log_ingestion,
    now_utc,
    safe_float,
    safe_int,
)

logger = logging.getLogger(__name__)

AIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
RUNWAYS_URL = "https://davidmegginson.github.io/ourairports-data/runways.csv"
FREQUENCIES_URL = "https://davidmegginson.github.io/ourairports-data/airport-frequencies.csv"

SOURCE = "ourairports"


def _download_csv(url: str) -> list[dict]:
    """Download a CSV from a URL and return a list of dicts."""
    logger.info(f"Downloading {url}")
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    return list(reader)


def _upsert_airports(conn, rows: list[dict]) -> tuple[int, int, int, int]:
    """Upsert airports into the airports table.

    Returns (processed, inserted, updated, errored).
    """
    processed = inserted = updated = errored = 0
    now = now_utc()

    for row in rows:
        processed += 1
        try:
            icao_code = row.get("ident", "").strip()
            if not icao_code:
                errored += 1
                continue

            lat = safe_float(row.get("latitude_deg"))
            lon = safe_float(row.get("longitude_deg"))
            if lat is None or lon is None:
                errored += 1
                continue

            name = row.get("name", "").strip() or "Unknown"
            airport_type = row.get("type", "").strip() or "unknown"
            iata_code = row.get("iata_code", "").strip() or None
            country_code = row.get("iso_country", "").strip() or "XX"

            faa_lid = None
            if country_code == "US":
                faa_lid = row.get("local_code", "").strip() or None

            iso_region = row.get("iso_region", "").strip() or ""
            state_province = iso_region.split("-", 1)[1] if "-" in iso_region else (iso_region or None)

            city = row.get("municipality", "").strip() or None
            continent = row.get("continent", "").strip() or None
            elevation_ft = safe_int(row.get("elevation_ft"))

            cursor = conn.execute(
                "SELECT 1 FROM airports WHERE icao_code = ?", (icao_code,)
            )
            exists = cursor.fetchone() is not None

            conn.execute(
                """
                INSERT INTO airports (
                    icao_code, iata_code, faa_lid, name, airport_type,
                    city, state_province, country_code, continent,
                    latitude, longitude, elevation_ft,
                    source, ingested_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(icao_code) DO UPDATE SET
                    iata_code = excluded.iata_code,
                    faa_lid = excluded.faa_lid,
                    name = excluded.name,
                    airport_type = excluded.airport_type,
                    city = excluded.city,
                    state_province = excluded.state_province,
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    elevation_ft = excluded.elevation_ft,
                    updated_at = excluded.updated_at
                """,
                (
                    icao_code, iata_code, faa_lid, name, airport_type,
                    city, state_province, country_code, continent,
                    lat, lon, elevation_ft,
                    SOURCE, now, now,
                ),
            )

            if exists:
                updated += 1
            else:
                inserted += 1

        except Exception as e:
            errored += 1
            logger.warning(f"Error processing airport {row.get('ident', '?')}: {e}")

    conn.commit()
    return processed, inserted, updated, errored


def _build_airport_ident_lookup(conn) -> dict[str, int]:
    """Build a mapping of icao_code -> airport id."""
    cursor = conn.execute("SELECT id, icao_code FROM airports")
    return {row[1]: row[0] for row in cursor.fetchall()}


def _insert_runways(conn, rows: list[dict], ident_to_id: dict[str, int]) -> tuple[int, int, int]:
    """Insert runways linked to airports. Returns (processed, inserted, errored)."""
    processed = inserted = errored = 0
    now = now_utc()

    conn.execute("DELETE FROM runways")

    for row in rows:
        processed += 1
        try:
            airport_ident = row.get("airport_ident", "").strip()
            airport_id = ident_to_id.get(airport_ident)
            if airport_id is None:
                continue

            conn.execute(
                """
                INSERT INTO runways (
                    airport_id, runway_id_le, runway_id_he,
                    length_ft, width_ft, surface_type,
                    is_lighted, is_closed,
                    le_latitude, le_longitude, le_elevation_ft,
                    le_displaced_threshold_ft,
                    he_latitude, he_longitude, he_elevation_ft,
                    he_displaced_threshold_ft,
                    source, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    airport_id,
                    row.get("le_ident", "").strip() or None,
                    row.get("he_ident", "").strip() or None,
                    safe_int(row.get("length_ft")),
                    safe_int(row.get("width_ft")),
                    row.get("surface", "").strip() or None,
                    1 if row.get("lighted", "0") == "1" else 0,
                    1 if row.get("closed", "0") == "1" else 0,
                    safe_float(row.get("le_latitude_deg")),
                    safe_float(row.get("le_longitude_deg")),
                    safe_int(row.get("le_elevation_ft")),
                    safe_int(row.get("le_displaced_threshold_ft")),
                    safe_float(row.get("he_latitude_deg")),
                    safe_float(row.get("he_longitude_deg")),
                    safe_int(row.get("he_elevation_ft")),
                    safe_int(row.get("he_displaced_threshold_ft")),
                    SOURCE, now,
                ),
            )
            inserted += 1

        except Exception as e:
            errored += 1
            logger.warning(f"Error processing runway: {e}")

    conn.commit()
    return processed, inserted, errored


def _insert_frequencies(conn, rows: list[dict], ident_to_id: dict[str, int]) -> tuple[int, int, int]:
    """Insert frequencies linked to airports. Returns (processed, inserted, errored)."""
    processed = inserted = errored = 0
    now = now_utc()

    conn.execute("DELETE FROM airport_frequencies")

    for row in rows:
        processed += 1
        try:
            airport_ident = row.get("airport_ident", "").strip()
            airport_id = ident_to_id.get(airport_ident)
            if airport_id is None:
                continue

            freq_mhz = safe_float(row.get("frequency_mhz"))
            if freq_mhz is None:
                errored += 1
                continue

            conn.execute(
                """
                INSERT INTO airport_frequencies (
                    airport_id, frequency_type, frequency_mhz,
                    description, source, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    airport_id,
                    row.get("type", "").strip().upper() or "OTHER",
                    freq_mhz,
                    row.get("description", "").strip() or None,
                    SOURCE, now,
                ),
            )
            inserted += 1

        except Exception as e:
            errored += 1
            logger.warning(f"Error processing frequency: {e}")

    conn.commit()
    return processed, inserted, errored


def run_airport_etl(db_path: str):
    """Run the full airport ETL pipeline: airports, runways, frequencies."""
    started_at = now_utc()
    conn = get_db_connection(db_path)

    total_processed = total_inserted = total_updated = total_errored = 0

    try:
        logger.info("Downloading airports...")
        airport_rows = _download_csv(AIRPORTS_URL)
        logger.info(f"Downloaded {len(airport_rows)} airport records")

        ap, ai, au, ae = _upsert_airports(conn, airport_rows)
        total_processed += ap
        total_inserted += ai
        total_updated += au
        total_errored += ae
        logger.info(f"Airports: {ap} processed, {ai} inserted, {au} updated, {ae} errors")

        ident_to_id = _build_airport_ident_lookup(conn)

        logger.info("Downloading runways...")
        runway_rows = _download_csv(RUNWAYS_URL)
        logger.info(f"Downloaded {len(runway_rows)} runway records")

        rp, ri, re_ = _insert_runways(conn, runway_rows, ident_to_id)
        total_processed += rp
        total_inserted += ri
        total_errored += re_
        logger.info(f"Runways: {rp} processed, {ri} inserted, {re_} errors")

        logger.info("Downloading frequencies...")
        freq_rows = _download_csv(FREQUENCIES_URL)
        logger.info(f"Downloaded {len(freq_rows)} frequency records")

        fp, fi, fe = _insert_frequencies(conn, freq_rows, ident_to_id)
        total_processed += fp
        total_inserted += fi
        total_errored += fe
        logger.info(f"Frequencies: {fp} processed, {fi} inserted, {fe} errors")

        log_ingestion(
            conn, module="airports", source=SOURCE, started_at=started_at,
            records_processed=total_processed, records_inserted=total_inserted,
            records_updated=total_updated, records_errored=total_errored,
            status="completed",
        )
        logger.info("Airport ETL completed successfully.")

    except Exception as e:
        logger.error(f"Airport ETL failed: {e}")
        log_ingestion(
            conn, module="airports", source=SOURCE, started_at=started_at,
            records_processed=total_processed, records_inserted=total_inserted,
            records_updated=total_updated, records_errored=total_errored,
            status="failed", error_message=str(e),
        )
        raise
    finally:
        conn.close()


def main(db_path: str = "fleetpulse.db"):
    """CLI entry point for the airport ETL."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_airport_etl(db_path)


if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "fleetpulse.db"
    main(db)
