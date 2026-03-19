"""Base ETL utilities for FleetPulse data ingestion."""
import logging
import sqlite3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def get_db_connection(db_path: str):
    """Get a SQLite connection with WAL and FK enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def safe_int(val, default=None):
    if val is None or val == '': return default
    try: return int(float(val))
    except (ValueError, TypeError): return default

def safe_float(val, default=None):
    if val is None or val == '': return default
    try: return float(val)
    except (ValueError, TypeError): return default

def now_utc():
    return datetime.now(timezone.utc).isoformat()

def log_ingestion(conn, module, source, started_at, records_processed=0,
                  records_inserted=0, records_updated=0, records_errored=0,
                  status='completed', error_message=None, source_file=None):
    conn.execute("""
        INSERT INTO ingestion_log (module, source, started_at, completed_at,
            records_processed, records_inserted, records_updated,
            records_errored, status, error_message, source_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (module, source, started_at, now_utc(),
          records_processed, records_inserted, records_updated,
          records_errored, status, error_message, source_file))
    conn.commit()
