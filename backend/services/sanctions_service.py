"""Service layer for OFAC / sanctions screening.

Provides functions to check individual aircraft or operators against
the ``ofac_matches`` table, and to retrieve all unconfirmed alerts.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.aircraft import Aircraft
from backend.models.ofac import OFACMatch, OFACSDN
from backend.models.operator import Operator, OperatorFleet
from backend.schemas.sanctions import (
    SDNEntryResponse,
    SanctionsCheckResponse,
    SanctionsMatchResponse,
)


def _match_to_response(match: OFACMatch) -> SanctionsMatchResponse:
    """Convert an OFACMatch ORM object to a SanctionsMatchResponse."""
    sdn_entry: Optional[SDNEntryResponse] = None
    if match.sdn:
        sdn_entry = SDNEntryResponse.model_validate(match.sdn)

    return SanctionsMatchResponse(
        id=match.id,
        match_type=match.match_type,
        match_confidence=match.match_confidence,
        matched_value=match.matched_value,
        sdn_value=match.sdn_value,
        is_confirmed=match.is_confirmed,
        sdn_entry=sdn_entry,
    )


def check_aircraft_sanctions(db: Session, aircraft_id: int) -> dict:
    """Check sanctions matches for a single aircraft.

    Returns a dict with:
        has_match : bool
        matches   : list[OFACMatch] (with joined SDN details)
    """
    stmt = (
        select(OFACMatch)
        .where(OFACMatch.aircraft_id == aircraft_id)
        .order_by(OFACMatch.match_confidence.desc())
    )
    matches = list(db.execute(stmt).scalars().all())

    # Eagerly load related SDN entries
    match_responses = [_match_to_response(m) for m in matches]

    return {
        "has_match": len(matches) > 0,
        "matches": match_responses,
    }


def check_operator_sanctions(db: Session, operator_id: int) -> list[dict]:
    """Check all fleet aircraft for a given operator against OFAC matches.

    Returns a list of per-aircraft result dicts, one for each aircraft
    in the operator's active fleet that has at least one match.
    """
    # Get all aircraft IDs in the operator's fleet
    fleet_stmt = (
        select(OperatorFleet.aircraft_id)
        .where(OperatorFleet.operator_id == operator_id)
        .where(OperatorFleet.aircraft_id.isnot(None))
    )
    aircraft_ids = [
        row for row in db.execute(fleet_stmt).scalars().all()
    ]

    results = []
    for aircraft_id in aircraft_ids:
        data = check_aircraft_sanctions(db, aircraft_id)
        if data["has_match"]:
            aircraft = db.execute(
                select(Aircraft).where(Aircraft.id == aircraft_id)
            ).scalar_one_or_none()
            results.append({
                "aircraft_id": aircraft_id,
                "n_number": aircraft.n_number if aircraft else None,
                "has_match": True,
                "matches": data["matches"],
            })

    return results


def get_all_sanctions_alerts(db: Session) -> list[SanctionsCheckResponse]:
    """Return all unconfirmed OFAC matches grouped by aircraft.

    Each aircraft with at least one unconfirmed match appears as a
    ``SanctionsCheckResponse``.
    """
    # Fetch all unconfirmed matches
    stmt = (
        select(OFACMatch)
        .where(OFACMatch.is_confirmed.is_(None))
        .order_by(OFACMatch.match_confidence.desc())
    )
    matches = list(db.execute(stmt).scalars().all())

    # Group by aircraft_id
    by_aircraft: dict[int, list[OFACMatch]] = {}
    for m in matches:
        by_aircraft.setdefault(m.aircraft_id, []).append(m)

    results: list[SanctionsCheckResponse] = []
    for aircraft_id, ac_matches in by_aircraft.items():
        aircraft = db.execute(
            select(Aircraft).where(Aircraft.id == aircraft_id)
        ).scalar_one_or_none()
        n_number = aircraft.n_number if aircraft else f"ID:{aircraft_id}"

        match_responses = [_match_to_response(m) for m in ac_matches]
        results.append(
            SanctionsCheckResponse(
                n_number=n_number,
                has_match=True,
                match_count=len(match_responses),
                matches=match_responses,
            )
        )

    return results
