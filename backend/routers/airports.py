"""FastAPI router for airport-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.airport import AirportDetail, RunwayResponse
from backend.services.airport_service import (
    get_airport_by_code,
    get_airport_notams,
    get_airport_runways,
    get_airport_weather,
)

router = APIRouter(prefix="/api/airports", tags=["airports"])


@router.get("/{code}", response_model=AirportDetail)
def read_airport(code: str, db: Session = Depends(get_db)):
    """Look up an airport by ICAO, IATA, or FAA LID code."""
    airport = get_airport_by_code(db, code)
    if airport is None:
        raise HTTPException(
            status_code=404,
            detail=f"Airport not found for code: {code}",
        )
    return airport


@router.get("/{code}/weather")
def read_airport_weather(code: str, db: Session = Depends(get_db)):
    """Get the latest METAR and TAF for an airport.

    Checks the database first. If no weather data exists, fetches live
    from NOAA Aviation Weather Center.
    """
    airport = get_airport_by_code(db, code)
    if airport is None:
        raise HTTPException(
            status_code=404,
            detail=f"Airport not found for code: {code}",
        )

    icao = airport.icao_code
    weather = get_airport_weather(db, icao)

    # If no data in DB, fetch live from NOAA
    if weather["metar"] is None and weather["taf"] is None:
        try:
            from backend.etl.weather import fetch_metar, fetch_taf
            live_metars = fetch_metar([icao])
            live_tafs = fetch_taf([icao])

            metar_data = None
            if live_metars:
                m = live_metars[0]
                metar_data = {
                    "station_id": m.get("icaoId", icao),
                    "raw_text": m.get("rawOb"),
                    "temperature_c": m.get("temp"),
                    "dewpoint_c": m.get("dewp"),
                    "wind_direction_deg": m.get("wdir"),
                    "wind_speed_kts": m.get("wspd"),
                    "wind_gust_kts": m.get("wgst"),
                    "visibility_sm": m.get("visib"),
                    "altimeter_inhg": m.get("altim"),
                    "flight_category": m.get("fltcat"),
                    "observation_time": str(m.get("reportTime", "")),
                }

            taf_data = None
            if live_tafs:
                t = live_tafs[0]
                taf_data = {
                    "station_id": t.get("icaoId", icao),
                    "raw_text": t.get("rawTAF") or t.get("rawOb"),
                    "issue_time": str(t.get("issueTime", "")),
                    "valid_from": str(t.get("validTimeFrom", "")),
                    "valid_to": str(t.get("validTimeTo", "")),
                }

            return {"metar": metar_data, "taf": taf_data}
        except Exception:
            return {"metar": None, "taf": None}

    metar_data = None
    if weather["metar"] is not None:
        m = weather["metar"]
        metar_data = {
            "station_id": m.station_id,
            "observation_time": str(m.observation_time),
            "raw_text": m.raw_text,
            "temperature_c": m.temperature_c,
            "dewpoint_c": m.dewpoint_c,
            "wind_direction_deg": m.wind_direction_deg,
            "wind_speed_kts": m.wind_speed_kts,
            "wind_gust_kts": m.wind_gust_kts,
            "visibility_sm": m.visibility_sm,
            "altimeter_inhg": m.altimeter_inhg,
            "ceiling_ft": m.ceiling_ft,
            "flight_category": m.flight_category,
        }

    taf_data = None
    if weather["taf"] is not None:
        t = weather["taf"]
        taf_data = {
            "station_id": t.station_id,
            "issue_time": str(t.issue_time),
            "valid_from": str(t.valid_from),
            "valid_to": str(t.valid_to),
            "raw_text": t.raw_text,
        }

    return {"metar": metar_data, "taf": taf_data}


@router.get("/{code}/notams")
def read_airport_notams(code: str, db: Session = Depends(get_db)):
    """Get active NOTAMs for an airport."""
    airport = get_airport_by_code(db, code)
    if airport is None:
        raise HTTPException(
            status_code=404,
            detail=f"Airport not found for code: {code}",
        )

    notams = get_airport_notams(db, airport.icao_code)
    return [
        {
            "notam_id": n.notam_id,
            "classification": n.classification,
            "category": n.category,
            "effective_start": str(n.effective_start),
            "effective_end": str(n.effective_end) if n.effective_end else None,
            "text": n.text,
            "is_active": n.is_active,
        }
        for n in notams
    ]


@router.get("/{code}/runways", response_model=list[RunwayResponse])
def read_airport_runways(code: str, db: Session = Depends(get_db)):
    """Get runways for an airport."""
    airport = get_airport_by_code(db, code)
    if airport is None:
        raise HTTPException(
            status_code=404,
            detail=f"Airport not found for code: {code}",
        )

    runways = get_airport_runways(db, airport.id)
    return runways
