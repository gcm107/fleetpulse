"""FastAPI router for aircraft-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.aircraft import Aircraft
from backend.schemas.aircraft import AircraftDetail, OwnershipEntry, TailHistoryEntry
from backend.schemas.safety import NTSBAccidentResponse, SafetyScoreResponse
from backend.schemas.sanctions import SanctionsCheckResponse
from backend.services.aircraft_service import (
    get_aircraft_by_n_number,
    get_aircraft_history,
    get_aircraft_ownership,
)
from backend.services.safety_scorer import get_aircraft_safety
from backend.services.sanctions_service import check_aircraft_sanctions
from backend.services.tracking_service import get_aircraft_track

router = APIRouter(prefix="/api/aircraft", tags=["aircraft"])


@router.get("/types/manufacturers")
def list_manufacturers(db: Session = Depends(get_db)):
    """Return distinct manufacturers with 10+ aircraft, ordered alphabetically."""
    stmt = (
        select(Aircraft.manufacturer)
        .where(Aircraft.manufacturer.isnot(None))
        .where(Aircraft.manufacturer != "")
        .group_by(Aircraft.manufacturer)
        .having(func.count(Aircraft.id) >= 10)
        .order_by(Aircraft.manufacturer)
    )
    rows = db.execute(stmt).scalars().all()
    return {"manufacturers": list(rows)}


@router.get("/types/models")
def list_models(
    manufacturer: str = Query(..., description="Manufacturer name"),
    db: Session = Depends(get_db),
):
    """Return distinct models for a given manufacturer, ordered alphabetically."""
    stmt = (
        select(Aircraft.model)
        .where(Aircraft.manufacturer == manufacturer)
        .where(Aircraft.model.isnot(None))
        .where(Aircraft.model != "")
        .distinct()
        .order_by(Aircraft.model)
    )
    rows = db.execute(stmt).scalars().all()
    return {"models": list(rows)}


@router.get("/types/search")
def search_by_type(
    manufacturer: str = Query(..., description="Manufacturer name"),
    model: str = Query(None, description="Model name (optional)"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    db: Session = Depends(get_db),
):
    """Search aircraft by manufacturer and optionally model."""
    stmt = select(Aircraft).where(Aircraft.manufacturer == manufacturer)
    if model:
        stmt = stmt.where(Aircraft.model == model)
    stmt = stmt.order_by(Aircraft.n_number).limit(limit)
    results = db.execute(stmt).scalars().all()
    return [
        {
            "n_number": a.n_number,
            "manufacturer": a.manufacturer,
            "model": a.model,
            "year_mfr": a.year_mfr,
            "registrant_name": a.registrant_name,
            "registration_status": a.registration_status,
            "serial_number": a.serial_number,
            "icao_type_designator": a.icao_type_designator,
        }
        for a in results
    ]


@router.get("/{n_number}", response_model=AircraftDetail)
def read_aircraft(n_number: str, db: Session = Depends(get_db)):
    """Look up an aircraft by N-number (with or without 'N' prefix)."""
    aircraft = get_aircraft_by_n_number(db, n_number)
    if aircraft is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aircraft not found for N-number: {n_number}",
        )
    return aircraft


@router.get("/{n_number}/history", response_model=list[TailHistoryEntry])
def read_aircraft_history(n_number: str, db: Session = Depends(get_db)):
    """Get tail/registration history for an aircraft."""
    aircraft = get_aircraft_by_n_number(db, n_number)
    if aircraft is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aircraft not found for N-number: {n_number}",
        )
    history = get_aircraft_history(db, n_number)
    return history


@router.get("/{n_number}/ownership", response_model=list[OwnershipEntry])
def read_aircraft_ownership(n_number: str, db: Session = Depends(get_db)):
    """Get ownership records for an aircraft."""
    aircraft = get_aircraft_by_n_number(db, n_number)
    if aircraft is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aircraft not found for N-number: {n_number}",
        )
    records = get_aircraft_ownership(db, aircraft.id)
    return records


@router.get("/{n_number}/safety")
def read_aircraft_safety(n_number: str, db: Session = Depends(get_db)):
    """Get safety scores and NTSB accidents for an aircraft."""
    aircraft = get_aircraft_by_n_number(db, n_number)
    if aircraft is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aircraft not found for N-number: {n_number}",
        )
    safety_data = get_aircraft_safety(db, aircraft.id)
    score = safety_data["score"]

    return {
        "n_number": aircraft.n_number,
        "safety_score": SafetyScoreResponse.model_validate(score) if score else None,
        "accidents": [
            NTSBAccidentResponse.model_validate(a) for a in safety_data["accidents"]
        ],
    }


@router.get("/{n_number}/sanctions", response_model=SanctionsCheckResponse)
def read_aircraft_sanctions(n_number: str, db: Session = Depends(get_db)):
    """Check OFAC/sanctions matches for an aircraft."""
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


@router.get("/{n_number}/track")
def read_aircraft_track(n_number: str, db: Session = Depends(get_db)):
    """Get recent flight tracking data for an aircraft.

    Returns flights from the last 7 days with position history.
    """
    aircraft = get_aircraft_by_n_number(db, n_number)
    if aircraft is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aircraft not found for N-number: {n_number}",
        )
    return get_aircraft_track(db, n_number)
