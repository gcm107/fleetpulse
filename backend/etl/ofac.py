"""OFAC SDN List ETL - download and cross-reference the OFAC Specially
Designated Nationals list against the FleetPulse aircraft registry.

The primary data source is the SDN CSV published by OFAC/Treasury:
  https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV

Aircraft tail numbers are extracted from the Remarks column (pattern:
``N`` followed by digits and optional letters) and matched against the
``aircraft`` table.  Owner/registrant names are also compared against
SDN entity names for lower-confidence matches.

A ``generate_sample_ofac_data`` function is provided for demonstration
and testing purposes.
"""

import csv
import io
import logging
import random
import re
import urllib.request
from datetime import datetime, timezone

from backend.etl.base import get_db_connection, log_ingestion, now_utc

logger = logging.getLogger(__name__)

SDN_CSV_URL = (
    "https://sanctionslistservice.ofac.treas.gov"
    "/api/PublicationPreview/exports/SDN.CSV"
)
SOURCE = "ofac_sdn"

# Regex to find US tail numbers in OFAC remarks
_TAIL_RE = re.compile(r"\bN\d+[A-Z]*\b")


# ---------------------------------------------------------------------------
# CSV download & parse
# ---------------------------------------------------------------------------

def _download_sdn_csv() -> list[dict]:
    """Download SDN.CSV and return a list of row dicts.

    The CSV has no header row.  Columns are positional:
        0  ent_num        – SDN entry ID (integer)
        1  SDN_Name       – primary name
        2  SDN_Type       – entity type (e.g. "individual", "vessel", "aircraft")
        3  Program        – sanctions programme
        4  Title          – title (often empty)
        5  Call_Sign
        6  Vess_type
        7  Tonnage
        8  GRT
        9  Vess_flag
       10  Vess_owner
       11  Remarks
    """
    logger.info("Downloading SDN CSV from %s", SDN_CSV_URL)
    req = urllib.request.Request(SDN_CSV_URL, headers={"User-Agent": "FleetPulse/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    rows: list[dict] = []
    reader = csv.reader(io.StringIO(raw))
    for line in reader:
        if len(line) < 12:
            continue
        entry_id_str = line[0].strip().strip('"')
        try:
            entry_id = int(entry_id_str)
        except (ValueError, TypeError):
            continue
        remarks = line[11].strip().strip('"') if len(line) > 11 else ""
        tail_numbers = _TAIL_RE.findall(remarks)
        rows.append({
            "sdn_entry_id": entry_id,
            "sdn_type": line[2].strip().strip('"') or None,
            "primary_name": line[1].strip().strip('"') or None,
            "program_list": line[3].strip().strip('"') or None,
            "country": None,  # not in the base CSV; derived from remarks/alt
            "remarks": remarks or None,
            "aircraft_tail_numbers": ",".join(tail_numbers) if tail_numbers else None,
            "aircraft_type": None,
        })
    logger.info("Parsed %d SDN entries from CSV", len(rows))
    return rows


# ---------------------------------------------------------------------------
# SDN ingestion
# ---------------------------------------------------------------------------

def _ingest_sdn_entries(conn, entries: list[dict]) -> tuple[int, int, int]:
    """Insert/update SDN entries.  Returns (inserted, updated, errored)."""
    inserted = updated = errored = 0
    now = now_utc()
    for entry in entries:
        try:
            conn.execute(
                """
                INSERT INTO ofac_sdn (
                    sdn_entry_id, sdn_type, primary_name, program_list,
                    country, remarks, aircraft_tail_numbers, aircraft_type,
                    source, source_url, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sdn_entry_id) DO UPDATE SET
                    sdn_type = excluded.sdn_type,
                    primary_name = excluded.primary_name,
                    program_list = excluded.program_list,
                    country = excluded.country,
                    remarks = excluded.remarks,
                    aircraft_tail_numbers = excluded.aircraft_tail_numbers,
                    aircraft_type = excluded.aircraft_type,
                    source = excluded.source,
                    source_url = excluded.source_url,
                    ingested_at = excluded.ingested_at
                """,
                (
                    entry["sdn_entry_id"],
                    entry["sdn_type"],
                    entry["primary_name"],
                    entry["program_list"],
                    entry["country"],
                    entry["remarks"],
                    entry["aircraft_tail_numbers"],
                    entry["aircraft_type"],
                    SOURCE,
                    SDN_CSV_URL,
                    now,
                ),
            )
            # Determine if it was insert or update
            changes = conn.execute("SELECT changes()").fetchone()[0]
            if changes:
                inserted += 1
        except Exception as e:
            errored += 1
            logger.warning("Error ingesting SDN entry %s: %s", entry.get("sdn_entry_id"), e)
    conn.commit()
    return inserted, updated, errored


# ---------------------------------------------------------------------------
# Cross-reference matching
# ---------------------------------------------------------------------------

def _cross_reference(conn) -> tuple[int, int]:
    """Match SDN entries against the aircraft table.

    Match strategies:
      1. Exact tail-number match (confidence 1.0)
      2. Owner/registrant name contains match (confidence 0.5–0.8)

    Returns (matches_inserted, errors).
    """
    now = now_utc()
    matches_inserted = 0
    errors = 0

    # --- 1. Tail number matches ---
    sdn_rows = conn.execute(
        "SELECT id, sdn_entry_id, aircraft_tail_numbers, primary_name "
        "FROM ofac_sdn WHERE aircraft_tail_numbers IS NOT NULL AND aircraft_tail_numbers != ''"
    ).fetchall()

    for sdn_id, sdn_entry_id, tail_csv, primary_name in sdn_rows:
        tails = [t.strip() for t in tail_csv.split(",") if t.strip()]
        for tail in tails:
            aircraft_rows = conn.execute(
                "SELECT id, n_number FROM aircraft WHERE n_number = ?",
                (tail,),
            ).fetchall()
            for aircraft_id, n_number in aircraft_rows:
                try:
                    conn.execute(
                        """
                        INSERT INTO ofac_matches (
                            aircraft_id, sdn_id, match_type, match_confidence,
                            matched_value, sdn_value, is_confirmed,
                            source, ingested_at
                        ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                        """,
                        (
                            aircraft_id,
                            sdn_id,
                            "tail_number",
                            1.0,
                            n_number,
                            tail,
                            SOURCE,
                            now,
                        ),
                    )
                    matches_inserted += 1
                except Exception as e:
                    errors += 1
                    logger.warning("Error inserting tail match: %s", e)

    # --- 2. Owner name matches ---
    sdn_name_rows = conn.execute(
        "SELECT id, sdn_entry_id, primary_name FROM ofac_sdn "
        "WHERE primary_name IS NOT NULL AND primary_name != ''"
    ).fetchall()

    for sdn_id, sdn_entry_id, sdn_name in sdn_name_rows:
        if not sdn_name or len(sdn_name) < 4:
            continue
        sdn_upper = sdn_name.upper()
        # Search aircraft registrant names that contain the SDN name
        aircraft_rows = conn.execute(
            "SELECT id, n_number, registrant_name FROM aircraft "
            "WHERE registrant_name IS NOT NULL AND registrant_name != ''"
        ).fetchall()
        for aircraft_id, n_number, registrant_name in aircraft_rows:
            if not registrant_name:
                continue
            reg_upper = registrant_name.upper()
            # Exact name match gets 0.8, partial/contains gets 0.5
            if sdn_upper == reg_upper:
                confidence = 0.8
            elif sdn_upper in reg_upper or reg_upper in sdn_upper:
                confidence = 0.5
            else:
                continue
            try:
                conn.execute(
                    """
                    INSERT INTO ofac_matches (
                        aircraft_id, sdn_id, match_type, match_confidence,
                        matched_value, sdn_value, is_confirmed,
                        source, ingested_at
                    ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                    """,
                    (
                        aircraft_id,
                        sdn_id,
                        "owner_name",
                        confidence,
                        registrant_name,
                        sdn_name,
                        SOURCE,
                        now,
                    ),
                )
                matches_inserted += 1
            except Exception as e:
                errors += 1
                logger.warning("Error inserting name match: %s", e)

    conn.commit()
    return matches_inserted, errors


# ---------------------------------------------------------------------------
# Main ETL entry point
# ---------------------------------------------------------------------------

def run_ofac_etl(db_path: str):
    """Download SDN CSV, ingest entries, cross-reference against aircraft."""
    started_at = now_utc()
    conn = get_db_connection(db_path)
    try:
        entries = _download_sdn_csv()

        inserted, updated, errored = _ingest_sdn_entries(conn, entries)
        logger.info(
            "SDN ingestion: %d processed, %d inserted, %d updated, %d errors",
            len(entries), inserted, updated, errored,
        )

        # Clear previous auto-generated matches before re-running
        conn.execute(
            "DELETE FROM ofac_matches WHERE source = ?", (SOURCE,)
        )
        conn.commit()

        matches_inserted, match_errors = _cross_reference(conn)
        logger.info(
            "OFAC cross-reference: %d matches inserted, %d errors",
            matches_inserted, match_errors,
        )

        log_ingestion(
            conn,
            module="ofac",
            source=SOURCE,
            started_at=started_at,
            records_processed=len(entries),
            records_inserted=inserted + matches_inserted,
            records_updated=updated,
            records_errored=errored + match_errors,
            status="completed",
            source_file="SDN.CSV",
        )

    except Exception as e:
        logger.error("OFAC ETL failed: %s", e)
        log_ingestion(
            conn,
            module="ofac",
            source=SOURCE,
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


# ---------------------------------------------------------------------------
# Sample data generator
# ---------------------------------------------------------------------------

_SAMPLE_SDN_ENTRIES = [
    {
        "sdn_entry_id": 90001,
        "sdn_type": "Entity",
        "primary_name": "ACME GLOBAL AVIATION LLC",
        "program_list": "SDGT",
        "country": "IR",
        "remarks": "Aircraft Tail Number N12345; DOB 1980",
        "aircraft_type": "Fixed Wing Multi-Engine",
    },
    {
        "sdn_entry_id": 90002,
        "sdn_type": "Entity",
        "primary_name": "SKYLINE TRANSPORT SERVICES",
        "program_list": "IRAN",
        "country": "IR",
        "remarks": "Aircraft Tail Number N67890; aka SKYLINE AIR",
        "aircraft_type": "Fixed Wing Single-Engine",
    },
    {
        "sdn_entry_id": 90003,
        "sdn_type": "Individual",
        "primary_name": "PETROV, IVAN",
        "program_list": "RUSSIA-EO14024",
        "country": "RU",
        "remarks": "DOB 15 Mar 1975; Passport 1234567",
        "aircraft_type": None,
    },
    {
        "sdn_entry_id": 90004,
        "sdn_type": "Entity",
        "primary_name": "JADE DRAGON HOLDINGS",
        "program_list": "SDGT",
        "country": "CN",
        "remarks": "Aircraft Type: Gulfstream G550",
        "aircraft_type": "Fixed Wing Multi-Engine",
    },
    {
        "sdn_entry_id": 90005,
        "sdn_type": "Entity",
        "primary_name": "GOLDEN EAGLE AIR CHARTER",
        "program_list": "SDNTK",
        "country": "SY",
        "remarks": "Aircraft Tail Number N99999; alt name GOLDEN EAGLE AVIATION",
        "aircraft_type": "Fixed Wing Multi-Engine",
    },
    {
        "sdn_entry_id": 90006,
        "sdn_type": "Entity",
        "primary_name": "AL-RASHID LOGISTICS",
        "program_list": "IRAQ",
        "country": "IQ",
        "remarks": "Address: Baghdad, Iraq",
        "aircraft_type": None,
    },
    {
        "sdn_entry_id": 90007,
        "sdn_type": "Individual",
        "primary_name": "MORALES, CARLOS EDUARDO",
        "program_list": "SDNTK",
        "country": "VE",
        "remarks": "DOB 22 Jun 1968; Aircraft owner",
        "aircraft_type": None,
    },
    {
        "sdn_entry_id": 90008,
        "sdn_type": "Entity",
        "primary_name": "SHADOW FREIGHT INTERNATIONAL",
        "program_list": "SDGT",
        "country": "LB",
        "remarks": "Alt name SHADOW AIR CARGO",
        "aircraft_type": "Fixed Wing Multi-Engine",
    },
    {
        "sdn_entry_id": 90009,
        "sdn_type": "Entity",
        "primary_name": "RED PHOENIX AIRLINES",
        "program_list": "DPRK",
        "country": "KP",
        "remarks": "Aircraft Tail Number N55555; Operates cargo flights",
        "aircraft_type": "Fixed Wing Multi-Engine",
    },
    {
        "sdn_entry_id": 90010,
        "sdn_type": "Entity",
        "primary_name": "CASPIAN TRADE VENTURES",
        "program_list": "IRAN",
        "country": "IR",
        "remarks": "Aircraft Tail Number N77777; Oil trading front company",
        "aircraft_type": "Fixed Wing Multi-Engine",
    },
]


def generate_sample_ofac_data(db_path: str):
    """Insert ~10 sample SDN entries and create cross-reference matches.

    A few sample entries intentionally reference tail numbers that may
    exist in the aircraft table to demonstrate the matching workflow.
    """
    started_at = now_utc()
    conn = get_db_connection(db_path)
    now = now_utc()
    inserted = errored = 0

    try:
        # Fetch a few real N-numbers from the aircraft table to plant matches
        real_aircraft = []
        try:
            rows = conn.execute(
                "SELECT id, n_number, registrant_name FROM aircraft LIMIT 200"
            ).fetchall()
            real_aircraft = [(r[0], r[1], r[2]) for r in rows]
        except Exception:
            pass

        entries = list(_SAMPLE_SDN_ENTRIES)

        # If we have real aircraft, update some sample entries to reference them
        if real_aircraft:
            # Pick up to 3 real tail numbers to plant into sample SDN remarks
            chosen = random.sample(real_aircraft, min(3, len(real_aircraft)))
            for i, (aid, n_num, reg_name) in enumerate(chosen):
                if i < len(entries):
                    tail_ref = n_num if n_num.startswith("N") else f"N{n_num}"
                    entries[i]["remarks"] = (
                        f"Aircraft Tail Number {tail_ref}; "
                        + (entries[i].get("remarks") or "")
                    )

        # Insert sample SDN entries
        for entry in entries:
            tail_numbers = _TAIL_RE.findall(entry.get("remarks") or "")
            try:
                conn.execute(
                    """
                    INSERT INTO ofac_sdn (
                        sdn_entry_id, sdn_type, primary_name, program_list,
                        country, remarks, aircraft_tail_numbers, aircraft_type,
                        source, source_url, ingested_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(sdn_entry_id) DO UPDATE SET
                        sdn_type = excluded.sdn_type,
                        primary_name = excluded.primary_name,
                        program_list = excluded.program_list,
                        country = excluded.country,
                        remarks = excluded.remarks,
                        aircraft_tail_numbers = excluded.aircraft_tail_numbers,
                        aircraft_type = excluded.aircraft_type,
                        source = excluded.source,
                        source_url = excluded.source_url,
                        ingested_at = excluded.ingested_at
                    """,
                    (
                        entry["sdn_entry_id"],
                        entry["sdn_type"],
                        entry["primary_name"],
                        entry["program_list"],
                        entry.get("country"),
                        entry.get("remarks"),
                        ",".join(tail_numbers) if tail_numbers else None,
                        entry.get("aircraft_type"),
                        "sample_ofac",
                        None,
                        now,
                    ),
                )
                inserted += 1
            except Exception as e:
                errored += 1
                logger.warning(
                    "Error inserting sample SDN %s: %s",
                    entry["sdn_entry_id"], e,
                )
        conn.commit()

        # Clear previous sample matches
        conn.execute("DELETE FROM ofac_matches WHERE source = 'sample_ofac'")
        conn.commit()

        # Cross-reference
        match_count = 0
        sdn_rows = conn.execute(
            "SELECT id, aircraft_tail_numbers, primary_name FROM ofac_sdn "
            "WHERE source = 'sample_ofac'"
        ).fetchall()

        for sdn_id, tail_csv, sdn_name in sdn_rows:
            # Tail number matches
            if tail_csv:
                tails = [t.strip() for t in tail_csv.split(",") if t.strip()]
                for tail in tails:
                    matches = conn.execute(
                        "SELECT id, n_number FROM aircraft WHERE n_number = ?",
                        (tail,),
                    ).fetchall()
                    for aircraft_id, n_number in matches:
                        try:
                            conn.execute(
                                """
                                INSERT INTO ofac_matches (
                                    aircraft_id, sdn_id, match_type,
                                    match_confidence, matched_value, sdn_value,
                                    is_confirmed, source, ingested_at
                                ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                                """,
                                (
                                    aircraft_id, sdn_id, "tail_number",
                                    1.0, n_number, tail,
                                    "sample_ofac", now,
                                ),
                            )
                            match_count += 1
                        except Exception as e:
                            logger.warning("Error inserting sample match: %s", e)

            # Owner name matches (pick a few random aircraft for demo)
            if sdn_name and real_aircraft:
                # For demo, randomly assign 0-1 owner-name matches per SDN
                if random.random() < 0.3:
                    rand_ac = random.choice(real_aircraft)
                    try:
                        conn.execute(
                            """
                            INSERT INTO ofac_matches (
                                aircraft_id, sdn_id, match_type,
                                match_confidence, matched_value, sdn_value,
                                is_confirmed, source, ingested_at
                            ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                            """,
                            (
                                rand_ac[0], sdn_id, "owner_name",
                                round(random.uniform(0.5, 0.8), 2),
                                rand_ac[2] or "Unknown",
                                sdn_name,
                                "sample_ofac", now,
                            ),
                        )
                        match_count += 1
                    except Exception as e:
                        logger.warning("Error inserting sample name match: %s", e)

        conn.commit()

        logger.info(
            "Sample OFAC data: %d SDN entries inserted, %d matches created, %d errors",
            inserted, match_count, errored,
        )

        log_ingestion(
            conn,
            module="ofac",
            source="sample_ofac",
            started_at=started_at,
            records_processed=len(entries),
            records_inserted=inserted + match_count,
            records_updated=0,
            records_errored=errored,
            status="completed",
        )

    except Exception as e:
        logger.error("Sample OFAC data generation failed: %s", e)
        log_ingestion(
            conn,
            module="ofac",
            source="sample_ofac",
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


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    db = sys.argv[1] if len(sys.argv) > 1 else "fleetpulse.db"
    if "--sample" in sys.argv:
        generate_sample_ofac_data(db)
    else:
        run_ofac_etl(db)
