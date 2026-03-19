from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class OFACSDN(Base):
    __tablename__ = "ofac_sdn"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sdn_entry_id = Column(Integer, unique=True)
    sdn_type = Column(String)
    primary_name = Column(String)
    aliases = Column(Text)
    program_list = Column(String)
    country = Column(String)
    id_type = Column(String)
    id_number = Column(String)
    remarks = Column(Text)
    aircraft_tail_numbers = Column(Text)
    aircraft_type = Column(String)
    source = Column(String)
    source_url = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    matches = relationship("OFACMatch", back_populates="sdn", cascade="all, delete-orphan")


class OFACMatch(Base):
    __tablename__ = "ofac_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"))
    sdn_id = Column(Integer, ForeignKey("ofac_sdn.id"))
    match_type = Column(String)
    match_confidence = Column(Float)
    matched_value = Column(String)
    sdn_value = Column(String)
    is_confirmed = Column(Boolean, nullable=True)
    reviewed_at = Column(DateTime)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    aircraft = relationship("Aircraft", back_populates="ofac_matches")
    sdn = relationship("OFACSDN", back_populates="matches")
