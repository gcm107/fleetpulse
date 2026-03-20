"""Startup script: initializes DB and seeds data if empty."""
import logging
import sqlite3
import os
import sys

# Ensure the app root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    import backend.models  # noqa: F401
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

    # Note: NTSB, enforcement, OFAC, operators, and safety scores
    # are NOT seeded with sample data. Only real data from actual
    # public sources (FAA registry, OurAirports) is loaded.
    # The sanctions, safety, and enforcement features will show
    # empty states until real data ETLs are implemented.

    logger.info(f"Seed complete. Airports: {table_count('airports'):,}, Aircraft: {table_count('aircraft'):,}")
    logger.info("Starting server...")


if __name__ == "__main__":
    main()
