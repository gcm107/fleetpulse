from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class OwnershipRecord(Base):
    __tablename__ = "ownership_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"))
    n_number = Column(String)
    owner_type = Column(String)
    owner_name = Column(String)
    owner_street = Column(String)
    owner_city = Column(String)
    owner_state = Column(String)
    owner_zip = Column(String)
    owner_country = Column(String)
    trustee_name = Column(String)
    fractional_program = Column(String)
    ownership_share = Column(Float)
    effective_date = Column(Date)
    expiration_date = Column(Date)
    is_current = Column(Boolean, default=True)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    aircraft = relationship("Aircraft", back_populates="ownership_records")


class LienRecord(Base):
    __tablename__ = "lien_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"))
    n_number = Column(String)
    document_type = Column(String)
    recording_date = Column(Date)
    document_number = Column(String)
    lien_holder_name = Column(String)
    lien_holder_address = Column(Text)
    lien_amount = Column(Float)
    maturity_date = Column(Date)
    is_released = Column(Boolean, default=False)
    release_date = Column(Date)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    aircraft = relationship("Aircraft", back_populates="lien_records")
