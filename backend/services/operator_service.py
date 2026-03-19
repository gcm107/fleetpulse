"""Service layer for operator-related database operations."""

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.models.aircraft import Aircraft
from backend.models.operator import Operator, OperatorFleet
from backend.models.safety import EnforcementAction


def get_operator_by_cert(db: Session, cert_number: str) -> Optional[Operator]:
    """Look up an operator by certificate number.

    Returns the Operator ORM instance or None if no match is found.
    """
    cert = cert_number.strip()
    stmt = select(Operator).where(Operator.certificate_number == cert)
    return db.execute(stmt).scalar_one_or_none()


def search_operators(
    db: Session,
    query: str,
    state: Optional[str] = None,
    limit: int = 50,
) -> list[Operator]:
    """Search operators by holder_name, dba_name, or certificate_number.

    Performs a case-insensitive LIKE search.  Results can optionally be filtered
    by state.
    """
    pattern = f"%{query.strip()}%"

    stmt = select(Operator).where(
        or_(
            Operator.holder_name.ilike(pattern),
            Operator.dba_name.ilike(pattern),
            Operator.certificate_number.ilike(pattern),
        )
    )

    if state is not None:
        stmt = stmt.where(Operator.state == state.upper())

    stmt = stmt.order_by(Operator.holder_name).limit(limit)
    result = db.execute(stmt).scalars().all()
    return list(result)


def get_operator_fleet(db: Session, operator_id: int) -> list[dict]:
    """Get fleet entries for an operator, joined with aircraft details.

    Returns a list of dicts containing fleet entry info plus aircraft
    manufacturer, model, and year from the aircraft table.
    """
    stmt = (
        select(
            OperatorFleet.id,
            OperatorFleet.n_number,
            OperatorFleet.role,
            OperatorFleet.is_active,
            Aircraft.manufacturer.label("aircraft_manufacturer"),
            Aircraft.model.label("aircraft_model"),
            Aircraft.year_mfr.label("aircraft_year"),
        )
        .outerjoin(Aircraft, OperatorFleet.aircraft_id == Aircraft.id)
        .where(OperatorFleet.operator_id == operator_id)
        .order_by(OperatorFleet.n_number)
    )

    rows = db.execute(stmt).all()
    return [
        {
            "id": row.id,
            "n_number": row.n_number,
            "role": row.role,
            "is_active": row.is_active,
            "aircraft_manufacturer": row.aircraft_manufacturer,
            "aircraft_model": row.aircraft_model,
            "aircraft_year": row.aircraft_year,
        }
        for row in rows
    ]


def get_operator_enforcement(
    db: Session, operator_id: int
) -> list[EnforcementAction]:
    """Get enforcement actions for an operator."""
    stmt = (
        select(EnforcementAction)
        .where(EnforcementAction.operator_id == operator_id)
        .order_by(EnforcementAction.action_date.desc())
    )
    result = db.execute(stmt).scalars().all()
    return list(result)
