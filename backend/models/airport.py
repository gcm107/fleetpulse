from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class Airport(Base):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    icao_code = Column(String, unique=True)
    iata_code = Column(String)
    faa_lid = Column(String)
    name = Column(String, nullable=False)
    airport_type = Column(String, nullable=False)
    city = Column(String)
    state_province = Column(String)
    country_code = Column(String, nullable=False)
    continent = Column(String)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation_ft = Column(Integer)
    timezone_iana = Column(String)
    utc_offset = Column(Float)
    dst_rule = Column(String)
    magnetic_variation = Column(Float)
    is_customs_aoe = Column(Boolean, default=False)
    is_slot_controlled = Column(Boolean, default=False)
    has_tower = Column(Boolean, default=False)
    fuel_types = Column(String)
    lighting = Column(String)
    operating_hours = Column(String)
    noise_restrictions = Column(Text)
    website_url = Column(String)
    source = Column(String, nullable=False)
    source_url = Column(String)
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    runways = relationship("Runway", back_populates="airport", cascade="all, delete-orphan")
    frequencies = relationship("AirportFrequency", back_populates="airport", cascade="all, delete-orphan")
    services = relationship("AirportService", back_populates="airport", cascade="all, delete-orphan")
    weather_metars = relationship("WeatherMETAR", back_populates="airport")
    weather_tafs = relationship("WeatherTAF", back_populates="airport")
    notams = relationship("NOTAM", back_populates="airport")


class Runway(Base):
    __tablename__ = "runways"

    id = Column(Integer, primary_key=True, autoincrement=True)
    airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    runway_id_le = Column(String)
    runway_id_he = Column(String)
    length_ft = Column(Integer)
    width_ft = Column(Integer)
    surface_type = Column(String)
    is_lighted = Column(Boolean, default=False)
    is_closed = Column(Boolean, default=False)
    le_latitude = Column(Float)
    le_longitude = Column(Float)
    le_elevation_ft = Column(Integer)
    le_displaced_threshold_ft = Column(Integer)
    le_ils_type = Column(String)
    he_latitude = Column(Float)
    he_longitude = Column(Float)
    he_elevation_ft = Column(Integer)
    he_displaced_threshold_ft = Column(Integer)
    he_ils_type = Column(String)
    source = Column(String, nullable=False)
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    airport = relationship("Airport", back_populates="runways")


class AirportFrequency(Base):
    __tablename__ = "airport_frequencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    frequency_type = Column(String, nullable=False)
    frequency_mhz = Column(Float, nullable=False)
    description = Column(String)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    airport = relationship("Airport", back_populates="frequencies")


class AirportService(Base):
    __tablename__ = "airport_services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    service_type = Column(String, nullable=False)
    provider_name = Column(String)
    phone = Column(String)
    email = Column(String)
    website_url = Column(String)
    operating_hours = Column(String)
    fuel_types = Column(String)
    has_gpu = Column(Boolean)
    has_lavatory_service = Column(Boolean)
    has_hangar_space = Column(Boolean)
    has_deicing = Column(Boolean)
    has_customs = Column(Boolean)
    notes = Column(Text)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    airport = relationship("Airport", back_populates="services")
