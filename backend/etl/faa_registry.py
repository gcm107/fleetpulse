"""FAA Aircraft Registry ETL - downloads and upserts aircraft data from the FAA Releasable Aircraft Database."""
import csv
import io
import logging
import os
import zipfile

import requests

from backend.etl.base import (
    get_db_connection,
    log_ingestion,
    now_utc,
    safe_float,
    safe_int,
)

logger = logging.getLogger(__name__)

FAA_REGISTRY_URL = "https://registry.faa.gov/database/ReleasableAircraft.zip"
EXTRACT_DIR = "/tmp/faa_aircraft"

SOURCE = "faa_registry"
SOURCE_URL = "https://registry.faa.gov/database/ReleasableAircraft.zip"

BATCH_SIZE = 5000

# ----- Decode maps -----

AIRCRAFT_TYPE_MAP = {
    "1": "Glider",
    "2": "Balloon",
    "3": "Blimp/Dirigible",
    "4": "Fixed wing single-engine",
    "5": "Fixed wing multi-engine",
    "6": "Rotorcraft",
    "7": "Weight-shift-control",
    "8": "Powered parachute",
    "9": "Gyroplane",
}

ENGINE_TYPE_MAP = {
    "0": "None",
    "1": "Reciprocating",
    "2": "Turbo-prop",
    "3": "Turbo-shaft",
    "4": "Turbo-jet",
    "5": "Turbo-fan",
    "6": "Ramjet",
    "7": "2-cycle",
    "8": "4-cycle",
    "9": "Unknown",
    "11": "Electric",
}

REGISTRANT_TYPE_MAP = {
    "1": "Individual",
    "2": "Partnership",
    "3": "Corporation",
    "4": "Co-Owned",
    "5": "Government",
    "8": "Non-Citizen Corporation",
    "9": "Non-Citizen Co-Owner",
}

STATUS_CODE_MAP = {
    "V": "Valid",
    "S": "Sale Reported",
    "D": "Revoked",
    "R": "Registration Pending",
    "X": "Expired",
    "T": "Transfer Pending",
    "M": "Multiple",
    "N": "Non-US Validated",
    "A": "Available",
}


def _detect_delimiter(first_line: str) -> str:
    """Detect whether a file is comma-delimited or pipe-delimited from the first line."""
    pipe_count = first_line.count("|")
    comma_count = first_line.count(",")
    return "|" if pipe_count > comma_count else ","


def _download_and_extract() -> str:
    """Download the FAA ReleasableAircraft.zip and extract to EXTRACT_DIR.

    Returns the extract directory path. Retries up to 3 times with backoff.
    """
    import time

    os.makedirs(EXTRACT_DIR, exist_ok=True)
    zip_path = os.path.join(EXTRACT_DIR, "ReleasableAircraft.zip")

    headers = {
        "User-Agent": "FleetPulse/1.0 (Aviation Intelligence Platform)",
        "Accept": "*/*",
    }

    for attempt in range(1, 4):
        try:
            logger.info(f"Downloading {FAA_REGISTRY_URL} (attempt {attempt}/3)")
            resp = requests.get(FAA_REGISTRY_URL, timeout=300, stream=True, headers=headers)
            resp.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)

            file_size = os.path.getsize(zip_path)
            logger.info(f"Downloaded {file_size / 1024 / 1024:.1f} MB")
            break
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            if attempt == 3:
                raise
            wait = attempt * 10
            logger.info(f"Retrying in {wait}s...")
            time.sleep(wait)

    logger.info(f"Extracting to {EXTRACT_DIR}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(EXTRACT_DIR)

    return EXTRACT_DIR


def _read_delimited_file(filepath: str) -> list[dict]:
    """Read a comma- or pipe-delimited file with headers, auto-detecting the delimiter.

    Strips whitespace from both header names and field values.
    """
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return []

    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        first_line = f.readline()
        delimiter = _detect_delimiter(first_line)
        f.seek(0)

        reader = csv.DictReader(f, delimiter=delimiter)
        # Strip header names
        if reader.fieldnames:
            reader.fieldnames = [name.strip() for name in reader.fieldnames]

        rows = []
        for row in reader:
            cleaned = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}
            rows.append(cleaned)

    return rows


def _build_acftref_lookup(extract_dir: str) -> dict:
    """Build lookup dict from ACFTREF.txt keyed by MFR MDL CODE.

    Returns dict mapping code -> {manufacturer, model, series, aircraft_type,
    engine_count, number_of_seats}.
    """
    filepath = os.path.join(extract_dir, "ACFTREF.txt")
    rows = _read_delimited_file(filepath)

    lookup = {}
    for row in rows:
        code = row.get("CODE", "").strip()
        if not code:
            continue
        lookup[code] = {
            "manufacturer": row.get("MFR", "").strip() or None,
            "model": row.get("MODEL", "").strip() or None,
            "series": row.get("SERIES", "").strip() or None,
            "aircraft_type": AIRCRAFT_TYPE_MAP.get(row.get("TYPE-ACFT", "").strip(), None),
            "engine_count": safe_int(row.get("NO-ENG", "").strip()),
            "number_of_seats": safe_int(row.get("NO-SEATS", "").strip()),
        }

    logger.info(f"Built ACFTREF lookup with {len(lookup)} entries")
    return lookup


def _build_engine_lookup(extract_dir: str) -> dict:
    """Build lookup dict from ENGINE.txt keyed by engine code.

    Returns dict mapping code -> {engine_model, engine_type}.
    """
    filepath = os.path.join(extract_dir, "ENGINE.txt")
    rows = _read_delimited_file(filepath)

    lookup = {}
    for row in rows:
        code = row.get("CODE", "").strip()
        if not code:
            continue
        lookup[code] = {
            "engine_model": row.get("MFR", "").strip() or None,
            "engine_type": ENGINE_TYPE_MAP.get(row.get("TYPE", "").strip(), None),
        }

    logger.info(f"Built ENGINE lookup with {len(lookup)} entries")
    return lookup


def _convert_mode_s_to_hex(octal_str: str) -> str | None:
    """Convert FAA MODE S CODE (octal) to transponder hex code.

    Example: '52630070' -> ''AB3038' (hex(int('52630070', 8))).
    """
    octal_str = octal_str.strip()
    if not octal_str:
        return None
    try:
        decimal_val = int(octal_str, 8)
        return hex(decimal_val)[2:].upper().zfill(6)
    except (ValueError, TypeError):
        return None


def _parse_faa_date(date_str: str):
    """Parse FAA date format YYYYMMDD into an ISO date string or None."""
    date_str = date_str.strip() if date_str else ""
    if not date_str or len(date_str) < 8:
        return None
    try:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        if year < 1900 or month < 1 or month > 12 or day < 1 or day > 31:
            return None
        return f"{year:04d}-{month:02d}-{day:02d}"
    except (ValueError, TypeError):
        return None


def _upsert_aircraft_batch(conn, batch: list[dict]) -> tuple[int, int]:
    """Upsert a batch of aircraft records.

    Returns (inserted, updated) counts.
    """
    conn.executemany(
        """
        INSERT INTO aircraft (
            n_number, serial_number, mfr_mdl_code,
            manufacturer, model, series, aircraft_type,
            engine_type, engine_model, engine_count, number_of_seats,
            year_mfr, transponder_hex,
            cert_issue_date, airworthiness_class, airworthiness_date,
            category, registration_status, country_code,
            registrant_type, registrant_name,
            registrant_street, registrant_city, registrant_state,
            registrant_zip, registrant_country,
            last_action_date, fractional_owner,
            source, source_url, ingested_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(n_number) DO UPDATE SET
            serial_number = excluded.serial_number,
            mfr_mdl_code = excluded.mfr_mdl_code,
            manufacturer = excluded.manufacturer,
            model = excluded.model,
            series = excluded.series,
            aircraft_type = excluded.aircraft_type,
            engine_type = excluded.engine_type,
            engine_model = excluded.engine_model,
            engine_count = excluded.engine_count,
            number_of_seats = excluded.number_of_seats,
            year_mfr = excluded.year_mfr,
            transponder_hex = excluded.transponder_hex,
            cert_issue_date = excluded.cert_issue_date,
            airworthiness_class = excluded.airworthiness_class,
            airworthiness_date = excluded.airworthiness_date,
            category = excluded.category,
            registration_status = excluded.registration_status,
            registrant_type = excluded.registrant_type,
            registrant_name = excluded.registrant_name,
            registrant_street = excluded.registrant_street,
            registrant_city = excluded.registrant_city,
            registrant_state = excluded.registrant_state,
            registrant_zip = excluded.registrant_zip,
            registrant_country = excluded.registrant_country,
            last_action_date = excluded.last_action_date,
            fractional_owner = excluded.fractional_owner,
            updated_at = excluded.updated_at
        """,
        batch,
    )
    conn.commit()
    return len(batch), 0


def _process_master(conn, extract_dir: str, acftref: dict, engine_lookup: dict) -> tuple[int, int, int, int]:
    """Parse MASTER.txt and upsert aircraft records.

    Returns (processed, inserted, updated, errored).
    """
    filepath = os.path.join(extract_dir, "MASTER.txt")
    rows = _read_delimited_file(filepath)

    logger.info(f"Processing {len(rows)} MASTER.txt records")

    processed = inserted = updated = errored = 0
    now = now_utc()
    batch = []

    for row in rows:
        processed += 1
        try:
            n_number = row.get("N-NUMBER", "").strip()
            if not n_number:
                errored += 1
                continue

            # Add N prefix if not present for storage
            n_number = n_number.upper()

            serial_number = row.get("SERIAL NUMBER", "").strip() or None
            mfr_mdl_code = row.get("MFR MDL CODE", "").strip() or None

            # Look up ACFTREF for manufacturer/model/series/type/seats/engines
            acft_info = acftref.get(mfr_mdl_code, {})
            manufacturer = acft_info.get("manufacturer")
            model = acft_info.get("model")
            series = acft_info.get("series")
            aircraft_type = acft_info.get("aircraft_type")

            # Override aircraft_type from MASTER if present
            master_type = row.get("TYPE AIRCRAFT", "").strip()
            if master_type:
                aircraft_type = AIRCRAFT_TYPE_MAP.get(master_type, aircraft_type)

            # Engine info: look up from ENGINE.txt via engine code, fallback to MASTER
            eng_mfr_code = row.get("ENG MFR MDL", "").strip() or None
            eng_info = engine_lookup.get(eng_mfr_code, {})
            engine_model = eng_info.get("engine_model")
            engine_type_code = row.get("TYPE ENGINE", "").strip()
            engine_type = ENGINE_TYPE_MAP.get(engine_type_code, eng_info.get("engine_type"))

            # Engine count / seats from ACFTREF, or from MASTER
            engine_count = acft_info.get("engine_count")
            number_of_seats = acft_info.get("number_of_seats")

            year_mfr = safe_int(row.get("YEAR MFR", "").strip())

            # Transponder hex from MODE S CODE (OCTAL)
            # Prefer the pre-computed hex field; fall back to octal conversion
            transponder_hex = row.get("MODE S CODE HEX", "").strip() or None
            if transponder_hex:
                transponder_hex = transponder_hex.upper()
            else:
                mode_s_octal = row.get("MODE S CODE", "").strip()
                transponder_hex = _convert_mode_s_to_hex(mode_s_octal)

            # Dates
            cert_issue_date = _parse_faa_date(row.get("CERT ISSUE DATE", ""))
            airworthiness_date = _parse_faa_date(row.get("AIR WORTH DATE", ""))
            last_action_date = _parse_faa_date(row.get("LAST ACTION DATE", ""))

            # Classification / status
            airworthiness_class = row.get("CERTIFICATION", "").strip() or None
            status_code = row.get("STATUS CODE", "").strip()
            registration_status = STATUS_CODE_MAP.get(status_code, status_code or None)

            # Registrant
            registrant_type_code = row.get("TYPE REGISTRANT", "").strip()
            registrant_type = REGISTRANT_TYPE_MAP.get(registrant_type_code, registrant_type_code or None)
            registrant_name = row.get("NAME", "").strip() or None
            registrant_street = row.get("STREET", "").strip() or None
            registrant_city = row.get("CITY", "").strip() or None
            registrant_state = row.get("STATE", "").strip() or None
            registrant_zip = row.get("ZIP CODE", "").strip() or None
            registrant_country = row.get("COUNTRY", "").strip() or None

            fractional_owner = row.get("FRACT OWNER", "").strip() or None

            batch.append((
                n_number, serial_number, mfr_mdl_code,
                manufacturer, model, series, aircraft_type,
                engine_type, engine_model, engine_count, number_of_seats,
                year_mfr, transponder_hex,
                cert_issue_date, airworthiness_class, airworthiness_date,
                None,  # category
                registration_status, "US",
                registrant_type, registrant_name,
                registrant_street, registrant_city, registrant_state,
                registrant_zip, registrant_country,
                last_action_date, fractional_owner,
                SOURCE, SOURCE_URL, now, now,
            ))

            if len(batch) >= BATCH_SIZE:
                _upsert_aircraft_batch(conn, batch)
                inserted += len(batch)
                batch = []

        except Exception as e:
            errored += 1
            logger.warning(f"Error processing aircraft N-NUMBER={row.get('N-NUMBER', '?')}: {e}")

    # Flush remaining batch
    if batch:
        _upsert_aircraft_batch(conn, batch)
        inserted += len(batch)

    logger.info(f"MASTER.txt: {processed} processed, {inserted} upserted, {errored} errors")
    return processed, inserted, updated, errored


def _process_dereg(conn, extract_dir: str) -> tuple[int, int, int]:
    """Parse DEREG.txt and insert deregistration records into tail_history.

    Returns (processed, inserted, errored).
    """
    filepath = os.path.join(extract_dir, "DEREG.txt")
    rows = _read_delimited_file(filepath)

    if not rows:
        logger.info("No DEREG.txt found or empty")
        return 0, 0, 0

    logger.info(f"Processing {len(rows)} DEREG.txt records")

    processed = inserted = errored = 0
    now = now_utc()
    batch = []

    for row in rows:
        processed += 1
        try:
            n_number = row.get("N-NUMBER", "").strip()
            if not n_number:
                errored += 1
                continue

            n_number = n_number.upper()
            serial_number = (row.get("SERIAL-NUMBER") or row.get("SERIAL NUMBER") or "").strip() or None

            # Dates
            event_date = _parse_faa_date(
                row.get("CANCEL-DATE") or row.get("CANCEL DATE") or ""
            )

            # Registrant info from deregistration record
            registrant_name = row.get("NAME", "").strip() or None
            export_country = (row.get("COUNTRY-MAIL") or row.get("COUNTRY-PHYSICAL") or row.get("COUNTRY") or "").strip() or None

            # Reason for deregistration
            reason = (row.get("INDICATOR-GROUP") or row.get("INDICATOR GROUP") or "").strip() or None

            batch.append((
                serial_number,
                n_number,
                None,  # previous_n_number
                "US",  # registration_country
                None,  # foreign_registration
                "deregistration",  # event_type
                event_date,
                reason,
                registrant_name,
                export_country,
                SOURCE,
                now,
            ))

            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    """
                    INSERT INTO tail_history (
                        serial_number, n_number, previous_n_number,
                        registration_country, foreign_registration,
                        event_type, event_date, reason,
                        registrant_name, export_country,
                        source, ingested_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    batch,
                )
                conn.commit()
                inserted += len(batch)
                batch = []

        except Exception as e:
            errored += 1
            logger.warning(f"Error processing deregistration N-NUMBER={row.get('N-NUMBER', '?')}: {e}")

    # Flush remaining batch
    if batch:
        conn.executemany(
            """
            INSERT INTO tail_history (
                serial_number, n_number, previous_n_number,
                registration_country, foreign_registration,
                event_type, event_date, reason,
                registrant_name, export_country,
                source, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch,
        )
        conn.commit()
        inserted += len(batch)

    logger.info(f"DEREG.txt: {processed} processed, {inserted} inserted, {errored} errors")
    return processed, inserted, errored


def run_faa_registry_etl(db_path: str):
    """Run the full FAA Aircraft Registry ETL pipeline.

    Downloads ReleasableAircraft.zip, parses MASTER.txt, ACFTREF.txt, ENGINE.txt,
    and DEREG.txt, then upserts data into the aircraft and tail_history tables.
    """
    started_at = now_utc()
    conn = get_db_connection(db_path)

    total_processed = total_inserted = total_updated = total_errored = 0

    try:
        # Download and extract
        extract_dir = _download_and_extract()

        # Build lookup tables
        acftref = _build_acftref_lookup(extract_dir)
        engine_lookup = _build_engine_lookup(extract_dir)

        # Process MASTER.txt -> aircraft table
        mp, mi, mu, me = _process_master(conn, extract_dir, acftref, engine_lookup)
        total_processed += mp
        total_inserted += mi
        total_updated += mu
        total_errored += me

        # Process DEREG.txt -> tail_history table
        dp, di, de_ = _process_dereg(conn, extract_dir)
        total_processed += dp
        total_inserted += di
        total_errored += de_

        log_ingestion(
            conn,
            module="faa_registry",
            source=SOURCE,
            started_at=started_at,
            records_processed=total_processed,
            records_inserted=total_inserted,
            records_updated=total_updated,
            records_errored=total_errored,
            status="completed",
            source_file="ReleasableAircraft.zip",
        )
        logger.info("FAA Registry ETL completed successfully.")

    except Exception as e:
        logger.error(f"FAA Registry ETL failed: {e}")
        log_ingestion(
            conn,
            module="faa_registry",
            source=SOURCE,
            started_at=started_at,
            records_processed=total_processed,
            records_inserted=total_inserted,
            records_updated=total_updated,
            records_errored=total_errored,
            status="failed",
            error_message=str(e),
            source_file="ReleasableAircraft.zip",
        )
        raise
    finally:
        conn.close()


def main(db_path: str = "fleetpulse.db"):
    """CLI entry point for the FAA Registry ETL."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_faa_registry_etl(db_path)


if __name__ == "__main__":
    import sys

    db = sys.argv[1] if len(sys.argv) > 1 else "fleetpulse.db"
    main(db)
