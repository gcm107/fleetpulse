"""Startup script: initializes DB and seeds data if empty."""
import logging
import sqlite3
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("seed")

DB_PATH = os.environ.get("DATABASE_URL", "sqlite:////app/data/fleetpulse.db")
DB_PATH = DB_PATH.replace("sqlite:///", "").replace("sqlite:////", "/")

# Fallback for local dev
if not DB_PATH or DB_PATH == "":
    DB_PATH = "fleetpulse.db"


def table_count(table):
    """Return row count for a table, or 0 if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def main():
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
        run_airport_etl(DB_PATH)
    else:
        logger.info(f"Airports already loaded: {table_count('airports'):,} records")

    # Step 3: Seed aircraft registry if empty
    if table_count("aircraft") == 0:
        logger.info("Seeding FAA aircraft registry (310K+ records, ~3-5 min)...")
        from backend.etl.faa_registry import run_faa_registry_etl
        run_faa_registry_etl(DB_PATH)
    else:
        logger.info(f"Aircraft already loaded: {table_count('aircraft'):,} records")

    # Step 4: Seed sample data if empty
    if table_count("ntsb_accidents") == 0:
        logger.info("Seeding NTSB sample data...")
        from backend.etl.ntsb import run_ntsb_etl
        run_ntsb_etl(DB_PATH)

    if table_count("enforcement_actions") == 0:
        logger.info("Seeding enforcement sample data...")
        from backend.etl.enforcement import run_enforcement_etl
        run_enforcement_etl(DB_PATH)

    if table_count("ofac_sdn") == 0:
        logger.info("Seeding OFAC sample data...")
        from backend.etl.ofac import generate_sample_ofac_data
        generate_sample_ofac_data(DB_PATH)

    # Step 5: Compute safety scores if empty
    if table_count("safety_scores") == 0:
        logger.info("Computing operator safety scores...")
        from backend.etl.safety_scores import compute_operator_scores
        compute_operator_scores(DB_PATH)
        # Skip aircraft scores on startup — takes too long (305K records)
        logger.info("Aircraft safety scores will be computed on-demand or via ETL trigger.")

    logger.info("Seed complete. Starting server...")


if __name__ == "__main__":
    main()
