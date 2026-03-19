"""Unified search router — search across airports, aircraft, and operators."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.search_service import unified_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(..., min_length=1, description="Search query string"),
    db: Session = Depends(get_db),
):
    """Search across airports, aircraft, and operators.

    Returns grouped results with up to 10 matches per category:
    {
        "airports": [...],
        "aircraft": [...],
        "operators": [...]
    }
    """
    results = unified_search(db, q, limit_per_category=10)

    return {
        "airports": [
            {
                "id": a.id,
                "icao_code": a.icao_code,
                "iata_code": a.iata_code,
                "faa_lid": a.faa_lid,
                "name": a.name,
                "city": a.city,
                "state_province": a.state_province,
                "country_code": a.country_code,
                "airport_type": a.airport_type,
            }
            for a in results["airports"]
        ],
        "aircraft": [
            {
                "id": ac.id,
                "n_number": ac.n_number,
                "serial_number": ac.serial_number,
                "manufacturer": ac.manufacturer,
                "model": ac.model,
                "year_mfr": ac.year_mfr,
                "registrant_name": ac.registrant_name,
                "registration_status": ac.registration_status,
            }
            for ac in results["aircraft"]
        ],
        "operators": [
            {
                "id": op.id,
                "certificate_number": op.certificate_number,
                "certificate_type": op.certificate_type,
                "holder_name": op.holder_name,
                "dba_name": op.dba_name,
                "city": op.city,
                "state": op.state,
                "certificate_status": op.certificate_status,
            }
            for op in results["operators"]
        ],
    }
