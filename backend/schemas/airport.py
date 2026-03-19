"""Pydantic response models for airport-related endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AirportBase(BaseModel):
    """Base airport fields shared across all airport response models."""

    model_config = ConfigDict(from_attributes=True)

    icao_code: str
    iata_code: Optional[str] = None
    faa_lid: Optional[str] = None
    name: str
    airport_type: str
    city: Optional[str] = None
    state_province: Optional[str] = None
    country_code: str
    latitude: float
    longitude: float
    elevation_ft: Optional[int] = None


class AirportSummary(AirportBase):
    """Airport summary with database ID, used in search results and lists."""

    id: int


class RunwayResponse(BaseModel):
    """Runway information for an airport."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    runway_id_le: Optional[str] = None
    runway_id_he: Optional[str] = None
    length_ft: Optional[int] = None
    width_ft: Optional[int] = None
    surface_type: Optional[str] = None
    is_lighted: Optional[bool] = False
    is_closed: Optional[bool] = False
    le_ils_type: Optional[str] = None
    he_ils_type: Optional[str] = None


class FrequencyResponse(BaseModel):
    """Airport frequency information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    frequency_type: str
    frequency_mhz: float
    description: Optional[str] = None


class AirportDetail(AirportSummary):
    """Full airport detail including metadata, runways, and frequencies."""

    continent: Optional[str] = None
    timezone_iana: Optional[str] = None
    utc_offset: Optional[float] = None
    magnetic_variation: Optional[float] = None
    is_customs_aoe: Optional[bool] = False
    is_slot_controlled: Optional[bool] = False
    has_tower: Optional[bool] = False
    fuel_types: Optional[str] = None
    lighting: Optional[str] = None
    operating_hours: Optional[str] = None
    noise_restrictions: Optional[str] = None
    website_url: Optional[str] = None
    source: str
    ingested_at: datetime
    updated_at: datetime
    runways: list[RunwayResponse] = []
    frequencies: list[FrequencyResponse] = []
