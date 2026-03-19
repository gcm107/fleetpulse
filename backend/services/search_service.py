"""Unified search service across airports, aircraft, and operators."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.models.aircraft import Aircraft
from backend.models.airport import Airport
from backend.models.operator import Operator


def unified_search(
    db: Session,
    query: str,
    limit_per_category: int = 10,
) -> dict:
    """Search across airports, aircraft, and operators.

    Returns a dict with keys 'airports', 'aircraft', and 'operators', each
    containing a list of matching ORM instances (capped at limit_per_category).
    """
    raw_query = query.strip()
    pattern = f"%{raw_query}%"

    # Strip N prefix for aircraft n_number searches
    stripped = raw_query.upper()
    if stripped.startswith("N") and len(stripped) > 1 and any(c.isdigit() for c in stripped[1:]):
        n_pattern = f"%{stripped[1:]}%"
    else:
        n_pattern = pattern

    # --- Airports: match on icao_code, iata_code, faa_lid, name, city ---
    airport_stmt = (
        select(Airport)
        .where(
            or_(
                Airport.icao_code.ilike(pattern),
                Airport.iata_code.ilike(pattern),
                Airport.faa_lid.ilike(pattern),
                Airport.name.ilike(pattern),
                Airport.city.ilike(pattern),
            )
        )
        .order_by(Airport.name)
        .limit(limit_per_category)
    )
    airports = list(db.execute(airport_stmt).scalars().all())

    # --- Aircraft: match on n_number, serial_number, registrant_name,
    #     or concatenated manufacturer + model ---
    aircraft_stmt = (
        select(Aircraft)
        .where(
            or_(
                Aircraft.n_number.ilike(n_pattern),
                Aircraft.serial_number.ilike(pattern),
                Aircraft.registrant_name.ilike(pattern),
                Aircraft.manufacturer.ilike(pattern),
                Aircraft.model.ilike(pattern),
            )
        )
        .order_by(Aircraft.n_number)
        .limit(limit_per_category)
    )
    aircraft_list = list(db.execute(aircraft_stmt).scalars().all())

    # --- Operators: match on holder_name, dba_name, certificate_number ---
    operator_stmt = (
        select(Operator)
        .where(
            or_(
                Operator.holder_name.ilike(pattern),
                Operator.dba_name.ilike(pattern),
                Operator.certificate_number.ilike(pattern),
            )
        )
        .order_by(Operator.holder_name)
        .limit(limit_per_category)
    )
    operators = list(db.execute(operator_stmt).scalars().all())

    return {
        "airports": airports,
        "aircraft": aircraft_list,
        "operators": operators,
    }
