"""Weather ETL - fetches METAR and TAF data from NOAA Aviation Weather Center."""
import json
import logging
from datetime import datetime, timezone

import requests

from backend.etl.base import (
    get_db_connection,
    log_ingestion,
    now_utc,
    safe_float,
    safe_int,
)

logger = logging.getLogger(__name__)

METAR_URL = "https://aviationweather.gov/api/data/metar"
TAF_URL = "https://aviationweather.gov/api/data/taf"

SOURCE = "noaa_awc"

# Top 50 US airports by traffic for default weather fetch
TOP_50_US_AIRPORTS = [
    "KATL", "KLAX", "KORD", "KDFW", "KDEN", "KJFK", "KSFO", "KSEA", "KLAS", "KMCO",
    "KEWR", "KBOS", "KMSP", "KPHL", "KLGA", "KFLL", "KDTW", "KBWI", "KSLC", "KSAN",
    "KDCA", "KMDW", "KTPA", "KPDX", "KSTL", "KHNL", "KBNA", "KAUS", "KOAK", "KMCI",
    "KRDU", "KCLE", "KSMF", "KSJC", "KSAT", "KPIT", "KIND", "KCVG", "KCMH", "KPBI",
    "KRSW", "KABQ", "KBUF", "KMKE", "KONT", "KBDL", "KANC", "KOMA", "KRIC", "KJAX",
]


def fetch_metar(station_ids: list[str]) -> list[dict]:
    """Fetch current METAR observations from the Aviation Weather Center API.

    Args:
        station_ids: List of ICAO station identifiers (e.g. ['KJFK', 'KLAX']).

    Returns:
        List of METAR dicts with fields: rawOb, temp, dewp, wdir, wspd, wgst,
        visib, altim, clouds, fltcat, icaoId, reportTime, etc.
    """
    if not station_ids:
        return []

    ids_param = ",".join(s.strip().upper() for s in station_ids)
    try:
        resp = requests.get(
            METAR_URL,
            params={"ids": ids_param, "format": "json"},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.HTTPError as e:
        logger.error("METAR fetch failed: %s", e)
        return []
    except requests.ConnectionError as e:
        logger.error("METAR connection error: %s", e)
        return []

    data = resp.json()
    if not isinstance(data, list):
        logger.warning("Unexpected METAR response format: %s", type(data))
        return []

    logger.info("Fetched %d METAR observations", len(data))
    return data


def fetch_taf(station_ids: list[str]) -> list[dict]:
    """Fetch current TAF forecasts from the Aviation Weather Center API.

    Args:
        station_ids: List of ICAO station identifiers.

    Returns:
        List of TAF dicts with raw forecast text and parsed fields.
    """
    if not station_ids:
        return []

    ids_param = ",".join(s.strip().upper() for s in station_ids)
    try:
        resp = requests.get(
            TAF_URL,
            params={"ids": ids_param, "format": "json"},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.HTTPError as e:
        logger.error("TAF fetch failed: %s", e)
        return []
    except requests.ConnectionError as e:
        logger.error("TAF connection error: %s", e)
        return []

    data = resp.json()
    if not isinstance(data, list):
        logger.warning("Unexpected TAF response format: %s", type(data))
        return []

    logger.info("Fetched %d TAF forecasts", len(data))
    return data


def _parse_observation_time(time_val) -> str | None:
    """Parse a datetime value from the API into a standard format.

    The NOAA API may return times as ISO strings or Unix timestamps (int/float).
    """
    if time_val is None:
        return None
    try:
        if isinstance(time_val, (int, float)):
            dt = datetime.fromtimestamp(time_val, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        time_str = str(time_val)
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return str(time_val) if time_val else None


def _extract_ceiling(clouds: list | None) -> int | None:
    """Extract ceiling in feet from cloud layer data.

    Ceiling is the lowest BKN (broken) or OVC (overcast) layer.
    """
    if not clouds or not isinstance(clouds, list):
        return None

    for layer in clouds:
        if not isinstance(layer, dict):
            continue
        cover = (layer.get("cover") or "").upper()
        if cover in ("BKN", "OVC", "VV"):
            base = safe_int(layer.get("base"))
            if base is not None:
                return base * 100  # API returns in hundreds of feet
    return None


def _extract_wx_phenomena(raw_text: str | None) -> str | None:
    """Extract weather phenomena from raw METAR text (basic extraction)."""
    if not raw_text:
        return None
    # Common wx codes
    wx_codes = [
        "TS", "RA", "SN", "FG", "BR", "HZ", "DZ", "GR", "GS",
        "PE", "PL", "SG", "IC", "FZ", "SH", "MI", "BC", "PR",
        "BL", "DR", "VC", "UP", "DU", "SA", "SS", "DS", "PO",
        "SQ", "FC", "VA",
    ]
    parts = raw_text.split()
    found = []
    for part in parts:
        clean = part.lstrip("+-")
        for code in wx_codes:
            if code in clean and part not in found:
                found.append(part)
                break
    return " ".join(found) if found else None


def ingest_weather(db_path: str, station_ids: list[str]) -> dict:
    """Fetch and store METAR and TAF data for the given stations.

    Args:
        db_path: Path to the SQLite database.
        station_ids: List of ICAO station IDs to fetch weather for.

    Returns:
        Dict with counts: metars_inserted, tafs_inserted.
    """
    conn = get_db_connection(db_path)
    now = now_utc()
    metars_inserted = 0
    tafs_inserted = 0

    try:
        # Fetch data
        metars = fetch_metar(station_ids)
        tafs = fetch_taf(station_ids)

        # Build airport_id lookup: station_id -> airport.id
        placeholders = ",".join("?" for _ in station_ids)
        airport_rows = conn.execute(
            f"SELECT id, icao_code FROM airports WHERE icao_code IN ({placeholders})",
            [s.strip().upper() for s in station_ids],
        ).fetchall()
        airport_lookup = {row[1]: row[0] for row in airport_rows}

        # Ingest METARs
        for m in metars:
            station = (m.get("icaoId") or "").strip().upper()
            if not station:
                continue

            airport_id = airport_lookup.get(station)
            observation_time = _parse_observation_time(m.get("reportTime"))
            if not observation_time:
                continue

            raw_text = m.get("rawOb") or m.get("rawTaf") or None
            temperature_c = safe_float(m.get("temp"))
            dewpoint_c = safe_float(m.get("dewp"))
            wind_direction_deg = safe_int(m.get("wdir"))
            wind_speed_kts = safe_int(m.get("wspd"))
            wind_gust_kts = safe_int(m.get("wgst"))
            visibility_sm = safe_float(m.get("visib"))
            altimeter_inhg = safe_float(m.get("altim"))

            clouds = m.get("clouds")
            cloud_layers_json = json.dumps(clouds) if clouds else None
            ceiling_ft = _extract_ceiling(clouds)

            wx_phenomena = _extract_wx_phenomena(raw_text)
            flight_category = m.get("fltcat") or None

            conn.execute(
                """INSERT INTO weather_metars (
                    station_id, airport_id, observation_time, raw_text,
                    temperature_c, dewpoint_c, wind_direction_deg, wind_speed_kts,
                    wind_gust_kts, visibility_sm, altimeter_inhg, ceiling_ft,
                    cloud_layers, wx_phenomena, flight_category, source, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    station,
                    airport_id,
                    observation_time,
                    raw_text,
                    temperature_c,
                    dewpoint_c,
                    wind_direction_deg,
                    wind_speed_kts,
                    wind_gust_kts,
                    visibility_sm,
                    altimeter_inhg,
                    ceiling_ft,
                    cloud_layers_json,
                    wx_phenomena,
                    flight_category,
                    SOURCE,
                    now,
                ),
            )
            metars_inserted += 1

        # Ingest TAFs
        for t in tafs:
            station = (t.get("icaoId") or "").strip().upper()
            if not station:
                continue

            airport_id = airport_lookup.get(station)

            issue_time = _parse_observation_time(t.get("issueTime"))
            valid_from = _parse_observation_time(t.get("validTimeFrom"))
            valid_to = _parse_observation_time(t.get("validTimeTo"))

            if not issue_time or not valid_from or not valid_to:
                continue

            raw_text = t.get("rawTAF") or t.get("rawOb") or None
            forecast_periods = t.get("fcsts")
            forecast_periods_json = json.dumps(forecast_periods) if forecast_periods else None

            conn.execute(
                """INSERT INTO weather_tafs (
                    station_id, airport_id, issue_time, valid_from, valid_to,
                    raw_text, forecast_periods, source, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    station,
                    airport_id,
                    issue_time,
                    valid_from,
                    valid_to,
                    raw_text,
                    forecast_periods_json,
                    SOURCE,
                    now,
                ),
            )
            tafs_inserted += 1

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    result = {"metars_inserted": metars_inserted, "tafs_inserted": tafs_inserted}
    logger.info("Weather ingestion complete: %s", result)
    return result


def run_weather_etl(db_path: str, stations: list[str] | None = None):
    """Run the weather ETL pipeline.

    If no stations are provided, fetches weather for the top 50 US airports.

    Args:
        db_path: Path to the SQLite database.
        stations: Optional list of ICAO station IDs. Defaults to TOP_50_US_AIRPORTS.
    """
    started_at = now_utc()
    station_ids = stations or TOP_50_US_AIRPORTS

    conn = None
    total_inserted = 0
    total_errored = 0

    try:
        result = ingest_weather(db_path, station_ids)
        total_inserted = result["metars_inserted"] + result["tafs_inserted"]

        conn = get_db_connection(db_path)
        log_ingestion(
            conn,
            module="weather",
            source=SOURCE,
            started_at=started_at,
            records_processed=len(station_ids),
            records_inserted=total_inserted,
            records_errored=total_errored,
            status="completed",
        )
        logger.info("Weather ETL completed successfully.")

    except Exception as e:
        logger.error("Weather ETL failed: %s", e)
        if conn is None:
            conn = get_db_connection(db_path)
        log_ingestion(
            conn,
            module="weather",
            source=SOURCE,
            started_at=started_at,
            records_processed=len(station_ids),
            records_inserted=total_inserted,
            records_errored=total_errored,
            status="failed",
            error_message=str(e),
        )
        raise
    finally:
        if conn is not None:
            conn.close()


def main(db_path: str = "fleetpulse.db"):
    """CLI entry point for the Weather ETL."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_weather_etl(db_path)


if __name__ == "__main__":
    import sys

    db = sys.argv[1] if len(sys.argv) > 1 else "fleetpulse.db"
    main(db)
