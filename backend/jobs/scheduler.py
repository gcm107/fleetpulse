"""APScheduler setup for FleetPulse background jobs."""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from backend.etl.airports import run_airport_etl

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

DEFAULT_DB_PATH = "fleetpulse.db"


def _run_airport_job():
    """Wrapper to run airport ETL as a scheduled job."""
    logger.info("Scheduled job: airport ETL starting")
    try:
        run_airport_etl(DEFAULT_DB_PATH)
    except Exception as e:
        logger.error(f"Scheduled airport ETL failed: {e}")


def _run_weather_job():
    """Stub for weather ETL scheduled job."""
    logger.info("Scheduled job: weather ETL (stub - not yet implemented)")


def start_scheduler() -> BackgroundScheduler:
    """Create and start the background scheduler with all configured jobs."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("Scheduler is already running")
        return _scheduler

    _scheduler = BackgroundScheduler()

    # Airport ETL - run weekly (every Sunday at 03:00 UTC)
    _scheduler.add_job(
        _run_airport_job,
        trigger="cron",
        day_of_week="sun",
        hour=3,
        minute=0,
        id="airport_etl",
        name="Airport ETL (weekly)",
        replace_existing=True,
    )

    # Weather ETL - run every 15 minutes (stub)
    _scheduler.add_job(
        _run_weather_job,
        trigger="interval",
        minutes=15,
        id="weather_etl",
        name="Weather ETL (every 15 min)",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Scheduler started with %d jobs", len(_scheduler.get_jobs()))
    return _scheduler


def stop_scheduler():
    """Shut down the scheduler gracefully."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    _scheduler = None
