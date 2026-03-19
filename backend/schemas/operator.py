"""Pydantic response models for operator-related endpoints."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OperatorSummary(BaseModel):
    """Operator summary used in search results and lists."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    certificate_number: str
    certificate_type: str
    holder_name: str
    dba_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    certificate_status: Optional[str] = None


class FleetEntry(BaseModel):
    """A single fleet entry linking an operator to an aircraft."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    n_number: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = True
    aircraft_manufacturer: Optional[str] = None
    aircraft_model: Optional[str] = None
    aircraft_year: Optional[int] = None


class OperatorDetail(OperatorSummary):
    """Full operator detail including certificate info and authorities."""

    street_address: Optional[str] = None
    zip_code: Optional[str] = None
    country_code: Optional[str] = None
    phone: Optional[str] = None
    certificate_issue_date: Optional[date] = None
    certificate_expiration_date: Optional[date] = None
    dot_fitness_date: Optional[date] = None
    dot_fitness_status: Optional[str] = None
    district_office: Optional[str] = None
    operations_base: Optional[str] = None
    wet_lease_authority: Optional[bool] = False
    dry_lease_authority: Optional[bool] = False
    on_demand_authority: Optional[bool] = False
    scheduled_authority: Optional[bool] = False
    authorized_aircraft_count: Optional[int] = None
    source: str
    ingested_at: datetime
    updated_at: datetime


class EnforcementEntry(BaseModel):
    """An enforcement action record associated with an operator."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: Optional[str] = None
    action_date: Optional[date] = None
    action_type: Optional[str] = None
    respondent_name: Optional[str] = None
    violation_description: Optional[str] = None
    penalty_amount: Optional[float] = None
    disposition: Optional[str] = None
    suspension_days: Optional[int] = None
