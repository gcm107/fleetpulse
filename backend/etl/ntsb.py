"""NTSB Accident ETL - generate realistic sample NTSB accident records.

Since the actual NTSB download (avall.zip) contains an Access DB that
requires mdbtools to parse, this module provides a sample-data generator
that creates ~100 realistic accident/incident records spanning 2015-2025.
"""
import logging
import random
from datetime import date, timedelta

from backend.etl.base import get_db_connection, log_ingestion, now_utc

logger = logging.getLogger(__name__)

SOURCE = "sample_ntsb"

# ---------------------------------------------------------------------------
# Reference data for realistic generation
# ---------------------------------------------------------------------------

_REGIONS = [
    ("ERA", "Eastern"),
    ("CEN", "Central"),
    ("WPR", "Western"),
]

_EVENT_TYPES = ["Accident", "Incident"]

_AIRCRAFT_TYPES = [
    ("Cessna", "172S"),
    ("Cessna", "182T"),
    ("Cessna", "206H"),
    ("Cessna", "210N"),
    ("Cessna", "525 Citation CJ1"),
    ("Piper", "PA-28-181"),
    ("Piper", "PA-32R-301"),
    ("Piper", "PA-46-350P"),
    ("Beechcraft", "King Air 350"),
    ("Beechcraft", "Baron 58"),
    ("Beechcraft", "Bonanza A36"),
    ("Bombardier", "CL-600-2B16"),
    ("Embraer", "EMB-505"),
    ("Gulfstream", "GV-SP"),
    ("Gulfstream", "G280"),
    ("Dassault", "Falcon 900EX"),
    ("Cirrus", "SR22"),
    ("Mooney", "M20J"),
    ("Diamond", "DA40"),
    ("Pilatus", "PC-12/47E"),
]

_CITIES = [
    ("Miami", "FL", "US", 25.76, -80.19),
    ("Dallas", "TX", "US", 32.78, -96.80),
    ("Denver", "CO", "US", 39.74, -104.99),
    ("Phoenix", "AZ", "US", 33.45, -112.07),
    ("Atlanta", "GA", "US", 33.75, -84.39),
    ("Los Angeles", "CA", "US", 34.05, -118.24),
    ("Chicago", "IL", "US", 41.88, -87.63),
    ("Teterboro", "NJ", "US", 40.85, -74.06),
    ("Van Nuys", "CA", "US", 34.19, -118.49),
    ("Opa-locka", "FL", "US", 25.91, -80.28),
    ("Scottsdale", "AZ", "US", 33.49, -111.93),
    ("Columbus", "OH", "US", 39.96, -82.99),
    ("San Antonio", "TX", "US", 29.42, -98.49),
    ("Anchorage", "AK", "US", 61.22, -149.90),
    ("Honolulu", "HI", "US", 21.31, -157.86),
    ("Wichita", "KS", "US", 37.69, -97.34),
    ("Savannah", "GA", "US", 32.08, -81.09),
    ("Farmingdale", "NY", "US", 40.73, -73.42),
    ("Centennial", "CO", "US", 39.57, -104.85),
    ("Naples", "FL", "US", 26.14, -81.79),
]

_PHASES = ["Takeoff", "Initial climb", "Cruise", "Approach", "Landing", "Taxi", "Maneuvering"]
_WEATHER = ["VMC", "IMC"]
_FAR_PARTS = ["91", "135", "121"]
_FLIGHT_PURPOSE = [
    "Personal", "Business", "Instructional", "Aerial observation",
    "Positioning", "Charter/air taxi", "Scheduled",
]
_DAMAGE = ["Substantial", "Destroyed", "Minor", "None"]
_REPORT_STATUS = ["Probable Cause", "Factual", "Preliminary"]

_PROBABLE_CAUSES = [
    "The pilot's failure to maintain directional control during the landing roll.",
    "The pilot's inadequate preflight inspection, which resulted in a fuel exhaustion condition during cruise flight.",
    "The pilot's failure to maintain adequate airspeed during the approach, resulting in an aerodynamic stall.",
    "The loss of engine power due to fuel contamination.",
    "The pilot's improper decision to continue VFR flight into instrument meteorological conditions.",
    "The pilot's failure to maintain adequate altitude during maneuvering flight.",
    "A total loss of engine power due to a fractured crankshaft.",
    "The pilot's loss of control during a go-around maneuver.",
    "The collapse of the nose landing gear during the landing roll due to a fatigue fracture of the nose gear trunnion.",
    "The pilot's failure to extend the landing gear before touchdown.",
    "A birdstrike during the takeoff climb that resulted in a loss of engine power.",
    "An in-flight breakup due to the pilot's exceedance of the design stress limits of the airplane during an inadvertent encounter with severe turbulence.",
    "The pilot's spatial disorientation due to continued VFR flight into night IMC conditions.",
    "Improper maintenance that resulted in a hydraulic system failure and subsequent loss of flight control.",
    "The flight crew's failure to monitor fuel quantity, resulting in fuel exhaustion in both engines.",
    "A runway excursion following a hydroplane event during the landing roll in heavy rain.",
    "The failure of the number 2 engine due to uncontained turbine blade separation.",
    "The pilot's delayed remedial action to address a partial power loss on takeoff.",
    "The flight crew's improper configuration of the autopilot, leading to a controlled flight into terrain.",
    "A loss of engine power during initial climb due to carburetor icing.",
]

# Operator names that may match the sample operators from the operators ETL
_OPERATOR_NAMES = [
    "XOJet Inc", "NetJets Aviation Inc", "Flexjet LLC",
    "ExcelAire Service Inc", "Jet Aviation Flight Services Inc",
    "Wheels Up Partners LLC", "Clay Lacy Aviation Inc",
    "Priester Aviation LLC", "Private Owner", "Private Owner",
    "Private Owner", "Private Owner", "Private Owner",
    "Private Owner", "Flight School Inc", "Regional Air LLC",
    "Cargo Express Inc", "Survey Aviation Corp",
]


def _random_date(start_year: int, end_year: int) -> str:
    """Return a random date string between start_year-01-01 and end_year-12-31."""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.isoformat()


def _generate_ntsb_number(region: str, year: int, suffix: str, seq: int) -> str:
    """Generate a realistic NTSB number like ERA25LA123."""
    return f"{region}{year % 100:02d}{suffix}{seq:03d}"


def generate_sample_ntsb_data(db_path: str):
    """Generate ~100 realistic sample NTSB accident records spanning 2015-2025.

    Produces a mix of fatal, serious, minor, and no-injury events across
    various aircraft types, operators, phases of flight, and weather conditions.
    Records are linked to existing aircraft and operators in the database where
    possible.
    """
    started_at = now_utc()
    conn = get_db_connection(db_path)
    now = now_utc()
    inserted = updated = errored = 0
    total = 100

    try:
        # Fetch existing aircraft N-numbers for linking
        existing_aircraft = {}
        try:
            rows = conn.execute(
                "SELECT id, n_number, manufacturer, model FROM aircraft LIMIT 500"
            ).fetchall()
            for row in rows:
                existing_aircraft[row[1]] = {"id": row[0], "make_model": f"{row[2]} {row[3]}"}
        except Exception:
            pass

        # Fetch existing operators for linking
        existing_operators = {}
        try:
            rows = conn.execute(
                "SELECT id, holder_name FROM operators"
            ).fetchall()
            for row in rows:
                existing_operators[row[1]] = row[0]
        except Exception:
            pass

        # Plan the severity distribution
        severity_plan = (
            [("Fatal", 7)] +
            [("Serious", 12)] +
            [("Minor", 35)] +
            [("None", 46)]
        )
        records = []
        seq = 1

        for severity, count in severity_plan:
            for _ in range(count):
                region_code, _ = random.choice(_REGIONS)
                year = random.randint(2015, 2025)

                if severity == "Fatal":
                    suffix = "FA"
                    event_type = "Accident"
                elif severity == "Serious":
                    suffix = "LA"
                    event_type = "Accident"
                elif severity == "Minor":
                    suffix = random.choice(["LA", "IA"])
                    event_type = random.choice(["Accident", "Incident"])
                else:
                    suffix = "IA"
                    event_type = "Incident"

                ntsb_number = _generate_ntsb_number(region_code, year, suffix, seq)
                seq += 1

                event_date = _random_date(year, year)
                city_info = random.choice(_CITIES)
                mfr, mdl = random.choice(_AIRCRAFT_TYPES)
                make_model = f"{mfr} {mdl}"

                # Try to link to a real aircraft
                aircraft_id = None
                n_number = None
                if existing_aircraft and random.random() < 0.3:
                    rand_n = random.choice(list(existing_aircraft.keys()))
                    aircraft_id = existing_aircraft[rand_n]["id"]
                    n_number = rand_n
                    make_model = existing_aircraft[rand_n]["make_model"]
                else:
                    n_number = f"{random.randint(1, 9)}{random.randint(1000, 99999)}"

                # Operator
                operator_name = random.choice(_OPERATOR_NAMES)
                operator_id = existing_operators.get(operator_name)

                # Severity-based injury counts
                if severity == "Fatal":
                    fatal = random.randint(1, 4)
                    serious = random.randint(0, 2)
                    minor = random.randint(0, 2)
                    uninjured = random.randint(0, 3)
                    damage = random.choice(["Destroyed", "Substantial"])
                elif severity == "Serious":
                    fatal = 0
                    serious = random.randint(1, 3)
                    minor = random.randint(0, 3)
                    uninjured = random.randint(0, 5)
                    damage = random.choice(["Substantial", "Destroyed"])
                elif severity == "Minor":
                    fatal = 0
                    serious = 0
                    minor = random.randint(1, 2)
                    uninjured = random.randint(1, 4)
                    damage = random.choice(["Substantial", "Minor"])
                else:
                    fatal = 0
                    serious = 0
                    minor = 0
                    uninjured = random.randint(1, 6)
                    damage = random.choice(["Minor", "None"])

                far_part = random.choice(_FAR_PARTS)
                phase = random.choice(_PHASES)
                weather = random.choices(_WEATHER, weights=[85, 15])[0]
                purpose = random.choice(_FLIGHT_PURPOSE)
                cause = random.choice(_PROBABLE_CAUSES)
                status = random.choice(_REPORT_STATUS)
                report_url = f"https://data.ntsb.gov/carol-repgen/api/Aviation/ReportMain/GenerateNewestReport/{ntsb_number}/pdf"

                records.append((
                    ntsb_number, event_date, city_info[0], city_info[1],
                    city_info[2], city_info[3], city_info[4],
                    event_type, n_number, aircraft_id, make_model,
                    operator_name, operator_id, far_part, purpose,
                    phase, weather, severity, fatal, serious, minor,
                    uninjured, damage, cause, status, report_url,
                    SOURCE, now,
                ))

        # Insert all records
        for rec in records:
            try:
                conn.execute(
                    """
                    INSERT INTO ntsb_accidents (
                        ntsb_number, event_date, event_city, event_state,
                        event_country, event_latitude, event_longitude,
                        event_type, n_number, aircraft_id, aircraft_make_model,
                        operator_name, operator_id, far_part, flight_purpose,
                        phase_of_flight, weather_condition, highest_injury,
                        fatal_count, serious_count, minor_count, uninjured_count,
                        aircraft_damage, probable_cause, report_status,
                        report_url, source, ingested_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?
                    )
                    ON CONFLICT(ntsb_number) DO UPDATE SET
                        event_date = excluded.event_date,
                        event_city = excluded.event_city,
                        event_state = excluded.event_state,
                        event_country = excluded.event_country,
                        event_latitude = excluded.event_latitude,
                        event_longitude = excluded.event_longitude,
                        event_type = excluded.event_type,
                        n_number = excluded.n_number,
                        aircraft_id = excluded.aircraft_id,
                        aircraft_make_model = excluded.aircraft_make_model,
                        operator_name = excluded.operator_name,
                        operator_id = excluded.operator_id,
                        far_part = excluded.far_part,
                        flight_purpose = excluded.flight_purpose,
                        phase_of_flight = excluded.phase_of_flight,
                        weather_condition = excluded.weather_condition,
                        highest_injury = excluded.highest_injury,
                        fatal_count = excluded.fatal_count,
                        serious_count = excluded.serious_count,
                        minor_count = excluded.minor_count,
                        uninjured_count = excluded.uninjured_count,
                        aircraft_damage = excluded.aircraft_damage,
                        probable_cause = excluded.probable_cause,
                        report_status = excluded.report_status,
                        report_url = excluded.report_url,
                        source = excluded.source,
                        ingested_at = excluded.ingested_at
                    """,
                    rec,
                )

                # Check if it was an insert or update by rowcount
                cursor = conn.execute(
                    "SELECT changes()"
                )
                changes = cursor.fetchone()[0]
                if changes:
                    inserted += 1

            except Exception as e:
                errored += 1
                logger.warning(f"Error inserting NTSB record {rec[0]}: {e}")

        conn.commit()
        logger.info(
            f"NTSB sample data: {total} processed, {inserted} inserted, "
            f"{updated} updated, {errored} errors"
        )

        log_ingestion(
            conn,
            module="ntsb",
            source=SOURCE,
            started_at=started_at,
            records_processed=total,
            records_inserted=inserted,
            records_updated=updated,
            records_errored=errored,
            status="completed",
        )

    except Exception as e:
        logger.error(f"NTSB sample data generation failed: {e}")
        log_ingestion(
            conn,
            module="ntsb",
            source=SOURCE,
            started_at=started_at,
            records_processed=0,
            records_inserted=0,
            records_updated=0,
            records_errored=0,
            status="failed",
            error_message=str(e),
        )
        raise
    finally:
        conn.close()


def run_ntsb_etl(db_path: str):
    """Run the NTSB ETL pipeline.

    Generates sample NTSB accident data since the real NTSB Access DB
    requires mdbtools to parse.
    """
    logger.info("Running NTSB ETL (sample data generation)")
    generate_sample_ntsb_data(db_path)
    logger.info("NTSB ETL completed.")


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    db = sys.argv[1] if len(sys.argv) > 1 else "fleetpulse.db"
    run_ntsb_etl(db)
