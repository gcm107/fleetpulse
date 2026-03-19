"""Operator ETL - ingest operator data from CSV files and generate sample data."""
import csv
import logging
import re

from backend.etl.base import (
    get_db_connection,
    log_ingestion,
    now_utc,
    safe_int,
)

logger = logging.getLogger(__name__)

SOURCE = "faa_operator_csv"


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

_CERT_TYPE_MAP = {
    "135": "part_135",
    "part 135": "part_135",
    "part135": "part_135",
    "p135": "part_135",
    "121": "part_121",
    "part 121": "part_121",
    "part121": "part_121",
    "p121": "part_121",
    "91k": "part_91k",
    "part 91k": "part_91k",
    "part91k": "part_91k",
    "91": "part_91",
    "part 91": "part_91",
    "part91": "part_91",
    "125": "part_125",
    "part 125": "part_125",
    "part125": "part_125",
    "129": "part_129",
    "part 129": "part_129",
    "part129": "part_129",
    "133": "part_133",
    "part 133": "part_133",
    "137": "part_137",
    "part 137": "part_137",
}


def normalize_certificate_type(raw: str) -> str:
    """Normalize certificate type strings to a canonical form."""
    if not raw:
        return raw
    key = re.sub(r"[_\-]+", " ", raw.strip()).lower()
    return _CERT_TYPE_MAP.get(key, raw.strip().lower())


_STATUS_MAP = {
    "active": "active",
    "a": "active",
    "act": "active",
    "suspended": "suspended",
    "s": "suspended",
    "susp": "suspended",
    "revoked": "revoked",
    "r": "revoked",
    "rev": "revoked",
    "inactive": "inactive",
    "i": "inactive",
    "surrendered": "surrendered",
    "expired": "expired",
    "pending": "pending",
}


def normalize_status(raw: str) -> str:
    """Normalize certificate status strings to a canonical form."""
    if not raw:
        return raw
    key = raw.strip().lower()
    return _STATUS_MAP.get(key, raw.strip().lower())


def _parse_bool(val) -> int:
    """Convert various boolean-ish values to 0 or 1."""
    if val is None or val == "":
        return 0
    if isinstance(val, bool):
        return 1 if val else 0
    s = str(val).strip().lower()
    return 1 if s in ("1", "true", "yes", "y", "t") else 0


# ---------------------------------------------------------------------------
# CSV ingestion
# ---------------------------------------------------------------------------

def _upsert_operators_from_csv(conn, csv_path: str) -> tuple[int, int, int, int]:
    """Read a CSV file and upsert operators.

    Expected CSV columns (case-insensitive, underscored):
        certificate_number, certificate_type, holder_name, dba_name,
        street_address, city, state, zip_code, country_code, phone,
        certificate_issue_date, certificate_expiration_date,
        certificate_status, dot_fitness_date, dot_fitness_status,
        district_office, operations_base, wet_lease_authority,
        dry_lease_authority, on_demand_authority, scheduled_authority,
        authorized_aircraft_count

    Returns (processed, inserted, updated, errored).
    """
    processed = inserted = updated = errored = 0
    now = now_utc()

    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        # Normalize header names: lowercase and strip whitespace
        if reader.fieldnames:
            reader.fieldnames = [
                f.strip().lower().replace(" ", "_") for f in reader.fieldnames
            ]

        for row in reader:
            processed += 1
            try:
                cert_number = (row.get("certificate_number") or "").strip()
                cert_type = normalize_certificate_type(
                    row.get("certificate_type", "")
                )
                holder_name = (row.get("holder_name") or "").strip()

                if not cert_number or not cert_type or not holder_name:
                    errored += 1
                    logger.warning(
                        f"Row {processed}: missing required field "
                        f"(cert={cert_number!r}, type={cert_type!r}, name={holder_name!r})"
                    )
                    continue

                status = normalize_status(row.get("certificate_status", ""))

                cursor = conn.execute(
                    "SELECT 1 FROM operators WHERE certificate_number = ?",
                    (cert_number,),
                )
                exists = cursor.fetchone() is not None

                conn.execute(
                    """
                    INSERT INTO operators (
                        certificate_number, certificate_type, holder_name,
                        dba_name, street_address, city, state, zip_code,
                        country_code, phone,
                        certificate_issue_date, certificate_expiration_date,
                        certificate_status, dot_fitness_date, dot_fitness_status,
                        district_office, operations_base,
                        wet_lease_authority, dry_lease_authority,
                        on_demand_authority, scheduled_authority,
                        authorized_aircraft_count,
                        source, source_url, ingested_at, updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?
                    )
                    ON CONFLICT(certificate_number) DO UPDATE SET
                        certificate_type = excluded.certificate_type,
                        holder_name = excluded.holder_name,
                        dba_name = excluded.dba_name,
                        street_address = excluded.street_address,
                        city = excluded.city,
                        state = excluded.state,
                        zip_code = excluded.zip_code,
                        country_code = excluded.country_code,
                        phone = excluded.phone,
                        certificate_issue_date = excluded.certificate_issue_date,
                        certificate_expiration_date = excluded.certificate_expiration_date,
                        certificate_status = excluded.certificate_status,
                        dot_fitness_date = excluded.dot_fitness_date,
                        dot_fitness_status = excluded.dot_fitness_status,
                        district_office = excluded.district_office,
                        operations_base = excluded.operations_base,
                        wet_lease_authority = excluded.wet_lease_authority,
                        dry_lease_authority = excluded.dry_lease_authority,
                        on_demand_authority = excluded.on_demand_authority,
                        scheduled_authority = excluded.scheduled_authority,
                        authorized_aircraft_count = excluded.authorized_aircraft_count,
                        source = excluded.source,
                        updated_at = excluded.updated_at
                    """,
                    (
                        cert_number,
                        cert_type,
                        holder_name,
                        (row.get("dba_name") or "").strip() or None,
                        (row.get("street_address") or "").strip() or None,
                        (row.get("city") or "").strip() or None,
                        (row.get("state") or "").strip().upper() or None,
                        (row.get("zip_code") or "").strip() or None,
                        (row.get("country_code") or "US").strip().upper(),
                        (row.get("phone") or "").strip() or None,
                        (row.get("certificate_issue_date") or "").strip() or None,
                        (row.get("certificate_expiration_date") or "").strip() or None,
                        status,
                        (row.get("dot_fitness_date") or "").strip() or None,
                        (row.get("dot_fitness_status") or "").strip() or None,
                        (row.get("district_office") or "").strip() or None,
                        (row.get("operations_base") or "").strip() or None,
                        _parse_bool(row.get("wet_lease_authority")),
                        _parse_bool(row.get("dry_lease_authority")),
                        _parse_bool(row.get("on_demand_authority")),
                        _parse_bool(row.get("scheduled_authority")),
                        safe_int(row.get("authorized_aircraft_count")),
                        SOURCE,
                        None,  # source_url
                        now,
                        now,
                    ),
                )

                if exists:
                    updated += 1
                else:
                    inserted += 1

            except Exception as e:
                errored += 1
                logger.warning(
                    f"Error processing operator row {processed}: {e}"
                )

    conn.commit()
    return processed, inserted, updated, errored


def run_operator_etl(db_path: str, csv_path: str):
    """Run the operator CSV ETL pipeline."""
    started_at = now_utc()
    conn = get_db_connection(db_path)

    try:
        logger.info(f"Ingesting operators from {csv_path}")
        processed, ins, upd, err = _upsert_operators_from_csv(conn, csv_path)
        logger.info(
            f"Operators: {processed} processed, {ins} inserted, "
            f"{upd} updated, {err} errors"
        )

        log_ingestion(
            conn,
            module="operators",
            source=SOURCE,
            started_at=started_at,
            records_processed=processed,
            records_inserted=ins,
            records_updated=upd,
            records_errored=err,
            status="completed",
            source_file=csv_path,
        )
        logger.info("Operator ETL completed successfully.")

    except Exception as e:
        logger.error(f"Operator ETL failed: {e}")
        log_ingestion(
            conn,
            module="operators",
            source=SOURCE,
            started_at=started_at,
            records_processed=0,
            records_inserted=0,
            records_updated=0,
            records_errored=0,
            status="failed",
            error_message=str(e),
            source_file=csv_path,
        )
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Sample data generation
# ---------------------------------------------------------------------------

SAMPLE_OPERATORS = [
    # (cert_number, cert_type, holder_name, dba_name, street, city, state, zip, phone,
    #  issue_date, status, dot_fitness_status, district_office, ops_base,
    #  wet, dry, on_demand, scheduled, aircraft_count)
    ("XOJA135A", "part_135", "XOJet Inc", "XO", "2000 Sierra Point Pkwy", "Brisbane", "CA", "94005",
     "650-588-2600", "2008-03-15", "active", "satisfactory", "WP-19", "KSFO",
     1, 0, 1, 0, 42),
    ("NJAA135A", "part_135", "NetJets Aviation Inc", "NetJets", "4111 Bridgeway Ave", "Columbus", "OH", "43219",
     "614-239-5500", "1998-06-01", "active", "satisfactory", "GL-33", "KCMH",
     1, 1, 1, 0, 750),
    ("FLEX135A", "part_135", "Flexjet LLC", "Flexjet", "3300 S Service Rd", "Burlington", "ON", "44130",
     "866-353-9538", "2004-09-12", "active", "satisfactory", "GL-33", "KCLE",
     1, 1, 1, 0, 230),
    ("EXCA135A", "part_135", "ExcelAire Service Inc", None, "100 New Highway", "Ronkonkoma", "NY", "11779",
     "631-737-8900", "2001-11-20", "active", "satisfactory", "EA-16", "KISP",
     0, 0, 1, 0, 18),
    ("JETF135A", "part_135", "Jet Aviation Flight Services Inc", "Jet Aviation",
     "236 Riser Rd", "Teterboro", "NJ", "07608",
     "201-462-4100", "1995-04-10", "active", "satisfactory", "EA-16", "KTEB",
     1, 0, 1, 0, 55),
    ("WFLT135A", "part_135", "Wheels Up Partners LLC", "Wheels Up",
     "601 W 26th St", "New York", "NY", "10001",
     "212-257-5400", "2015-07-01", "active", "satisfactory", "EA-16", "KTEB",
     1, 0, 1, 0, 190),
    ("VIST135A", "part_135", "VistaJet Ltd", "VistaJet US", "800 Brickell Key Dr", "Miami", "FL", "33131",
     "305-400-5100", "2012-05-18", "active", "satisfactory", "SO-23", "KOPF",
     1, 1, 1, 0, 85),
    ("SENT135A", "part_135", "Sentient Jet LLC", "Sentient Jet",
     "55 Lane Rd", "Fairfield", "NJ", "07004",
     "973-396-0300", "2006-02-28", "active", "satisfactory", "EA-16", "KTEB",
     0, 0, 1, 0, 0),
    ("MAGG135A", "part_135", "Magellan Jets LLC", None, "200 Hanscom Dr", "Bedford", "MA", "01730",
     "781-535-6525", "2008-10-15", "active", "satisfactory", "NE-13", "KBED",
     0, 0, 1, 0, 0),
    ("CLAY135A", "part_135", "Clay Lacy Aviation Inc", "Clay Lacy",
     "7435 Valjean Ave", "Van Nuys", "CA", "91406",
     "818-989-2900", "1968-08-01", "active", "satisfactory", "WP-19", "KVNY",
     1, 0, 1, 0, 65),
    ("PREM135A", "part_135", "Priester Aviation LLC", "Priester Aviation",
     "1300 Soldiers Field Dr", "Wheeling", "IL", "60090",
     "847-537-1200", "1992-03-25", "active", "satisfactory", "GL-33", "KPWK",
     1, 0, 1, 0, 40),
    ("SURF135A", "part_135", "Surf Air Mobility Inc", "Surf Air",
     "12180 Millennium Dr", "Los Angeles", "CA", "90094",
     "310-496-3200", "2017-01-10", "active", "satisfactory", "WP-19", "KHHR",
     0, 0, 1, 1, 22),
    ("SOAR121A", "part_121", "Southern Air Inc", "Southern Air",
     "100 N Riverside Dr", "Florence", "KY", "41042",
     "859-283-2000", "1999-12-01", "active", "satisfactory", "GL-33", "KCVG",
     0, 0, 0, 1, 15),
    ("ATLS121A", "part_121", "Atlas Air Inc", "Atlas Air",
     "2000 Westchester Ave", "Purchase", "NY", "10577",
     "914-701-8000", "1993-01-15", "active", "satisfactory", "EA-16", "KJFK",
     1, 1, 0, 1, 110),
    ("KALM121A", "part_121", "Kalitta Air LLC", "Kalitta Air",
     "818 Willow Run Airport", "Ypsilanti", "MI", "48198",
     "734-544-7100", "2000-11-30", "active", "satisfactory", "GL-33", "KYIP",
     1, 1, 0, 1, 28),
    ("FRKN91KA", "part_91k", "Flexjet Fractional Program", "Flexjet Fractional",
     "3300 S Service Rd", "Cleveland", "OH", "44130",
     "866-353-9538", "2004-09-12", "active", "satisfactory", "GL-33", "KCLE",
     0, 0, 1, 0, 120),
    ("NJFR91KA", "part_91k", "NetJets Fractional Sales Inc", "NetJets Fractional",
     "4111 Bridgeway Ave", "Columbus", "OH", "43219",
     "614-239-5500", "2003-01-20", "active", "satisfactory", "GL-33", "KCMH",
     0, 0, 1, 0, 450),
    ("SUSP135A", "part_135", "Swift Charter Corp", None,
     "500 Industrial Blvd", "Dallas", "TX", "75207",
     "214-555-0100", "2010-06-15", "suspended", "unsatisfactory", "SW-27", "KDAL",
     0, 0, 1, 0, 5),
    ("REVK135A", "part_135", "AeroDynamic Charter LLC", None,
     "1234 Aviation Way", "Phoenix", "AZ", "85034",
     "602-555-0200", "2007-11-01", "revoked", "unsatisfactory", "WP-19", "KPHX",
     0, 0, 1, 0, 0),
    ("EXPR135A", "part_135", "Pacific Island Air LLC", None,
     "300 Airport Rd", "Honolulu", "HI", "96819",
     "808-555-0300", "2002-04-20", "expired", "not_assessed", "WP-19", "PHNL",
     0, 0, 1, 0, 3),
]


def generate_sample_operators(db_path: str):
    """Insert sample operator records for demo and development purposes."""
    started_at = now_utc()
    conn = get_db_connection(db_path)
    now = now_utc()
    inserted = updated = errored = 0

    try:
        for op in SAMPLE_OPERATORS:
            (
                cert_number, cert_type, holder_name, dba_name,
                street, city, state, zip_code, phone,
                issue_date, status, dot_fitness_status,
                district_office, ops_base,
                wet, dry, on_demand, scheduled, aircraft_count,
            ) = op

            try:
                cursor = conn.execute(
                    "SELECT 1 FROM operators WHERE certificate_number = ?",
                    (cert_number,),
                )
                exists = cursor.fetchone() is not None

                conn.execute(
                    """
                    INSERT INTO operators (
                        certificate_number, certificate_type, holder_name,
                        dba_name, street_address, city, state, zip_code,
                        country_code, phone,
                        certificate_issue_date, certificate_expiration_date,
                        certificate_status, dot_fitness_date, dot_fitness_status,
                        district_office, operations_base,
                        wet_lease_authority, dry_lease_authority,
                        on_demand_authority, scheduled_authority,
                        authorized_aircraft_count,
                        source, source_url, ingested_at, updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?
                    )
                    ON CONFLICT(certificate_number) DO UPDATE SET
                        certificate_type = excluded.certificate_type,
                        holder_name = excluded.holder_name,
                        dba_name = excluded.dba_name,
                        street_address = excluded.street_address,
                        city = excluded.city,
                        state = excluded.state,
                        zip_code = excluded.zip_code,
                        country_code = excluded.country_code,
                        phone = excluded.phone,
                        certificate_issue_date = excluded.certificate_issue_date,
                        certificate_status = excluded.certificate_status,
                        dot_fitness_status = excluded.dot_fitness_status,
                        district_office = excluded.district_office,
                        operations_base = excluded.operations_base,
                        wet_lease_authority = excluded.wet_lease_authority,
                        dry_lease_authority = excluded.dry_lease_authority,
                        on_demand_authority = excluded.on_demand_authority,
                        scheduled_authority = excluded.scheduled_authority,
                        authorized_aircraft_count = excluded.authorized_aircraft_count,
                        updated_at = excluded.updated_at
                    """,
                    (
                        cert_number,
                        cert_type,
                        holder_name,
                        dba_name,
                        street,
                        city,
                        state,
                        zip_code,
                        "US",
                        phone,
                        issue_date,
                        None,  # certificate_expiration_date
                        status,
                        None,  # dot_fitness_date
                        dot_fitness_status,
                        district_office,
                        ops_base,
                        wet,
                        dry,
                        on_demand,
                        scheduled,
                        aircraft_count,
                        "sample_data",
                        None,  # source_url
                        now,
                        now,
                    ),
                )

                if exists:
                    updated += 1
                else:
                    inserted += 1

            except Exception as e:
                errored += 1
                logger.warning(f"Error inserting sample operator {cert_number}: {e}")

        conn.commit()

        total = len(SAMPLE_OPERATORS)
        logger.info(
            f"Sample operators: {total} processed, {inserted} inserted, "
            f"{updated} updated, {errored} errors"
        )

        log_ingestion(
            conn,
            module="operators",
            source="sample_data",
            started_at=started_at,
            records_processed=total,
            records_inserted=inserted,
            records_updated=updated,
            records_errored=errored,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Sample operator generation failed: {e}")
        log_ingestion(
            conn,
            module="operators",
            source="sample_data",
            started_at=started_at,
            records_processed=0,
            records_inserted=0,
            records_updated=0,
            records_errored=0,
            status="failed",
            error_message=str(e),
        )
        raise
    finally:
        conn.close()


def main(db_path: str = "fleetpulse.db", csv_path: str | None = None):
    """CLI entry point for the operator ETL.

    If a csv_path is provided, runs the CSV ingestion ETL.
    Otherwise, generates sample operator data.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    if csv_path:
        run_operator_etl(db_path, csv_path)
    else:
        logger.info("No CSV path provided, generating sample operators.")
        generate_sample_operators(db_path)


if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "fleetpulse.db"
    csv = sys.argv[2] if len(sys.argv) > 2 else None
    main(db, csv)
