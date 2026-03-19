"""Pydantic response models for safety-related endpoints."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SafetyScoreResponse(BaseModel):
    """Safety score for an operator or aircraft."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str
    entity_id: int
    entity_name: Optional[str] = None
    overall_score: float
    accident_score: Optional[float] = None
    sdr_score: Optional[float] = None
    enforcement_score: Optional[float] = None
    fleet_age_score: Optional[float] = None
    certificate_tenure_score: Optional[float] = None
    ad_compliance_score: Optional[float] = None
    component_details: Optional[str] = None
    calculation_date: Optional[date] = None
    methodology_version: Optional[str] = None


class NTSBAccidentResponse(BaseModel):
    """NTSB accident/incident record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ntsb_number: str
    event_date: date
    event_city: Optional[str] = None
    event_state: Optional[str] = None
    event_type: Optional[str] = None
    n_number: Optional[str] = None
    aircraft_make_model: Optional[str] = None
    operator_name: Optional[str] = None
    far_part: Optional[str] = None
    phase_of_flight: Optional[str] = None
    weather_condition: Optional[str] = None
    highest_injury: Optional[str] = None
    fatal_count: int = 0
    serious_count: int = 0
    minor_count: int = 0
    uninjured_count: int = 0
    aircraft_damage: Optional[str] = None
    probable_cause: Optional[str] = None
    report_status: Optional[str] = None


class EnforcementActionResponse(BaseModel):
    """Enforcement action record."""

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


class SafetyComparisonResponse(BaseModel):
    """Side-by-side comparison of operator safety scores."""

    operators: list[dict]
