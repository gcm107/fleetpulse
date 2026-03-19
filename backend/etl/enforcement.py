"""Enforcement Actions ETL - generate realistic sample FAA enforcement records.

Generates ~30 sample enforcement action records spanning 2018-2025, covering
certificate actions, civil penalties, warnings, and letters of correction.
"""
import logging
import random
from datetime import date, timedelta

from backend.etl.base import get_db_connection, log_ingestion, now_utc

logger = logging.getLogger(__name__)

SOURCE = "sample_enforcement"

# ---------------------------------------------------------------------------
# Reference data for realistic generation
# ---------------------------------------------------------------------------

_ACTION_TYPES = [
    "certificate_action",
    "certificate_action",
    "civil_penalty",
    "civil_penalty",
    "civil_penalty",
    "warning",
    "warning",
    "warning",
    "letter_of_correction",
    "letter_of_correction",
]

_DISPOSITIONS = {
    "certificate_action": ["revocation", "suspension", "dismissed"],
    "civil_penalty": ["fine", "settled", "dismissed"],
    "warning": ["warning", "dismissed"],
    "letter_of_correction": ["letter_of_correction", "dismissed"],
}

_CERTIFICATE_TYPES = [
    "Air Carrier", "Air Carrier", "Air Carrier",
    "Mechanic", "Pilot", "Repair Station",
]

_FAR_VIOLATIONS = [
    ("14 CFR 91.13(a)", "Careless or reckless operation of aircraft"),
    ("14 CFR 91.103", "Failure to become familiar with all available information before flight"),
    ("14 CFR 91.119", "Minimum safe altitude violation - general"),
    ("14 CFR 91.155", "Basic VFR weather minimums - flight below minimums"),
    ("14 CFR 91.175", "IFR takeoff and approach procedures - unauthorized approach"),
    ("14 CFR 91.205", "Required instruments and equipment - inoperative equipment"),
    ("14 CFR 91.409", "Inspections - failure to comply with annual/100-hour inspection"),
    ("14 CFR 91.417", "Maintenance records - inadequate recordkeeping"),
    ("14 CFR 121.135", "Manual requirements - failure to maintain current operations manual"),
    ("14 CFR 121.383", "Airman: limitations on use of services - exceeded duty time"),
    ("14 CFR 121.533", "Responsibility for operational control - inadequate dispatch"),
    ("14 CFR 135.243", "Pilot in command qualifications - unqualified PIC"),
    ("14 CFR 135.263", "Flight time limitations and rest requirements - exceeded limits"),
    ("14 CFR 135.411", "Applicability - failure to comply with maintenance program"),
    ("14 CFR 135.427", "Manual requirements - inadequate maintenance manual"),
    ("14 CFR 43.12", "Maintenance records - falsification of records"),
    ("14 CFR 43.3", "Persons authorized to perform maintenance - unauthorized maintenance"),
    ("14 CFR 61.3", "Requirements for certificates - operating without valid certificate"),
    ("14 CFR 61.57", "Recent experience - pilot currency requirements not met"),
    ("14 CFR 91.7", "Civil aircraft airworthiness - operating unairworthy aircraft"),
]

_RESPONDENT_PATTERNS = [
    "{operator}",
    "{operator}, certificate holder",
    "John {last}, holder of ATP Certificate No. {cert}",
    "Maria {last}, holder of Commercial Pilot Certificate No. {cert}",
    "Robert {last}, holder of Mechanic Certificate No. {cert}",
    "{operator}, d/b/a {dba}",
]

_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Anderson", "Taylor",
    "Thomas", "Hernandez", "Moore", "Martin", "Jackson", "Thompson",
]

# Matching the sample operators from the operators ETL
_OPERATOR_NAMES_FOR_LINK = [
    ("XOJet Inc", "XO"),
    ("NetJets Aviation Inc", "NetJets"),
    ("Flexjet LLC", "Flexjet"),
    ("Wheels Up Partners LLC", "Wheels Up"),
    ("Clay Lacy Aviation Inc", "Clay Lacy"),
    ("Priester Aviation LLC", "Priester Aviation"),
    ("Swift Charter Corp", None),
    ("AeroDynamic Charter LLC", None),
]


def _random_date(start_year: int, end_year: int) -> str:
    """Return a random date string between start_year-01-01 and end_year-12-31."""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.isoformat()


def generate_sample_enforcement(db_path: str):
    """Generate ~30 realistic sample enforcement action records.

    Creates a mix of certificate actions, civil penalties, warnings, and
    letters of correction, some linked to existing operators in the database.
    """
    started_at = now_utc()
    conn = get_db_connection(db_path)
    now = now_utc()
    inserted = errored = 0
    total = 30

    try:
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

        records = []

        for i in range(1, total + 1):
            action_type = random.choice(_ACTION_TYPES)
            disposition = random.choice(_DISPOSITIONS[action_type])
            year = random.randint(2018, 2025)
            action_date = _random_date(year, year)
            case_number = f"EA-{year}-{random.choice(['NE', 'GL', 'SW', 'WP', 'EA', 'SO'])}-{i:04d}"

            cert_type = random.choice(_CERTIFICATE_TYPES)
            cert_number = f"{random.choice(['A', 'C', 'M', 'R'])}{random.randint(100000, 999999)}"

            # Pick FAR violation(s)
            num_violations = random.randint(1, 3)
            violations = random.sample(_FAR_VIOLATIONS, num_violations)
            far_sections = "; ".join(v[0] for v in violations)
            violation_desc = ". ".join(v[1] for v in violations) + "."

            # Penalty amount
            if action_type == "civil_penalty":
                if disposition == "fine":
                    penalty_amount = random.choice([
                        5000, 7500, 10000, 15000, 25000, 50000, 75000,
                        100000, 150000, 250000, 500000,
                    ])
                elif disposition == "settled":
                    penalty_amount = random.choice([
                        2500, 5000, 7500, 10000, 25000, 50000, 75000,
                    ])
                else:
                    penalty_amount = 0.0
            else:
                penalty_amount = None

            # Suspension days
            suspension_days = None
            if disposition == "suspension":
                suspension_days = random.choice([30, 60, 90, 120, 180, 365])

            # Effective / expiration dates
            effective_date = action_date
            expiration_date = None
            if suspension_days:
                eff = date.fromisoformat(action_date)
                expiration_date = (eff + timedelta(days=suspension_days)).isoformat()

            # Respondent name and operator linkage
            operator_id = None
            if random.random() < 0.5 and _OPERATOR_NAMES_FOR_LINK:
                op_name, dba = random.choice(_OPERATOR_NAMES_FOR_LINK)
                operator_id = existing_operators.get(op_name)
                if dba:
                    respondent = f"{op_name}, d/b/a {dba}"
                else:
                    respondent = f"{op_name}, certificate holder"
            else:
                last = random.choice(_LAST_NAMES)
                cert_label = random.choice(["ATP", "Commercial Pilot", "Mechanic"])
                respondent = f"{random.choice(['John', 'Robert', 'James', 'Maria', 'Susan', 'Patricia'])} {last}, holder of {cert_label} Certificate No. {cert_number}"

            records.append((
                case_number, action_date, action_type, respondent,
                operator_id, cert_type, cert_number,
                violation_desc, far_sections, penalty_amount,
                disposition, suspension_days, effective_date,
                expiration_date, SOURCE, now,
            ))

        # Insert all records
        for rec in records:
            try:
                conn.execute(
                    """
                    INSERT INTO enforcement_actions (
                        case_number, action_date, action_type, respondent_name,
                        operator_id, certificate_type, certificate_number,
                        violation_description, far_sections_violated, penalty_amount,
                        disposition, suspension_days, effective_date,
                        expiration_date, source, ingested_at
                    ) VALUES (
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?
                    )
                    ON CONFLICT(case_number) DO UPDATE SET
                        action_date = excluded.action_date,
                        action_type = excluded.action_type,
                        respondent_name = excluded.respondent_name,
                        operator_id = excluded.operator_id,
                        certificate_type = excluded.certificate_type,
                        certificate_number = excluded.certificate_number,
                        violation_description = excluded.violation_description,
                        far_sections_violated = excluded.far_sections_violated,
                        penalty_amount = excluded.penalty_amount,
                        disposition = excluded.disposition,
                        suspension_days = excluded.suspension_days,
                        effective_date = excluded.effective_date,
                        expiration_date = excluded.expiration_date,
                        source = excluded.source,
                        ingested_at = excluded.ingested_at
                    """,
                    rec,
                )
                inserted += 1

            except Exception as e:
                errored += 1
                logger.warning(f"Error inserting enforcement record {rec[0]}: {e}")

        conn.commit()
        logger.info(
            f"Enforcement sample data: {total} processed, {inserted} inserted, "
            f"{errored} errors"
        )

        log_ingestion(
            conn,
            module="enforcement",
            source=SOURCE,
            started_at=started_at,
            records_processed=total,
            records_inserted=inserted,
            records_updated=0,
            records_errored=errored,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Enforcement sample data generation failed: {e}")
        log_ingestion(
            conn,
            module="enforcement",
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


def run_enforcement_etl(db_path: str):
    """Run the enforcement actions ETL pipeline.

    Generates sample enforcement action data.
    """
    logger.info("Running Enforcement ETL (sample data generation)")
    generate_sample_enforcement(db_path)
    logger.info("Enforcement ETL completed.")


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    db = sys.argv[1] if len(sys.argv) > 1 else "fleetpulse.db"
    run_enforcement_etl(db)
