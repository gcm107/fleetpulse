"""Safety Scoring Engine - compute safety scores for operators and aircraft.

Implements a weighted composite scoring methodology that evaluates entities
across multiple safety dimensions including accident history, enforcement
actions, SDR frequency, fleet age, certificate tenure, and AD compliance.
"""
import json
import logging
from datetime import date, timedelta

from backend.etl.base import get_db_connection, log_ingestion, now_utc

logger = logging.getLogger(__name__)

SOURCE = "derived"
METHODOLOGY_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Scoring utility functions
# ---------------------------------------------------------------------------


def lerp(value: float, x0: float, y0: float, x1: float, y1: float) -> float:
    """Linear interpolation between two points, clamped to [min(y0,y1), max(y0,y1)].

    Maps *value* from the range [x0, x1] onto [y0, y1]. Values outside the
    input range are clamped so the result never exceeds the output bounds.
    """
    if x1 == x0:
        return y0
    t = (value - x0) / (x1 - x0)
    t = max(0.0, min(1.0, t))
    return y0 + t * (y1 - y0)


def score_from_breakpoints(value: float, breakpoints: list[tuple[float, float]]) -> float:
    """Piecewise linear scoring from a list of (x, score) breakpoint pairs.

    *breakpoints* must be sorted in ascending order by x. Values below the
    first breakpoint get the first score; values above the last breakpoint
    get the last score. Between breakpoints, linear interpolation is used.
    """
    if not breakpoints:
        return 100.0

    # Below the first breakpoint
    if value <= breakpoints[0][0]:
        return breakpoints[0][1]

    # Above the last breakpoint
    if value >= breakpoints[-1][0]:
        return breakpoints[-1][1]

    # Find the two surrounding breakpoints and interpolate
    for i in range(len(breakpoints) - 1):
        x0, y0 = breakpoints[i]
        x1, y1 = breakpoints[i + 1]
        if x0 <= value <= x1:
            return lerp(value, x0, y0, x1, y1)

    return breakpoints[-1][1]


# ---------------------------------------------------------------------------
# Operator scoring constants
# ---------------------------------------------------------------------------

_OP_ACCIDENT_WEIGHT = 0.30
_OP_ENFORCEMENT_WEIGHT = 0.20
_OP_SDR_WEIGHT = 0.15
_OP_FLEET_AGE_WEIGHT = 0.15
_OP_CERT_TENURE_WEIGHT = 0.10
_OP_AD_COMPLIANCE_WEIGHT = 0.10

# Accident severity penalties
_ACCIDENT_PENALTIES = {
    "Fatal": -40,
    "Serious": -25,
    "Minor": -15,
    "None": -5,
    "Incident": -5,
}

# Enforcement disposition penalties
_ENFORCEMENT_PENALTIES = {
    "revocation": -50,
    "suspension": -30,
}

# SDR rate ratio breakpoints (rate_ratio -> score)
_SDR_RATE_BREAKPOINTS = [
    (0.0, 100),
    (0.5, 90),
    (1.0, 75),
    (1.5, 60),
    (2.0, 45),
    (3.0, 25),
    (5.0, 10),
]
_INDUSTRY_AVG_SDR_RATE = 2.5  # SDRs per aircraft per year

# Fleet age breakpoints (average_age_years -> score)
_FLEET_AGE_BREAKPOINTS = [
    (5, 100),
    (10, 85),
    (15, 70),
    (20, 55),
    (25, 40),
    (30, 25),
    (40, 10),
]

# Certificate tenure breakpoints (years -> score)
_CERT_TENURE_BREAKPOINTS = [
    (0, 15),
    (1, 25),
    (2, 40),
    (5, 60),
    (10, 80),
    (20, 100),
]

# AD burden ratio breakpoints (ads_per_aircraft -> score)
_AD_BURDEN_BREAKPOINTS = [
    (0, 100),
    (2, 90),
    (5, 75),
    (10, 60),
    (20, 40),
    (40, 20),
    (80, 10),
]

# ---------------------------------------------------------------------------
# Aircraft scoring constants
# ---------------------------------------------------------------------------

_AC_ACCIDENT_WEIGHT = 0.25
_AC_SDR_WEIGHT = 0.25
_AC_AGE_WEIGHT = 0.15
_AC_AD_WEIGHT = 0.15
_AC_OPERATOR_WEIGHT = 0.10
_AC_OWNERSHIP_WEIGHT = 0.10

# Aircraft accident penalties (no time decay for airframes)
_AC_ACCIDENT_PENALTIES = {
    "Fatal": -50,
    "Serious": -35,
    "Minor": -20,
    "None": -10,
    "Incident": -10,
}

# SDR count breakpoints for aircraft
_AC_SDR_BREAKPOINTS = [
    (0, 100),
    (2, 85),
    (5, 70),
    (10, 50),
    (20, 25),
    (30, 10),
]

# Ownership stability breakpoints (tail_history events in 10 years -> score)
_OWNERSHIP_BREAKPOINTS = [
    (0, 100),
    (1, 85),
    (2, 70),
    (3, 50),
    (5, 20),
]


# ---------------------------------------------------------------------------
# Operator scoring implementation
# ---------------------------------------------------------------------------


def _score_operator_accidents(conn, operator_id: int, fleet_size: int) -> tuple[float, dict]:
    """Score an operator's accident history over the last 10 years.

    Returns (score, details_dict).
    """
    today = date.today()
    ten_years_ago = today - timedelta(days=3650)
    five_years_ago = today - timedelta(days=1825)

    rows = conn.execute(
        """
        SELECT highest_injury, event_date
        FROM ntsb_accidents
        WHERE operator_id = ? AND event_date >= ?
        """,
        (operator_id, ten_years_ago.isoformat()),
    ).fetchall()

    total_penalty = 0.0
    counts = {"fatal": 0, "serious": 0, "minor": 0, "incident": 0}

    for row in rows:
        injury = row[0] or "None"
        event_date_str = row[1]

        penalty = _ACCIDENT_PENALTIES.get(injury, -5)

        # Time decay: 50% for events older than 5 years
        try:
            event_date = date.fromisoformat(event_date_str) if isinstance(event_date_str, str) else event_date_str
            if event_date < five_years_ago:
                penalty *= 0.5
        except (ValueError, TypeError):
            pass

        total_penalty += penalty

        if injury == "Fatal":
            counts["fatal"] += 1
        elif injury == "Serious":
            counts["serious"] += 1
        elif injury == "Minor":
            counts["minor"] += 1
        else:
            counts["incident"] += 1

    # Normalize by fleet size (minimum 1 to avoid division by zero)
    normalizer = max(fleet_size, 1)
    normalized_penalty = total_penalty / normalizer

    # Convert penalty to score (start at 100)
    score = max(0.0, min(100.0, 100.0 + normalized_penalty * 10))

    details = {
        "total_events": len(rows),
        "counts": counts,
        "raw_penalty": total_penalty,
        "fleet_size_normalizer": normalizer,
    }
    return score, details


def _score_operator_enforcement(conn, operator_id: int) -> tuple[float, dict]:
    """Score an operator's enforcement history.

    Returns (score, details_dict).
    """
    today = date.today()
    ten_years_ago = today - timedelta(days=3650)
    five_years_ago = today - timedelta(days=1825)

    rows = conn.execute(
        """
        SELECT disposition, penalty_amount, action_date
        FROM enforcement_actions
        WHERE operator_id = ? AND action_date >= ?
        """,
        (operator_id, ten_years_ago.isoformat()),
    ).fetchall()

    total_penalty = 0.0
    counts = {"revocations": 0, "suspensions": 0, "penalties": 0, "warnings": 0, "letters": 0}

    for row in rows:
        disposition = (row[0] or "").lower()
        penalty_amount = row[1] or 0.0
        action_date_str = row[2]

        # Determine penalty value based on disposition
        if disposition in _ENFORCEMENT_PENALTIES:
            pen = _ENFORCEMENT_PENALTIES[disposition]
        elif disposition in ("fine", "settled"):
            if penalty_amount > 50000:
                pen = -25
            elif penalty_amount > 10000:
                pen = -15
            else:
                pen = -10
        elif disposition == "warning":
            pen = -5
        elif disposition in ("letter_of_correction", "letter"):
            pen = -3
        elif disposition == "dismissed":
            pen = 0
        else:
            pen = -5

        # Time decay: 50% for events older than 5 years
        try:
            action_date = date.fromisoformat(action_date_str) if isinstance(action_date_str, str) else action_date_str
            if action_date < five_years_ago:
                pen *= 0.5
        except (ValueError, TypeError):
            pass

        total_penalty += pen

        if disposition == "revocation":
            counts["revocations"] += 1
        elif disposition == "suspension":
            counts["suspensions"] += 1
        elif disposition in ("fine", "settled"):
            counts["penalties"] += 1
        elif disposition == "warning":
            counts["warnings"] += 1
        elif disposition in ("letter_of_correction", "letter"):
            counts["letters"] += 1

    score = max(0.0, min(100.0, 100.0 + total_penalty))
    details = {"total_actions": len(rows), "counts": counts, "raw_penalty": total_penalty}
    return score, details


def _score_operator_sdrs(conn, operator_id: int, fleet_size: int) -> tuple[float, dict]:
    """Score an operator's SDR frequency relative to industry average.

    Returns (score, details_dict).
    """
    # Get fleet aircraft IDs
    fleet_ids = conn.execute(
        "SELECT aircraft_id FROM operator_fleet WHERE operator_id = ? AND is_active = 1",
        (operator_id,),
    ).fetchall()

    aircraft_ids = [r[0] for r in fleet_ids if r[0] is not None]

    if not aircraft_ids or fleet_size == 0:
        return 100.0, {"sdr_count": 0, "fleet_size": fleet_size, "rate_ratio": 0}

    placeholders = ",".join("?" * len(aircraft_ids))
    one_year_ago = (date.today() - timedelta(days=365)).isoformat()

    row = conn.execute(
        f"SELECT COUNT(*) FROM faa_sdrs WHERE aircraft_id IN ({placeholders}) AND report_date >= ?",
        aircraft_ids + [one_year_ago],
    ).fetchone()

    sdr_count = row[0] if row else 0
    operator_rate = sdr_count / max(fleet_size, 1)
    rate_ratio = operator_rate / _INDUSTRY_AVG_SDR_RATE if _INDUSTRY_AVG_SDR_RATE > 0 else 0

    score = score_from_breakpoints(rate_ratio, _SDR_RATE_BREAKPOINTS)
    details = {
        "sdr_count": sdr_count,
        "fleet_size": fleet_size,
        "operator_rate": round(operator_rate, 2),
        "rate_ratio": round(rate_ratio, 2),
    }
    return score, details


def _score_operator_fleet_age(conn, operator_id: int) -> tuple[float, dict]:
    """Score an operator based on average fleet age.

    Returns (score, details_dict).
    """
    rows = conn.execute(
        """
        SELECT a.year_mfr
        FROM operator_fleet of_
        JOIN aircraft a ON of_.aircraft_id = a.id
        WHERE of_.operator_id = ? AND of_.is_active = 1 AND a.year_mfr IS NOT NULL
        """,
        (operator_id,),
    ).fetchall()

    if not rows:
        return 70.0, {"avg_age": None, "aircraft_count": 0}

    current_year = date.today().year
    ages = [current_year - r[0] for r in rows if r[0] and r[0] > 1900]

    if not ages:
        return 70.0, {"avg_age": None, "aircraft_count": 0}

    avg_age = sum(ages) / len(ages)
    score = score_from_breakpoints(avg_age, _FLEET_AGE_BREAKPOINTS)
    details = {"avg_age": round(avg_age, 1), "aircraft_count": len(ages)}
    return score, details


def _score_operator_cert_tenure(conn, operator_id: int) -> tuple[float, dict]:
    """Score an operator based on certificate tenure (years since issue).

    Returns (score, details_dict).
    """
    row = conn.execute(
        "SELECT certificate_issue_date FROM operators WHERE id = ?",
        (operator_id,),
    ).fetchone()

    if not row or not row[0]:
        return 50.0, {"tenure_years": None}

    try:
        issue_date = date.fromisoformat(row[0]) if isinstance(row[0], str) else row[0]
        tenure_years = (date.today() - issue_date).days / 365.25
    except (ValueError, TypeError):
        return 50.0, {"tenure_years": None}

    score = score_from_breakpoints(tenure_years, _CERT_TENURE_BREAKPOINTS)
    details = {"tenure_years": round(tenure_years, 1), "issue_date": str(issue_date)}
    return score, details


def _score_operator_ad_compliance(conn, operator_id: int, fleet_size: int) -> tuple[float, dict]:
    """Score AD compliance burden for an operator's fleet.

    Counts applicable ADs for each aircraft type in the fleet and computes
    a burden ratio (ADs per aircraft).
    """
    # Get distinct type designators in fleet
    rows = conn.execute(
        """
        SELECT DISTINCT a.icao_type_designator
        FROM operator_fleet of_
        JOIN aircraft a ON of_.aircraft_id = a.id
        WHERE of_.operator_id = ? AND of_.is_active = 1
              AND a.icao_type_designator IS NOT NULL
        """,
        (operator_id,),
    ).fetchall()

    type_designators = [r[0] for r in rows if r[0]]

    if not type_designators or fleet_size == 0:
        return 90.0, {"ad_count": 0, "fleet_size": fleet_size, "burden_ratio": 0}

    # Count ADs matching these type designators
    total_ads = 0
    for td in type_designators:
        row = conn.execute(
            """
            SELECT COUNT(*) FROM airworthiness_directives
            WHERE applicable_type_designators LIKE ?
                  AND is_superseded = 0
            """,
            (f"%{td}%",),
        ).fetchone()
        total_ads += row[0] if row else 0

    burden_ratio = total_ads / max(fleet_size, 1)
    score = score_from_breakpoints(burden_ratio, _AD_BURDEN_BREAKPOINTS)
    details = {
        "ad_count": total_ads,
        "fleet_size": fleet_size,
        "type_designators": type_designators,
        "burden_ratio": round(burden_ratio, 2),
    }
    return score, details


def compute_operator_scores(db_path: str):
    """Compute safety scores for all active operators and store in safety_scores.

    Each operator is scored across six dimensions: accident history,
    enforcement history, SDR frequency, fleet age, certificate tenure,
    and AD compliance. The weighted composite score is stored along with
    individual component scores.
    """
    started_at = now_utc()
    conn = get_db_connection(db_path)
    now = now_utc()
    today = date.today().isoformat()
    inserted = errored = 0

    try:
        operators = conn.execute(
            "SELECT id, holder_name, certificate_status FROM operators WHERE certificate_status = 'active'"
        ).fetchall()

        logger.info(f"Computing safety scores for {len(operators)} active operators")

        for op in operators:
            op_id, holder_name, _ = op

            try:
                # Get fleet size
                fleet_row = conn.execute(
                    "SELECT COUNT(*) FROM operator_fleet WHERE operator_id = ? AND is_active = 1",
                    (op_id,),
                ).fetchone()
                fleet_size = fleet_row[0] if fleet_row else 0

                # Compute each component
                accident_score, accident_details = _score_operator_accidents(conn, op_id, fleet_size)
                enforcement_score, enforcement_details = _score_operator_enforcement(conn, op_id)
                sdr_score, sdr_details = _score_operator_sdrs(conn, op_id, fleet_size)
                fleet_age_score, fleet_age_details = _score_operator_fleet_age(conn, op_id)
                cert_tenure_score, cert_tenure_details = _score_operator_cert_tenure(conn, op_id)
                ad_score, ad_details = _score_operator_ad_compliance(conn, op_id, fleet_size)

                # Weighted composite
                overall = (
                    accident_score * _OP_ACCIDENT_WEIGHT
                    + enforcement_score * _OP_ENFORCEMENT_WEIGHT
                    + sdr_score * _OP_SDR_WEIGHT
                    + fleet_age_score * _OP_FLEET_AGE_WEIGHT
                    + cert_tenure_score * _OP_CERT_TENURE_WEIGHT
                    + ad_score * _OP_AD_COMPLIANCE_WEIGHT
                )

                component_details = json.dumps({
                    "accident": accident_details,
                    "enforcement": enforcement_details,
                    "sdr": sdr_details,
                    "fleet_age": fleet_age_details,
                    "cert_tenure": cert_tenure_details,
                    "ad_compliance": ad_details,
                })

                # Upsert into safety_scores
                conn.execute(
                    """
                    INSERT INTO safety_scores (
                        entity_type, entity_id, entity_name, overall_score,
                        accident_score, sdr_score, enforcement_score,
                        fleet_age_score, certificate_tenure_score, ad_compliance_score,
                        component_details, calculation_date, methodology_version,
                        source, ingested_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                        entity_name = excluded.entity_name,
                        overall_score = excluded.overall_score,
                        accident_score = excluded.accident_score,
                        sdr_score = excluded.sdr_score,
                        enforcement_score = excluded.enforcement_score,
                        fleet_age_score = excluded.fleet_age_score,
                        certificate_tenure_score = excluded.certificate_tenure_score,
                        ad_compliance_score = excluded.ad_compliance_score,
                        component_details = excluded.component_details,
                        calculation_date = excluded.calculation_date,
                        methodology_version = excluded.methodology_version,
                        source = excluded.source,
                        ingested_at = excluded.ingested_at
                    """,
                    (
                        "operator", op_id, holder_name,
                        round(overall, 2),
                        round(accident_score, 2),
                        round(sdr_score, 2),
                        round(enforcement_score, 2),
                        round(fleet_age_score, 2),
                        round(cert_tenure_score, 2),
                        round(ad_score, 2),
                        component_details,
                        today,
                        METHODOLOGY_VERSION,
                        SOURCE,
                        now,
                    ),
                )
                inserted += 1

            except Exception as e:
                errored += 1
                logger.warning(f"Error scoring operator {op_id} ({holder_name}): {e}")

        conn.commit()
        logger.info(f"Operator scoring complete: {inserted} scored, {errored} errors")

        log_ingestion(
            conn,
            module="safety_scores",
            source="operator_scoring",
            started_at=started_at,
            records_processed=len(operators),
            records_inserted=inserted,
            records_updated=0,
            records_errored=errored,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Operator scoring failed: {e}")
        log_ingestion(
            conn,
            module="safety_scores",
            source="operator_scoring",
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


# ---------------------------------------------------------------------------
# Aircraft scoring implementation
# ---------------------------------------------------------------------------


def _score_aircraft_accidents(conn, aircraft_id: int, n_number: str) -> tuple[float, dict]:
    """Score an aircraft's accident history (no time decay for airframes).

    Returns (score, details_dict).
    """
    rows = conn.execute(
        """
        SELECT highest_injury
        FROM ntsb_accidents
        WHERE aircraft_id = ? OR n_number = ?
        """,
        (aircraft_id, n_number),
    ).fetchall()

    total_penalty = 0.0
    counts = {"fatal": 0, "serious": 0, "minor": 0, "incident": 0}

    for row in rows:
        injury = row[0] or "None"
        penalty = _AC_ACCIDENT_PENALTIES.get(injury, -10)
        total_penalty += penalty

        if injury == "Fatal":
            counts["fatal"] += 1
        elif injury == "Serious":
            counts["serious"] += 1
        elif injury == "Minor":
            counts["minor"] += 1
        else:
            counts["incident"] += 1

    score = max(0.0, min(100.0, 100.0 + total_penalty))
    details = {"total_events": len(rows), "counts": counts, "raw_penalty": total_penalty}
    return score, details


def _score_aircraft_sdrs(conn, aircraft_id: int) -> tuple[float, dict]:
    """Score an aircraft based on its SDR count.

    Returns (score, details_dict).
    """
    row = conn.execute(
        "SELECT COUNT(*) FROM faa_sdrs WHERE aircraft_id = ?",
        (aircraft_id,),
    ).fetchone()

    sdr_count = row[0] if row else 0
    score = score_from_breakpoints(sdr_count, _AC_SDR_BREAKPOINTS)
    details = {"sdr_count": sdr_count}
    return score, details


def _score_aircraft_age(year_mfr: int | None) -> tuple[float, dict]:
    """Score an aircraft based on its manufacturing year.

    Returns (score, details_dict).
    """
    if not year_mfr or year_mfr < 1900:
        return 70.0, {"age": None, "year_mfr": year_mfr}

    age = date.today().year - year_mfr
    score = score_from_breakpoints(age, _FLEET_AGE_BREAKPOINTS)
    details = {"age": age, "year_mfr": year_mfr}
    return score, details


def _score_aircraft_ad_exposure(conn, icao_type: str | None) -> tuple[float, dict]:
    """Score AD exposure for an aircraft based on its type designator.

    Returns (score, details_dict).
    """
    if not icao_type:
        return 90.0, {"ad_count": 0, "type_designator": icao_type}

    row = conn.execute(
        """
        SELECT COUNT(*) FROM airworthiness_directives
        WHERE applicable_type_designators LIKE ?
              AND is_superseded = 0
        """,
        (f"%{icao_type}%",),
    ).fetchone()

    ad_count = row[0] if row else 0
    # Use AD burden breakpoints directly against count
    score = score_from_breakpoints(ad_count, _AD_BURDEN_BREAKPOINTS)
    details = {"ad_count": ad_count, "type_designator": icao_type}
    return score, details


def _score_aircraft_operator(conn, aircraft_id: int) -> tuple[float, dict]:
    """Look up the operator safety score for the aircraft's operator.

    Returns (score, details_dict).
    """
    # Find operator via operator_fleet
    row = conn.execute(
        """
        SELECT of_.operator_id, ss.overall_score, o.holder_name
        FROM operator_fleet of_
        LEFT JOIN safety_scores ss ON ss.entity_type = 'operator' AND ss.entity_id = of_.operator_id
        LEFT JOIN operators o ON o.id = of_.operator_id
        WHERE of_.aircraft_id = ? AND of_.is_active = 1
        LIMIT 1
        """,
        (aircraft_id,),
    ).fetchone()

    if row and row[1] is not None:
        return row[1], {"operator_id": row[0], "operator_name": row[2], "operator_score": row[1]}

    return 75.0, {"operator_id": row[0] if row else None, "operator_name": None, "operator_score": None}


def _score_aircraft_ownership_stability(conn, n_number: str) -> tuple[float, dict]:
    """Score ownership stability based on tail_history events in the last 10 years.

    Returns (score, details_dict).
    """
    ten_years_ago = (date.today() - timedelta(days=3650)).isoformat()

    row = conn.execute(
        """
        SELECT COUNT(*) FROM tail_history
        WHERE n_number = ? AND event_date >= ?
        """,
        (n_number, ten_years_ago),
    ).fetchone()

    event_count = row[0] if row else 0
    score = score_from_breakpoints(event_count, _OWNERSHIP_BREAKPOINTS)
    details = {"registration_events": event_count}
    return score, details


def compute_aircraft_scores(db_path: str):
    """Compute safety scores for all Valid-registration aircraft.

    Processes aircraft in batches of 5000 with progress logging to handle
    the potentially large dataset (~310K aircraft).
    """
    started_at = now_utc()
    conn = get_db_connection(db_path)
    now = now_utc()
    today = date.today().isoformat()
    inserted = errored = 0
    batch_size = 5000

    try:
        # Count total aircraft
        count_row = conn.execute(
            "SELECT COUNT(*) FROM aircraft WHERE registration_status = 'Valid'"
        ).fetchone()
        total_aircraft = count_row[0] if count_row else 0
        logger.info(f"Computing safety scores for {total_aircraft} Valid aircraft")

        if total_aircraft == 0:
            logger.info("No Valid aircraft found, skipping aircraft scoring")
            log_ingestion(
                conn,
                module="safety_scores",
                source="aircraft_scoring",
                started_at=started_at,
                records_processed=0,
                records_inserted=0,
                records_updated=0,
                records_errored=0,
                status="completed",
            )
            return

        # Process in batches using LIMIT/OFFSET
        offset = 0
        batch_num = 0

        while offset < total_aircraft:
            batch_num += 1
            aircraft_batch = conn.execute(
                """
                SELECT id, n_number, year_mfr, icao_type_designator, manufacturer, model
                FROM aircraft
                WHERE registration_status = 'Valid'
                ORDER BY id
                LIMIT ? OFFSET ?
                """,
                (batch_size, offset),
            ).fetchall()

            if not aircraft_batch:
                break

            for ac in aircraft_batch:
                ac_id, n_number, year_mfr, icao_type, manufacturer, model = ac
                entity_name = f"{manufacturer or ''} {model or ''} (N{n_number or ''})".strip()

                try:
                    accident_score, accident_details = _score_aircraft_accidents(conn, ac_id, n_number)
                    sdr_score, sdr_details = _score_aircraft_sdrs(conn, ac_id)
                    age_score, age_details = _score_aircraft_age(year_mfr)
                    ad_score, ad_details = _score_aircraft_ad_exposure(conn, icao_type)
                    operator_score, operator_details = _score_aircraft_operator(conn, ac_id)
                    ownership_score, ownership_details = _score_aircraft_ownership_stability(conn, n_number)

                    overall = (
                        accident_score * _AC_ACCIDENT_WEIGHT
                        + sdr_score * _AC_SDR_WEIGHT
                        + age_score * _AC_AGE_WEIGHT
                        + ad_score * _AC_AD_WEIGHT
                        + operator_score * _AC_OPERATOR_WEIGHT
                        + ownership_score * _AC_OWNERSHIP_WEIGHT
                    )

                    component_details = json.dumps({
                        "accident": accident_details,
                        "sdr": sdr_details,
                        "age": age_details,
                        "ad_exposure": ad_details,
                        "operator": operator_details,
                        "ownership_stability": ownership_details,
                    })

                    conn.execute(
                        """
                        INSERT INTO safety_scores (
                            entity_type, entity_id, entity_name, overall_score,
                            accident_score, sdr_score, enforcement_score,
                            fleet_age_score, certificate_tenure_score, ad_compliance_score,
                            component_details, calculation_date, methodology_version,
                            source, ingested_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                            entity_name = excluded.entity_name,
                            overall_score = excluded.overall_score,
                            accident_score = excluded.accident_score,
                            sdr_score = excluded.sdr_score,
                            enforcement_score = excluded.enforcement_score,
                            fleet_age_score = excluded.fleet_age_score,
                            certificate_tenure_score = excluded.certificate_tenure_score,
                            ad_compliance_score = excluded.ad_compliance_score,
                            component_details = excluded.component_details,
                            calculation_date = excluded.calculation_date,
                            methodology_version = excluded.methodology_version,
                            source = excluded.source,
                            ingested_at = excluded.ingested_at
                        """,
                        (
                            "aircraft", ac_id, entity_name,
                            round(overall, 2),
                            round(accident_score, 2),
                            round(sdr_score, 2),
                            None,  # enforcement_score not applicable for aircraft
                            round(age_score, 2),
                            None,  # certificate_tenure_score not applicable for aircraft
                            round(ad_score, 2),
                            component_details,
                            today,
                            METHODOLOGY_VERSION,
                            SOURCE,
                            now,
                        ),
                    )
                    inserted += 1

                except Exception as e:
                    errored += 1
                    logger.warning(f"Error scoring aircraft {ac_id} (N{n_number}): {e}")

            # Commit batch
            conn.commit()
            processed_so_far = offset + len(aircraft_batch)
            logger.info(
                f"Aircraft scoring batch {batch_num}: "
                f"{processed_so_far}/{total_aircraft} processed "
                f"({inserted} scored, {errored} errors)"
            )
            offset += batch_size

        logger.info(f"Aircraft scoring complete: {inserted} scored, {errored} errors")

        log_ingestion(
            conn,
            module="safety_scores",
            source="aircraft_scoring",
            started_at=started_at,
            records_processed=total_aircraft,
            records_inserted=inserted,
            records_updated=0,
            records_errored=errored,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Aircraft scoring failed: {e}")
        log_ingestion(
            conn,
            module="safety_scores",
            source="aircraft_scoring",
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


def run_safety_scores_etl(db_path: str):
    """Run the full safety scoring pipeline.

    Computes operator scores first (since aircraft scoring may reference them),
    then computes aircraft scores.
    """
    logger.info("Starting safety scores ETL")
    compute_operator_scores(db_path)
    compute_aircraft_scores(db_path)
    logger.info("Safety scores ETL completed.")


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    db = sys.argv[1] if len(sys.argv) > 1 else "fleetpulse.db"
    run_safety_scores_etl(db)
