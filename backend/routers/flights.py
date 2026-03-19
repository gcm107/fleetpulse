"""FastAPI router for flight tracking endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.tracking_service import (
    add_to_watchlist,
    get_live_flight_by_hex,
    get_live_flights,
    get_watchlist,
    remove_from_watchlist,
)

router = APIRouter(prefix="/api/tracking", tags=["tracking"])


class WatchlistRequest(BaseModel):
    n_number: str


@router.get("/live")
def read_live_flights(db: Session = Depends(get_db)):
    """Get all currently tracked aircraft with their latest positions."""
    flights = get_live_flights(db)
    return {
        "count": len(flights),
        "flights": flights,
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
