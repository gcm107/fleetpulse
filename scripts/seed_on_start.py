"""Startup script: initializes DB and seeds data if empty."""
import logging
import sqlite3
import os
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("seed")

# Determine the SQLite file path from DATABASE_URL
_db_url = os.environ.get("DATABASE_URL", "sqlite:///./fleetpulse.db")
# Handle sqlite:////absolute/path and sqlite:///./relative/path
if _db_url.startswith("sqlite:////"):
    DB_FILE = _db_url[len("sqlite:///"):]  # keeps /absolute/path
elif _db_url.startswith("sqlite:///"):
    DB_FILE = _db_url[len("sqlite:///"):]  # keeps ./relative/path
else:
    DB_FILE = "fleetpulse.db"

logger.info(f"Database file: {DB_FILE}")
logger.info(f"DATABASE_URL: {_db_url}")


def table_count(table):
    """Return row count for a table, or 0 if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_FILE)
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def main():
    # Ensure parent directory exists
    parent = os.path.dirname(DB_FILE)
    if parent:
        os.makedirs(parent, exist_ok=True)

    # Step 1: Create all tables
    logger.info("Initializing database tables...")
    from backend.database import engine, Base
    from backend.models import *  # noqa: F401,F403
    Base.metadata.create_all(bind=engine)
    logger.info("Tables ready.")

    # Step 2: Seed airports if empty
    if table_count("airports") == 0:
        logger.info("Seeding airports (84K+ records)...")
        from backend.etl.airports import run_airport_etl
        try:
            run_airport_etl(DB_FILE)
        except Exception as e:
            logger.error(f"Airport seed failed: {e}")
    else:
        logger.info(f"Airports already loaded: {table_count('airports'):,} records")

    # Step 3: Seed aircraft registry if empty
    if table_count("aircraft") == 0:
        logger.info("Seeding FAA aircraft registry (310K+ records, ~3-5 min)...")
        from backend.etl.faa_registry import run_faa_registry_etl
        try:
            run_faa_registry_etl(DB_FILE)
        except Exception as e:
            logger.error(f"Aircraft seed failed: {e}")
    else:
        logger.info(f"Aircraft already loaded: {table_count('aircraft'):,} records")

    # Step 4: Seed sample data if empty
    if table_count("ntsb_accidents") == 0:
        logger.info("Seeding NTSB sample data...")
        try:
            from backend.etl.ntsb import run_ntsb_etl
            run_ntsb_etl(DB_FILE)
        except Exception as e:
            logger.error(f"NTSB seed failed: {e}")

    if table_count("enforcement_actions") == 0:
        logger.info("Seeding enforcement sample data...")
        try:
            from backend.etl.enforcement import run_enforcement_etl
            run_enforcement_etl(DB_FILE)
        except Exception as e:
            logger.error(f"Enforcement seed failed: {e}")

    if table_count("ofac_sdn") == 0:
        logger.info("Seeding OFAC sample data...")
        try:
            from backend.etl.ofac import generate_sample_ofac_data
            generate_sample_ofac_data(DB_FILE)
        except Exception as e:
            logger.error(f"OFAC seed failed: {e}")

    # Step 5: Compute safety scores if empty
    if table_count("safety_scores") == 0:
        logger.info("Computing operator safety scores...")
        try:
            from backend.etl.safety_scores import compute_operator_scores
            compute_operator_scores(DB_FILE)
        except Exception as e:
            logger.error(f"Safety scores failed: {e}")

    logger.info(f"Seed complete. Airports: {table_count('airports'):,}, Aircraft: {table_count('aircraft'):,}")
    logger.info("Starting server...")


if __name__ == "__main__":
    main()
