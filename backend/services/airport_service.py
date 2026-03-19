"""Service layer for airport-related database operations."""

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from backend.models.airport import Airport, AirportFrequency, Runway
from backend.models.weather import WeatherMETAR, WeatherTAF
from backend.models.notam import NOTAM


def get_airport_by_code(db: Session, code: str) -> Optional[Airport]:
    """Look up an airport by ICAO code, IATA code, or FAA LID.

    Returns the Airport ORM instance with eager-loaded runways and frequencies,
    or None if no match is found.  The lookup checks ICAO first (most specific),
    then IATA, then FAA LID.
    """
    code_upper = code.strip().upper()

    stmt = (
        select(Airport)
        .options(
            joinedload(Airport.runways),
            joinedload(Airport.frequencies),
        )
        .where(Airport.icao_code == code_upper)
    )
    airport = db.execute(stmt).unique().scalar_one_or_none()
    if airport is not None:
        return airport

    stmt = (
        select(Airport)
        .options(
            joinedload(Airport.runways),
            joinedload(Airport.frequencies),
        )
        .where(Airport.iata_code == code_upper)
    )
    airport = db.execute(stmt).unique().scalar_one_or_none()
    if airport is not None:
        return airport

    stmt = (
        select(Airport)
        .options(
            joinedload(Airport.runways),
            joinedload(Airport.frequencies),
        )
        .where(Airport.faa_lid == code_upper)
    )
    airport = db.execute(stmt).unique().scalar_one_or_none()
    return airport


def search_airports(
    db: Session,
    query: str,
    country: Optional[str] = None,
    airport_type: Optional[str] = None,
    limit: int = 50,
) -> list[Airport]:
    """Search airports by name, city, or code.

    Performs a case-insensitive LIKE search against name, city, icao_code,
    iata_code, and faa_lid.  Results can optionally be filtered by country
    code and/or airport type.
    """
    pattern = f"%{query.strip()}%"

    stmt = select(Airport).where(
        or_(
            Airport.name.ilike(pattern),
            Airport.city.ilike(pattern),
            Airport.icao_code.ilike(pattern),
            Airport.iata_code.ilike(pattern),
            Airport.faa_lid.ilike(pattern),
        )
    )

    if country is not None:
        stmt = stmt.where(Airport.country_code == country.upper())
    if airport_type is not None:
        stmt = stmt.where(Airport.airport_type == airport_type)

    stmt = stmt.order_by(Airport.name).limit(limit)
    result = db.execute(stmt).scalars().all()
    return list(result)


def get_airport_runways(db: Session, airport_id: int) -> list[Runway]:
    """Get all runways for a given airport ID."""
    stmt = select(Runway).where(Runway.airport_id == airport_id)
    result = db.execute(stmt).scalars().all()
    return list(result)


def get_airport_weather(db: Session, airport_icao: str) -> dict:
    """Get the latest METAR and TAF for an airport by ICAO code.

    Returns a dict with keys 'metar' and 'taf', each containing the latest
    record or None if unavailable.
    """
    icao = airport_icao.strip().upper()

    metar_stmt = (
        select(WeatherMETAR)
        .where(WeatherMETAR.station_id == icao)
        .order_by(WeatherMETAR.observation_time.desc())
        .limit(1)
    )
    latest_metar = db.execute(metar_stmt).scalar_one_or_none()

    taf_stmt = (
        select(WeatherTAF)
        .where(WeatherTAF.station_id == icao)
        .order_by(WeatherTAF.issue_time.desc())
        .limit(1)
    )
    latest_taf = db.execute(taf_stmt).scalar_one_or_none()

    return {
        "metar": latest_metar,
        "taf": latest_taf,
    }


def get_airport_notams(db: Session, airport_icao: str) -> list[NOTAM]:
    """Get all active NOTAMs for an airport by ICAO code."""
    icao = airport_icao.strip().upper()

    stmt = (
        select(NOTAM)
        .where(NOTAM.airport_icao == icao, NOTAM.is_active == True)  # noqa: E712
        .order_by(NOTAM.effective_start.desc())
    )
    result = db.execute(stmt).scalars().all()
    return list(result)
