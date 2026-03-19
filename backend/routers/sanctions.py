"""FastAPI router for sanctions/OFAC screening endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.sanctions import SanctionsCheckResponse
from backend.services.aircraft_service import get_aircraft_by_n_number
from backend.services.sanctions_service import (
    check_aircraft_sanctions,
    get_all_sanctions_alerts,
)

router = APIRouter(prefix="/api/sanctions", tags=["sanctions"])


@router.get("/alerts", response_model=list[SanctionsCheckResponse])
def list_sanctions_alerts(db: Session = Depends(get_db)):
    """Return all active (unconfirmed) OFAC sanctions alerts.

    Each entry represents an aircraft with one or more unreviewed OFAC
    matches, ordered by match confidence descending.
    """
    return get_all_sanctions_alerts(db)


@router.get("/check/{n_number}", response_model=SanctionsCheckResponse)
def check_aircraft(n_number: str, db: Session = Depends(get_db)):
    """Check a specific aircraft (by N-number) against the OFAC SDN list.

    Returns all current matches with their confidence scores and SDN
    entry details.
    """
    aircraft = get_aircraft_by_n_number(db, n_number)
    if aircraft is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aircraft not found for N-number: {n_number}",
        )

    data = check_aircraft_sanctions(db, aircraft.id)
    return SanctionsCheckResponse(
        n_number=aircraft.n_number,
        has_match=data["has_match"],
        match_count=len(data["matches"]),
        matches=data["matches"],
    )
