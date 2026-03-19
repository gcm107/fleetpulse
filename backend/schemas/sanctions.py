"""Pydantic response models for sanctions/OFAC-related endpoints."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class SDNEntryResponse(BaseModel):
    """OFAC SDN list entry."""

    model_config = ConfigDict(from_attributes=True)

    sdn_entry_id: Optional[int] = None
    sdn_type: Optional[str] = None
    primary_name: Optional[str] = None
    program_list: Optional[str] = None
    country: Optional[str] = None
    remarks: Optional[str] = None
    aircraft_tail_numbers: Optional[str] = None


class SanctionsMatchResponse(BaseModel):
    """A single OFAC match record with optional joined SDN details."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    match_type: Optional[str] = None
    match_confidence: Optional[float] = None
    matched_value: Optional[str] = None
    sdn_value: Optional[str] = None
    is_confirmed: Optional[bool] = None
    sdn_entry: Optional[SDNEntryResponse] = None


class SanctionsCheckResponse(BaseModel):
    """Result of a sanctions check for a single aircraft."""

    n_number: str
    has_match: bool
    match_count: int
    matches: list[SanctionsMatchResponse]
