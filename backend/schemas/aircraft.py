"""Pydantic response models for aircraft-related endpoints."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AircraftSummary(BaseModel):
    """Aircraft summary fields used in search results and lists."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    n_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    series: Optional[str] = None
    aircraft_type: Optional[str] = None
    year_mfr: Optional[int] = None
    registration_status: Optional[str] = None
    registrant_name: Optional[str] = None


class AircraftDetail(AircraftSummary):
    """Full aircraft detail with all registration and airworthiness fields."""

    serial_number: Optional[str] = None
    mfr_mdl_code: Optional[str] = None
    engine_type: Optional[str] = None
    engine_model: Optional[str] = None
    engine_count: Optional[int] = None
    number_of_seats: Optional[int] = None
    icao_type_designator: Optional[str] = None
    transponder_hex: Optional[str] = None
    cert_issue_date: Optional[date] = None
    airworthiness_class: Optional[str] = None
    airworthiness_date: Optional[date] = None
    category: Optional[str] = None
    mtow_lbs: Optional[int] = None
    type_certificate: Optional[str] = None
    country_code: Optional[str] = None
    registrant_type: Optional[str] = None
    registrant_street: Optional[str] = None
    registrant_city: Optional[str] = None
    registrant_state: Optional[str] = None
    registrant_zip: Optional[str] = None
    registrant_country: Optional[str] = None
    last_action_date: Optional[date] = None
    fractional_owner: Optional[str] = None
    source: Optional[str] = None
    ingested_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TailHistoryEntry(BaseModel):
    """A single tail history event (registration change, deregistration, etc.)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    serial_number: Optional[str] = None
    n_number: Optional[str] = None
    previous_n_number: Optional[str] = None
    event_type: Optional[str] = None
    event_date: Optional[date] = None
    reason: Optional[str] = None
    registrant_name: Optional[str] = None
    export_country: Optional[str] = None


class OwnershipEntry(BaseModel):
    """An ownership record for an aircraft."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    n_number: Optional[str] = None
    owner_type: Optional[str] = None
    owner_name: Optional[str] = None
    owner_city: Optional[str] = None
    owner_state: Optional[str] = None
    trustee_name: Optional[str] = None
    fractional_program: Optional[str] = None
    effective_date: Optional[date] = None
    is_current: Optional[bool] = None
