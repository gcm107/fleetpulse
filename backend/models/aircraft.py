from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from backend.database import Base


class Aircraft(Base):
    __tablename__ = "aircraft"

    id = Column(Integer, primary_key=True, autoincrement=True)
    n_number = Column(String, unique=True)
    serial_number = Column(String)
    mfr_mdl_code = Column(String)
    manufacturer = Column(String)
    model = Column(String)
    series = Column(String)
    aircraft_type = Column(String)
    engine_type = Column(String)
    engine_model = Column(String)
    engine_count = Column(Integer)
    number_of_seats = Column(Integer)
    year_mfr = Column(Integer)
    icao_type_designator = Column(String)
    transponder_hex = Column(String, unique=True)
    cert_issue_date = Column(Date)
    airworthiness_class = Column(String)
    airworthiness_date = Column(Date)
    category = Column(String)
    mtow_lbs = Column(Integer)
    type_certificate = Column(String)
    registration_status = Column(String)
    country_code = Column(String, nullable=False, default="US")
    registrant_type = Column(String)
    registrant_name = Column(String)
    registrant_street = Column(String)
    registrant_city = Column(String)
    registrant_state = Column(String)
    registrant_zip = Column(String)
    registrant_country = Column(String)
    last_action_date = Column(Date)
    fractional_owner = Column(String)
    source = Column(String, nullable=False)
    source_url = Column(String)
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    flights = relationship("Flight", back_populates="aircraft")
    operator_fleet_entries = relationship("OperatorFleet", back_populates="aircraft")
    ownership_records = relationship("OwnershipRecord", back_populates="aircraft")
    lien_records = relationship("LienRecord", back_populates="aircraft")
    ntsb_accidents = relationship("NTSBAccident", back_populates="aircraft")
    faa_sdrs = relationship("FAASDR", back_populates="aircraft")
    ofac_matches = relationship("OFACMatch", back_populates="aircraft")


class AircraftType(Base):
    __tablename__ = "aircraft_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    icao_designator = Column(String, unique=True)
    manufacturer = Column(String)
    model = Column(String)
    type_description = Column(String)
    engine_type = Column(String)
    engine_count = Column(Integer)
    wtc = Column(String)
    performance_class = Column(String)
    common_name = Column(String)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)


class TailHistory(Base):
    __tablename__ = "tail_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    serial_number = Column(String)
    n_number = Column(String)
    previous_n_number = Column(String)
    registration_country = Column(String)
    foreign_registration = Column(String)
    event_type = Column(String)
    event_date = Column(Date)
    reason = Column(String)
    registrant_name = Column(String)
    export_country = Column(String)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)
