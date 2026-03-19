"""FastAPI router for safety-related endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.safety import SafetyComparisonResponse
from backend.services.safety_scorer import compare_operators

router = APIRouter(prefix="/api/safety", tags=["safety"])


@router.get("/compare", response_model=SafetyComparisonResponse)
def compare_operator_scores(
    operators: str = Query(
        ...,
        description="Comma-separated list of operator IDs to compare (e.g. 1,2,3)",
    ),
    db: Session = Depends(get_db),
):
    """Side-by-side comparison of operator safety scores.

    Pass operator database IDs as a comma-separated string. Returns each
    operator's score breakdown for easy comparison.
    """
    try:
        operator_ids = [int(x.strip()) for x in operators.split(",") if x.strip()]
    except ValueError:
        return SafetyComparisonResponse(operators=[])

    if not operator_ids:
        return SafetyComparisonResponse(operators=[])

    results = compare_operators(db, operator_ids)
    return SafetyComparisonResponse(operators=results)
