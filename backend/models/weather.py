from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


class WeatherMETAR(Base):
    __tablename__ = "weather_metars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String)
    airport_id = Column(Integer, ForeignKey("airports.id"))
    observation_time = Column(DateTime, nullable=False)
    raw_text = Column(Text)
    temperature_c = Column(Float)
    dewpoint_c = Column(Float)
    wind_direction_deg = Column(Integer)
    wind_speed_kts = Column(Integer)
    wind_gust_kts = Column(Integer)
    visibility_sm = Column(Float)
    altimeter_inhg = Column(Float)
    ceiling_ft = Column(Integer)
    cloud_layers = Column(Text)
    wx_phenomena = Column(String)
    flight_category = Column(String)
    sea_level_pressure_mb = Column(Float)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    airport = relationship("Airport", back_populates="weather_metars")


class WeatherTAF(Base):
    __tablename__ = "weather_tafs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String)
    airport_id = Column(Integer, ForeignKey("airports.id"))
    issue_time = Column(DateTime, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    raw_text = Column(Text)
    forecast_periods = Column(Text)
    source = Column(String)
    ingested_at = Column(DateTime, default=datetime.utcnow)

    airport = relationship("Airport", back_populates="weather_tafs")
