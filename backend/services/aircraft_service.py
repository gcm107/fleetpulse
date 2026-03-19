"""Service layer for aircraft-related database operations."""

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.models.aircraft import Aircraft, TailHistory
from backend.models.ownership import OwnershipRecord


def get_aircraft_by_n_number(db: Session, n_number: str) -> Optional[Aircraft]:
    """Look up an aircraft by N-number.

    Strips leading 'N' prefix if present and uppercases the input to match
    the FAA registry format (stored without N prefix).
    """
    cleaned = n_number.strip().upper()
    if cleaned.startswith("N"):
        cleaned = cleaned[1:]

    stmt = select(Aircraft).where(Aircraft.n_number == cleaned)
    return db.execute(stmt).scalar_one_or_none()


def get_aircraft_by_hex(db: Session, hex_code: str) -> Optional[Aircraft]:
    """Look up an aircraft by transponder hex (ICAO 24-bit address)."""
    cleaned = hex_code.strip().upper()
    stmt = select(Aircraft).where(Aircraft.transponder_hex == cleaned)
    return db.execute(stmt).scalar_one_or_none()


def search_aircraft(db: Session, query: str, limit: int = 50) -> list[Aircraft]:
    """Search aircraft by N-number, serial number, registrant name, or manufacturer/model.

    Performs a case-insensitive LIKE search. Results are ordered by N-number
    and capped at the specified limit.
    """
    raw = query.strip()
    pattern = f"%{raw}%"

    # Strip N prefix for n_number search (DB stores without N)
    stripped = raw.upper()
    if stripped.startswith("N") and len(stripped) > 1 and any(c.isdigit() for c in stripped[1:]):
        n_pattern = f"%{stripped[1:]}%"
    else:
        n_pattern = pattern

    stmt = (
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
        .limit(limit)
    )
    result = db.execute(stmt).scalars().all()
    return list(result)


def get_aircraft_history(db: Session, n_number: str) -> list[TailHistory]:
    """Get tail history entries for an aircraft by N-number.

    Looks up the aircraft's serial number, then returns all tail_history
    records matching that serial number, ordered by event_date descending.
    """
    cleaned = n_number.strip().upper()
    if cleaned.startswith("N"):
        cleaned = cleaned[1:]

    # First get the aircraft to find its serial number
    aircraft = db.execute(
        select(Aircraft).where(Aircraft.n_number == cleaned)
    ).scalar_one_or_none()

    if aircraft is None or not aircraft.serial_number:
        # Fall back to searching by n_number in tail_history directly
        stmt = (
            select(TailHistory)
            .where(TailHistory.n_number == cleaned)
            .order_by(TailHistory.event_date.desc())
        )
        return list(db.execute(stmt).scalars().all())

    # Find all history entries for this serial number
    stmt = (
        select(TailHistory)
        .where(TailHistory.serial_number == aircraft.serial_number)
        .order_by(TailHistory.event_date.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_aircraft_ownership(db: Session, aircraft_id: int) -> list[OwnershipRecord]:
    """Get ownership records for an aircraft by its database ID.

    Returns all ownership records ordered by effective_date descending,
    with current records first.
    """
    stmt = (
        select(OwnershipRecord)
        .where(OwnershipRecord.aircraft_id == aircraft_id)
        .order_by(
            OwnershipRecord.is_current.desc(),
            OwnershipRecord.effective_date.desc(),
        )
    )
    return list(db.execute(stmt).scalars().all())
