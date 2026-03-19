"""Service layer for safety scoring and related data retrieval.

Provides functions to look up precomputed safety scores, fetch related
accident and enforcement data, and perform operator comparisons.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.aircraft import Aircraft
from backend.models.operator import Operator
from backend.models.safety import EnforcementAction, NTSBAccident, SafetyScore


def get_safety_score(
    db: Session, entity_type: str, entity_id: int
) -> Optional[SafetyScore]:
    """Retrieve the most recent safety score for a given entity.

    Parameters
    ----------
    db : Session
        SQLAlchemy database session.
    entity_type : str
        Either ``'operator'`` or ``'aircraft'``.
    entity_id : int
        The database ID of the operator or aircraft.

    Returns
    -------
    SafetyScore or None
    """
    stmt = (
        select(SafetyScore)
        .where(SafetyScore.entity_type == entity_type)
        .where(SafetyScore.entity_id == entity_id)
        .order_by(SafetyScore.calculation_date.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_operator_safety(db: Session, operator_id: int) -> dict:
    """Get comprehensive safety data for an operator.

    Returns a dict containing the operator's safety score, recent NTSB
    accidents, and recent enforcement actions.
    """
    score = get_safety_score(db, "operator", operator_id)

    # Recent accidents (last 20)
    accidents_stmt = (
        select(NTSBAccident)
        .where(NTSBAccident.operator_id == operator_id)
        .order_by(NTSBAccident.event_date.desc())
        .limit(20)
    )
    accidents = list(db.execute(accidents_stmt).scalars().all())

    # Recent enforcement actions (last 20)
    enforcement_stmt = (
        select(EnforcementAction)
        .where(EnforcementAction.operator_id == operator_id)
        .order_by(EnforcementAction.action_date.desc())
        .limit(20)
    )
    enforcement = list(db.execute(enforcement_stmt).scalars().all())

    # Get operator info
    operator = db.execute(
        select(Operator).where(Operator.id == operator_id)
    ).scalar_one_or_none()

    return {
        "operator_id": operator_id,
        "certificate_number": operator.certificate_number if operator else None,
        "holder_name": operator.holder_name if operator else None,
        "score": score,
        "accidents": accidents,
        "enforcement": enforcement,
    }


def get_aircraft_safety(db: Session, aircraft_id: int) -> dict:
    """Get comprehensive safety data for an aircraft.

    Returns a dict containing the aircraft's safety score and any NTSB
    accidents associated with this airframe (by aircraft_id or N-number).
    """
    score = get_safety_score(db, "aircraft", aircraft_id)

    # Get the aircraft to find n_number
    aircraft = db.execute(
        select(Aircraft).where(Aircraft.id == aircraft_id)
    ).scalar_one_or_none()

    n_number = aircraft.n_number if aircraft else None

    # Accidents for this aircraft (by ID or N-number)
    if n_number:
        accidents_stmt = (
            select(NTSBAccident)
            .where(
                (NTSBAccident.aircraft_id == aircraft_id)
                | (NTSBAccident.n_number == n_number)
            )
            .order_by(NTSBAccident.event_date.desc())
            .limit(20)
        )
    else:
        accidents_stmt = (
            select(NTSBAccident)
            .where(NTSBAccident.aircraft_id == aircraft_id)
            .order_by(NTSBAccident.event_date.desc())
            .limit(20)
        )
    accidents = list(db.execute(accidents_stmt).scalars().all())

    return {
        "aircraft_id": aircraft_id,
        "n_number": n_number,
        "score": score,
        "accidents": accidents,
    }


def compare_operators(db: Session, operator_ids: list[int]) -> list[dict]:
    """Compare safety scores for multiple operators side by side.

    Returns a list of dicts, each containing the operator's name and
    full score breakdown.
    """
    results = []

    for op_id in operator_ids:
        operator = db.execute(
            select(Operator).where(Operator.id == op_id)
        ).scalar_one_or_none()

        score = get_safety_score(db, "operator", op_id)

        entry = {
            "operator_id": op_id,
            "holder_name": operator.holder_name if operator else None,
            "certificate_number": operator.certificate_number if operator else None,
            "certificate_status": operator.certificate_status if operator else None,
        }

        if score:
            entry.update({
                "overall_score": score.overall_score,
                "accident_score": score.accident_score,
                "sdr_score": score.sdr_score,
                "enforcement_score": score.enforcement_score,
                "fleet_age_score": score.fleet_age_score,
                "certificate_tenure_score": score.certificate_tenure_score,
                "ad_compliance_score": score.ad_compliance_score,
                "calculation_date": str(score.calculation_date) if score.calculation_date else None,
                "methodology_version": score.methodology_version,
                "component_details": score.component_details,
            })
        else:
            entry.update({
                "overall_score": None,
                "accident_score": None,
                "sdr_score": None,
                "enforcement_score": None,
                "fleet_age_score": None,
                "certificate_tenure_score": None,
                "ad_compliance_score": None,
                "calculation_date": None,
                "methodology_version": None,
                "component_details": None,
            })

        results.append(entry)

    return results
