from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.database import Base


class NTSBAccident(Base):
    __tablename__ = "ntsb_accidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ntsb_number = Column(String, unique=True)
    event_date = Column(Date, nullable=False)
    event_city = Column(String)
    event_state = Column(String)
    event_country = Column(String)
    event_latitude = Column(Float)
    event_longitude = Column(Float)
    event_type = Column(String)
    n_number = Column(String)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"))
    aircraft_make_model = Column(String)
    operator_name = Column(String)
    operator_id = Column(Integer, ForeignKey("operators.id"))
    far_part = Column(String)
    flight_purpose = Column(String)
    phase_of_flight = Column(String)
    weather_condition = Column(String)
    highest_injury = Column(String)
    fatal_count = Column(Integer, default=0)
    serious_count = Column(Integer, default=0)
    minor_count = Column(Integer, default=0)
    uninjured_count = Column(Integer, default=0)
    aircraft_damage = Column(String)
    probable_cause = Column(Text)
    report_status = Column(String)
    report_url = Column(String)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    aircraft = relationship("Aircraft", back_populates="ntsb_accidents")
    operator = relationship("Operator", back_populates="ntsb_accidents")


class FAASDR(Base):
    __tablename__ = "faa_sdrs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sdr_number = Column(String, unique=True)
    report_date = Column(Date)
    aircraft_make = Column(String)
    aircraft_model = Column(String)
    aircraft_serial = Column(String)
    n_number = Column(String)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"))
    engine_make = Column(String)
    engine_model = Column(String)
    component_name = Column(String)
    ata_code = Column(String)
    defect_description = Column(Text)
    precautionary_action = Column(String)
    total_time_hours = Column(Float)
    total_cycles = Column(Integer)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    aircraft = relationship("Aircraft", back_populates="faa_sdrs")


class AirworthinessDirective(Base):
    __tablename__ = "airworthiness_directives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ad_number = Column(String, unique=True)
    amendment_number = Column(String)
    docket_number = Column(String)
    effective_date = Column(Date)
    subject = Column(String)
    applicability = Column(Text)
    applicable_type_designators = Column(Text)
    compliance_requirement = Column(Text)
    compliance_time = Column(String)
    is_emergency = Column(Boolean, default=False)
    is_superseded = Column(Boolean, default=False)
    superseded_by = Column(String)
    federal_register_url = Column(String)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)


class EnforcementAction(Base):
    __tablename__ = "enforcement_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String, unique=True)
    action_date = Column(Date)
    action_type = Column(String)
    respondent_name = Column(String)
    operator_id = Column(Integer, ForeignKey("operators.id"))
    certificate_type = Column(String)
    certificate_number = Column(String)
    violation_description = Column(Text)
    far_sections_violated = Column(Text)
    penalty_amount = Column(Float)
    disposition = Column(String)
    suspension_days = Column(Integer)
    effective_date = Column(Date)
    expiration_date = Column(Date)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    operator = relationship("Operator", back_populates="enforcement_actions")


class SafetyScore(Base):
    __tablename__ = "safety_scores"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="uq_safety_scores_entity"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    entity_name = Column(String)
    overall_score = Column(Float, nullable=False)
    accident_score = Column(Float)
    sdr_score = Column(Float)
    enforcement_score = Column(Float)
    fleet_age_score = Column(Float)
    certificate_tenure_score = Column(Float)
    ad_compliance_score = Column(Float)
    component_details = Column(Text)
    calculation_date = Column(Date, nullable=False)
    methodology_version = Column(String)
    source = Column(String, nullable=False, default="derived")
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
