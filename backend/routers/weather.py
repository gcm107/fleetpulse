"""FastAPI router for weather-related endpoints."""

from fastapi import APIRouter, HTTPException

from backend.config import settings
from backend.etl.weather import ingest_weather

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/refresh/{station_id}")
def refresh_weather(station_id: str):
    """Trigger a weather data refresh for a specific station.

    Fetches the latest METAR and TAF data from NOAA Aviation Weather Center
    for the given ICAO station identifier and stores it in the database.
    """
    cleaned = station_id.strip().upper()
    if not cleaned or len(cleaned) < 3:
        raise HTTPException(
            status_code=400,
            detail="Invalid station ID. Provide a valid ICAO code (e.g., KJFK).",
        )

    db_url = settings.DATABASE_URL
    db_path = db_url.replace("sqlite:///", "").replace("./", "")

    try:
        result = ingest_weather(db_path, [cleaned])
        return {
            "status": "success",
            "station_id": cleaned,
            "metars_inserted": result["metars_inserted"],
            "tafs_inserted": result["tafs_inserted"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Weather refresh failed for {cleaned}: {str(e)}",
        )
