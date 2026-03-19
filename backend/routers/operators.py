"""FastAPI router for operator-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.operator import (
    EnforcementEntry,
    FleetEntry,
    OperatorDetail,
    OperatorSummary,
)
from backend.schemas.safety import (
    EnforcementActionResponse,
    NTSBAccidentResponse,
    SafetyScoreResponse,
)
from backend.services.operator_service import (
    get_operator_by_cert,
    get_operator_enforcement,
    get_operator_fleet,
    search_operators,
)
from backend.services.safety_scorer import get_operator_safety

router = APIRouter(prefix="/api/operators", tags=["operators"])


@router.get("", response_model=list[OperatorSummary])
def list_operators(
    q: str = Query("", description="Search by name, DBA, or certificate number"),
    state: str | None = Query(None, description="Filter by two-letter state code"),
    db: Session = Depends(get_db),
):
    """Search operators by holder name, DBA name, or certificate number."""
    results = search_operators(db, query=q, state=state)
    return results


@router.get("/{cert_number}", response_model=OperatorDetail)
def read_operator(cert_number: str, db: Session = Depends(get_db)):
    """Look up an operator by certificate number."""
    operator = get_operator_by_cert(db, cert_number)
    if operator is None:
        raise HTTPException(
            status_code=404,
            detail=f"Operator not found for certificate number: {cert_number}",
        )
    return operator


@router.get("/{cert_number}/fleet", response_model=list[FleetEntry])
def read_operator_fleet(cert_number: str, db: Session = Depends(get_db)):
    """Get the fleet of aircraft associated with an operator."""
    operator = get_operator_by_cert(db, cert_number)
    if operator is None:
        raise HTTPException(
            status_code=404,
            detail=f"Operator not found for certificate number: {cert_number}",
        )
    fleet = get_operator_fleet(db, operator.id)
    return fleet


@router.get("/{cert_number}/safety")
def read_operator_safety(cert_number: str, db: Session = Depends(get_db)):
    """Get safety scores, recent accidents, and enforcement summary for an operator."""
    operator = get_operator_by_cert(db, cert_number)
    if operator is None:
        raise HTTPException(
            status_code=404,
            detail=f"Operator not found for certificate number: {cert_number}",
        )
    safety_data = get_operator_safety(db, operator.id)
    score = safety_data["score"]

    return {
        "operator_id": operator.id,
        "certificate_number": operator.certificate_number,
        "holder_name": operator.holder_name,
        "score": SafetyScoreResponse.model_validate(score) if score else None,
        "accidents": [
            NTSBAccidentResponse.model_validate(a) for a in safety_data["accidents"]
        ],
        "enforcement": [
            EnforcementActionResponse.model_validate(e) for e in safety_data["enforcement"]
        ],
    }


@router.get("/{cert_number}/enforcement", response_model=list[EnforcementEntry])
def read_operator_enforcement(cert_number: str, db: Session = Depends(get_db)):
    """Get enforcement actions for an operator."""
    operator = get_operator_by_cert(db, cert_number)
    if operator is None:
        raise HTTPException(
            status_code=404,
            detail=f"Operator not found for certificate number: {cert_number}",
        )
    actions = get_operator_enforcement(db, operator.id)
    return actions
