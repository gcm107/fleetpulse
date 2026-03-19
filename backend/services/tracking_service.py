"""Service layer for flight tracking and live position operations."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from backend.models.aircraft import Aircraft
from backend.models.flight import Flight, FlightPosition


def get_live_flights(db: Session) -> list[dict]:
    """Get all flights currently marked as live, joined with aircraft info.

    Returns a list of dicts containing flight and aircraft details along with
    the latest position for each live flight.
    """
    stmt = (
        select(Flight)
        .options(joinedload(Flight.aircraft))
        .where(Flight.is_live == True)  # noqa: E712
        .order_by(Flight.last_seen.desc())
    )
    flights = db.execute(stmt).unique().scalars().all()

    results = []
    for flight in flights:
        # Get the latest position for this flight
        pos_stmt = (
            select(FlightPosition)
            .where(FlightPosition.flight_id == flight.id)
            .order_by(FlightPosition.timestamp.desc())
            .limit(1)
        )
        latest_pos = db.execute(pos_stmt).scalar_one_or_none()

        aircraft = flight.aircraft
        result = {
            "flight_id": flight.id,
            "transponder_hex": flight.transponder_hex,
            "callsign": flight.callsign,
            "origin_icao": flight.origin_icao,
            "destination_icao": flight.destination_icao,
            "first_seen": str(flight.first_seen) if flight.first_seen else None,
            "last_seen": str(flight.last_seen) if flight.last_seen else None,
            "flight_date": str(flight.flight_date) if flight.flight_date else None,
            "squawk": flight.squawk,
            "aircraft": None,
            "latest_position": None,
        }

        if aircraft:
            result["aircraft"] = {
                "id": aircraft.id,
                "n_number": aircraft.n_number,
                "manufacturer": aircraft.manufacturer,
                "model": aircraft.model,
                "series": aircraft.series,
                "aircraft_type": aircraft.aircraft_type,
                "registrant_name": aircraft.registrant_name,
                "year_mfr": aircraft.year_mfr,
            }

        if latest_pos:
            result["latest_position"] = {
                "timestamp": str(latest_pos.timestamp),
                "latitude": latest_pos.latitude,
                "longitude": latest_pos.longitude,
                "altitude_ft": latest_pos.altitude_ft,
                "geo_altitude_ft": latest_pos.geo_altitude_ft,
                "ground_speed_kts": latest_pos.ground_speed_kts,
                "track_deg": latest_pos.track_deg,
                "vertical_rate_fpm": latest_pos.vertical_rate_fpm,
                "on_ground": latest_pos.on_ground,
                "squawk": latest_pos.squawk,
            }

        results.append(result)

    return results


def get_live_flight_by_hex(db: Session, hex_code: str) -> Optional[dict]:
    """Get a single live flight by transponder hex code.

    Args:
        db: Database session.
        hex_code: ICAO 24-bit hex identifier (e.g. 'A1B2C3').

    Returns:
        Dict with flight, aircraft, and position data, or None if not found.
    """
    cleaned = hex_code.strip().upper()

    stmt = (
        select(Flight)
        .options(joinedload(Flight.aircraft))
        .where(
            and_(
                Flight.transponder_hex == cleaned,
                Flight.is_live == True,  # noqa: E712
            )
        )
        .order_by(Flight.last_seen.desc())
        .limit(1)
    )
    flight = db.execute(stmt).unique().scalar_one_or_none()

    if flight is None:
        return None

    # Get all recent positions for this flight
    pos_stmt = (
        select(FlightPosition)
        .where(FlightPosition.flight_id == flight.id)
        .order_by(FlightPosition.timestamp.desc())
        .limit(500)
    )
    positions = db.execute(pos_stmt).scalars().all()

    aircraft = flight.aircraft
    result = {
        "flight_id": flight.id,
        "transponder_hex": flight.transponder_hex,
        "callsign": flight.callsign,
        "origin_icao": flight.origin_icao,
        "destination_icao": flight.destination_icao,
        "first_seen": str(flight.first_seen) if flight.first_seen else None,
        "last_seen": str(flight.last_seen) if flight.last_seen else None,
        "flight_date": str(flight.flight_date) if flight.flight_date else None,
        "squawk": flight.squawk,
        "aircraft": None,
        "positions": [],
    }

    if aircraft:
        result["aircraft"] = {
            "id": aircraft.id,
            "n_number": aircraft.n_number,
            "manufacturer": aircraft.manufacturer,
            "model": aircraft.model,
            "series": aircraft.series,
            "aircraft_type": aircraft.aircraft_type,
            "registrant_name": aircraft.registrant_name,
            "year_mfr": aircraft.year_mfr,
        }

    result["positions"] = [
        {
            "timestamp": str(p.timestamp),
            "latitude": p.latitude,
            "longitude": p.longitude,
            "altitude_ft": p.altitude_ft,
            "geo_altitude_ft": p.geo_altitude_ft,
            "ground_speed_kts": p.ground_speed_kts,
            "track_deg": p.track_deg,
            "vertical_rate_fpm": p.vertical_rate_fpm,
            "on_ground": p.on_ground,
            "squawk": p.squawk,
        }
        for p in positions
    ]

    return result


def get_aircraft_track(db: Session, n_number: str) -> dict:
    """Get recent flight positions for an aircraft identified by N-number.

    Returns flight records with their positions from the last 7 days.

    Args:
        db: Database session.
        n_number: FAA N-number (with or without 'N' prefix).

    Returns:
        Dict with n_number, flights list, last_seen, and total_flights count.
    """
    cleaned = n_number.strip().upper()
    if cleaned.startswith("N"):
        cleaned = cleaned[1:]

    # Find the aircraft
    stmt = select(Aircraft).where(Aircraft.n_number == cleaned)
    aircraft = db.execute(stmt).scalar_one_or_none()

    if aircraft is None:
        return {
            "n_number": cleaned,
            "flights": [],
            "last_seen": None,
            "total_flights": 0,
        }

    # Get recent flights (last 7 days)
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    flight_stmt = (
        select(Flight)
        .where(
            and_(
                Flight.aircraft_id == aircraft.id,
                Flight.first_seen >= cutoff,
            )
        )
        .order_by(Flight.first_seen.desc())
        .limit(50)
    )
    flights = db.execute(flight_stmt).scalars().all()

    # Get total flight count for this aircraft
    from sqlalchemy import func

    total_count = db.execute(
        select(func.count(Flight.id)).where(Flight.aircraft_id == aircraft.id)
    ).scalar() or 0

    flight_results = []
    last_seen = None

    for flight in flights:
        # Get positions for each flight
        pos_stmt = (
            select(FlightPosition)
            .where(FlightPosition.flight_id == flight.id)
            .order_by(FlightPosition.timestamp.asc())
        )
        positions = db.execute(pos_stmt).scalars().all()

        if flight.last_seen and (last_seen is None or str(flight.last_seen) > last_seen):
            last_seen = str(flight.last_seen)

        flight_results.append({
            "flight_id": flight.id,
            "transponder_hex": flight.transponder_hex,
            "callsign": flight.callsign,
            "origin_icao": flight.origin_icao,
            "destination_icao": flight.destination_icao,
            "first_seen": str(flight.first_seen) if flight.first_seen else None,
            "last_seen": str(flight.last_seen) if flight.last_seen else None,
            "flight_date": str(flight.flight_date) if flight.flight_date else None,
            "estimated_duration_min": flight.estimated_duration_min,
            "squawk": flight.squawk,
            "is_live": flight.is_live,
            "positions": [
                {
                    "timestamp": str(p.timestamp),
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "altitude_ft": p.altitude_ft,
                    "ground_speed_kts": p.ground_speed_kts,
                    "track_deg": p.track_deg,
                    "vertical_rate_fpm": p.vertical_rate_fpm,
                    "on_ground": p.on_ground,
                }
                for p in positions
            ],
        })

    return {
        "n_number": cleaned,
        "flights": flight_results,
        "last_seen": last_seen,
        "total_flights": total_count,
    }


def get_watchlist(db: Session) -> list[dict]:
    """Get the list of aircraft currently being tracked.

    Uses a simple heuristic: aircraft that have at least one flight marked
    as is_live, or have had a flight in the last 24 hours.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    stmt = (
        select(Aircraft)
        .join(Flight, Flight.aircraft_id == Aircraft.id)
        .where(
            (Flight.is_live == True) | (Flight.last_seen >= cutoff)  # noqa: E712
        )
        .distinct()
        .order_by(Aircraft.n_number)
    )
    aircraft_list = db.execute(stmt).scalars().all()

    results = []
    for ac in aircraft_list:
        # Get latest flight info
        flight_stmt = (
            select(Flight)
            .where(Flight.aircraft_id == ac.id)
            .order_by(Flight.last_seen.desc())
            .limit(1)
        )
        latest_flight = db.execute(flight_stmt).scalar_one_or_none()

        results.append({
            "n_number": ac.n_number,
            "transponder_hex": ac.transponder_hex,
            "manufacturer": ac.manufacturer,
            "model": ac.model,
            "registrant_name": ac.registrant_name,
            "is_live": latest_flight.is_live if latest_flight else False,
            "last_seen": str(latest_flight.last_seen) if latest_flight and latest_flight.last_seen else None,
            "callsign": latest_flight.callsign if latest_flight else None,
        })

    return results


def add_to_watchlist(db: Session, n_number: str) -> dict:
    """Add an aircraft to the tracking watchlist (placeholder).

    Currently returns success without persisting watchlist state, as the
    watchlist is derived from recent flight activity. Future versions may
    store explicit watchlist entries.

    Args:
        db: Database session.
        n_number: FAA N-number to add.

    Returns:
        Dict with status and the cleaned N-number.
    """
    cleaned = n_number.strip().upper()
    if cleaned.startswith("N"):
        cleaned = cleaned[1:]

    # Verify the aircraft exists
    stmt = select(Aircraft).where(Aircraft.n_number == cleaned)
    aircraft = db.execute(stmt).scalar_one_or_none()

    if aircraft is None:
        return {
            "status": "error",
            "message": f"Aircraft not found: {n_number}",
            "n_number": cleaned,
        }

    return {
        "status": "success",
        "message": f"Aircraft N{cleaned} added to watchlist",
        "n_number": cleaned,
        "transponder_hex": aircraft.transponder_hex,
    }


def remove_from_watchlist(db: Session, n_number: str) -> dict:
    """Remove an aircraft from the tracking watchlist (placeholder).

    Currently returns success without modifying state. Future versions may
    store explicit watchlist entries.

    Args:
        db: Database session.
        n_number: FAA N-number to remove.

    Returns:
        Dict with status and the cleaned N-number.
    """
    cleaned = n_number.strip().upper()
    if cleaned.startswith("N"):
        cleaned = cleaned[1:]

    return {
        "status": "success",
        "message": f"Aircraft N{cleaned} removed from watchlist",
        "n_number": cleaned,
    }
