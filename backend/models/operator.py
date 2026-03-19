from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class Operator(Base):
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    certificate_number = Column(String, unique=True)
    certificate_type = Column(String, nullable=False)
    holder_name = Column(String, nullable=False)
    dba_name = Column(String)
    street_address = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    country_code = Column(String, default="US")
    phone = Column(String)
    certificate_issue_date = Column(Date)
    certificate_expiration_date = Column(Date)
    certificate_status = Column(String)
    dot_fitness_date = Column(Date)
    dot_fitness_status = Column(String)
    district_office = Column(String)
    operations_base = Column(String)
    wet_lease_authority = Column(Boolean, default=False)
    dry_lease_authority = Column(Boolean, default=False)
    on_demand_authority = Column(Boolean, default=False)
    scheduled_authority = Column(Boolean, default=False)
    authorized_aircraft_count = Column(Integer)
    source = Column(String, nullable=False)
    source_url = Column(String)
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    fleet = relationship("OperatorFleet", back_populates="operator", cascade="all, delete-orphan")
    opspecs = relationship("OperatorOpSpec", back_populates="operator", cascade="all, delete-orphan")
    ntsb_accidents = relationship("NTSBAccident", back_populates="operator")
    enforcement_actions = relationship("EnforcementAction", back_populates="operator")


class OperatorFleet(Base):
    __tablename__ = "operator_fleet"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=False)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"))
    n_number = Column(String)
    role = Column(String)
    effective_date = Column(Date)
    expiration_date = Column(Date)
    is_active = Column(Boolean, default=True)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    operator = relationship("Operator", back_populates="fleet")
    aircraft = relationship("Aircraft", back_populates="operator_fleet_entries")


class OperatorOpSpec(Base):
    __tablename__ = "operator_opspecs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=False)
    opspec_code = Column(String)
    opspec_description = Column(Text)
    authorized_aircraft_types = Column(Text)
    geographic_authority = Column(Text)
    effective_date = Column(Date)
    amendment_date = Column(Date)
    status = Column(String)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    operator = relationship("Operator", back_populates="opspecs")
