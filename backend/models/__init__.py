from backend.models.aircraft import Aircraft, AircraftType, TailHistory
from backend.models.airport import Airport, AirportFrequency, AirportService, Runway
from backend.models.flight import Flight, FlightPosition
from backend.models.ingestion import IngestionLog
from backend.models.notam import NOTAM, TFR
from backend.models.ofac import OFACMatch, OFACSDN
from backend.models.operator import Operator, OperatorFleet, OperatorOpSpec
from backend.models.ownership import LienRecord, OwnershipRecord
from backend.models.safety import (
    AirworthinessDirective,
    EnforcementAction,
    FAASDR,
    NTSBAccident,
    SafetyScore,
)
from backend.models.weather import WeatherMETAR, WeatherTAF
