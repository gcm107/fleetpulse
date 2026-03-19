from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class NOTAM(Base):
    __tablename__ = "notams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notam_id = Column(String, unique=True)
    airport_icao = Column(String)
    airport_id = Column(Integer, ForeignKey("airports.id"))
    classification = Column(String)
    category = Column(String)
    effective_start = Column(DateTime, nullable=False)
    effective_end = Column(DateTime)
    text = Column(Text, nullable=False)
    affected_fdc = Column(String)
    min_altitude_ft = Column(Integer)
    max_altitude_ft = Column(Integer)
    is_active = Column(Boolean, default=True)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    airport = relationship("Airport", back_populates="notams")


class TFR(Base):
    __tablename__ = "tfrs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tfr_id = Column(String, unique=True)
    notam_id = Column(String)
    reason = Column(String)
    effective_start = Column(DateTime, nullable=False)
    effective_end = Column(DateTime)
    description = Column(Text)
    center_latitude = Column(Float)
    center_longitude = Column(Float)
    radius_nm = Column(Float)
    floor_altitude_ft = Column(Integer)
    ceiling_altitude_ft = Column(Integer)
    boundary_geojson = Column(Text)
    is_active = Column(Boolean, default=True)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)
