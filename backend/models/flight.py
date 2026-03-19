from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.database import Base


class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"))
    transponder_hex = Column(String)
    callsign = Column(String)
    origin_icao = Column(String)
    destination_icao = Column(String)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    flight_date = Column(Date)
    estimated_duration_min = Column(Integer)
    squawk = Column(String)
    is_live = Column(Boolean, default=False)
    source = Column(String, nullable=False)
    ingested_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    aircraft = relationship("Aircraft", back_populates="flights")
    positions = relationship("FlightPosition", back_populates="flight", cascade="all, delete-orphan")


class FlightPosition(Base):
    __tablename__ = "flight_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude_ft = Column(Integer)
    geo_altitude_ft = Column(Integer)
    ground_speed_kts = Column(Float)
    track_deg = Column(Float)
    vertical_rate_fpm = Column(Integer)
    on_ground = Column(Boolean, default=False)
    squawk = Column(String)

    flight = relationship("Flight", back_populates="positions")
