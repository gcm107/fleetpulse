"""FastAPI router for flight tracking endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.etl.opensky import fetch_live_states, get_opensky_token
from backend.config import settings
from backend.models.aircraft import Aircraft
from backend.services.tracking_service import (
    add_to_watchlist,
    get_live_flight_by_hex,
    get_live_flights,
    get_watchlist,
    remove_from_watchlist,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tracking", tags=["tracking"])


class WatchlistRequest(BaseModel):
    n_number: str


def _lookup_live_position(hex_codes: list[str]) -> list[dict]:
    """Query OpenSky for real-time positions of aircraft by hex codes."""
    if not hex_codes:
        return []

    token = None
    if settings.OPENSKY_CLIENT_ID and settings.OPENSKY_CLIENT_SECRET:
        try:
            token = get_opensky_token(settings.OPENSKY_CLIENT_ID, settings.OPENSKY_CLIENT_SECRET)
        except Exception as e:
            logger.warning(f"OpenSky auth failed, using anonymous: {e}")

    try:
        states = fetch_live_states(token=token, hex_codes=hex_codes)
    except Exception as e:
        logger.error(f"OpenSky fetch failed: {e}")
        return []

    results = []
    for sv in states:
        if len(sv) < 17:
            continue
        results.append({
            "transponder_hex": (sv[0] or "").upper(),
            "callsign": (sv[1] or "").strip(),
            "origin_country": sv[2],
            "latitude": sv[6],
            "longitude": sv[5],
            "altitude_ft": round(sv[7] * 3.28084) if sv[7] is not None else None,
            "geo_altitude_ft": round(sv[13] * 3.28084) if sv[13] is not None else None,
            "ground_speed_kts": round(sv[9] * 1.94384) if sv[9] is not None else None,
            "track_deg": sv[10],
            "vertical_rate_fpm": round(sv[11] * 196.85) if sv[11] is not None else None,
            "on_ground": sv[8],
            "squawk": sv[14],
        })
    return results


@router.get("/live")
def read_live_flights(db: Session = Depends(get_db)):
    """Get all currently tracked aircraft with their latest positions."""
    flights = get_live_flights(db)
    return {
        "count": len(flights),
        "flights": flights,
    }


@router.get("/lookup/{n_number}")
def lookup_live_aircraft(n_number: str, db: Session = Depends(get_db)):
    """Real-time lookup: find an aircraft's current position via OpenSky.

    Takes an N-number, looks up the transponder hex code, queries OpenSky,
    and returns the live position if the aircraft is airborne.
    """
    cleaned = n_number.strip().upper()
    if cleaned.startswith("N"):
        cleaned = cleaned[1:]

    aircraft = db.execute(
        select(Aircraft).where(Aircraft.n_number == cleaned)
    ).scalar_one_or_none()

    if not aircraft:
        raise HTTPException(status_code=404, detail=f"Aircraft N{cleaned} not found in registry")

    hex_code = aircraft.transponder_hex
    if not hex_code:
        raise HTTPException(
            status_code=404,
            detail=f"N{cleaned} has no transponder hex code on file"
        )

    positions = _lookup_live_position([hex_code])

    if not positions:
        return {
            "n_number": cleaned,
            "transponder_hex": hex_code,
            "manufacturer": aircraft.manufacturer,
            "model": aircraft.model,
            "status": "not_found",
            "message": f"N{cleaned} ({hex_code}) is not currently broadcasting ADS-B. The aircraft may be on the ground, outside ADS-B coverage, or have its transponder off.",
            "position": None,
        }

    pos = positions[0]
    return {
        "n_number": cleaned,
        "transponder_hex": hex_code,
        "manufacturer": aircraft.manufacturer,
        "model": aircraft.model,
        "status": "airborne" if not pos.get("on_ground") else "on_ground",
        "message": None,
        "position": pos,
    }


@router.get("/live/{hex_code}")
def read_live_flight(hex_code: str, db: Session = Depends(get_db)):
    """Get a single aircraft's live position and recent track by transponder hex code."""
    result = get_live_flight_by_hex(db, hex_code)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No live flight found for hex code: {hex_code}",
        )
    return result


@router.get("/watch")
def read_watchlist(db: Session = Depends(get_db)):
    """Get the list of aircraft currently on the tracking watchlist."""
    watchlist = get_watchlist(db)
    return {
        "count": len(watchlist),
        "aircraft": watchlist,
    }


@router.post("/watch")
def create_watchlist_entry(body: WatchlistRequest, db: Session = Depends(get_db)):
    """Add an aircraft to the tracking watchlist."""
    result = add_to_watchlist(db, body.n_number)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


@router.delete("/watch/{n_number}")
def delete_watchlist_entry(n_number: str, db: Session = Depends(get_db)):
    """Remove an aircraft from the tracking watchlist."""
    result = remove_from_watchlist(db, n_number)
    return result
