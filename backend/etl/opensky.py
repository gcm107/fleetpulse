"""OpenSky Network ETL - fetches live ADS-B state vectors and ingests flight/position data."""
import json
import logging
import time
from datetime import datetime, timezone

import requests

from backend.config import settings
from backend.etl.base import (
    get_db_connection,
    log_ingestion,
    now_utc,
    safe_float,
    safe_int,
)

logger = logging.getLogger(__name__)

TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
)
STATES_URL = "https://opensky-network.org/api/states/all"
TRACKS_URL = "https://opensky-network.org/api/tracks/all"

SOURCE = "opensky"

# Rate-limit tracking (simple in-memory counters)
_request_count = 0
_request_window_start = 0.0


def get_opensky_token(client_id: str, client_secret: str) -> str:
    """Obtain an OAuth2 access token using client credentials flow.

    Args:
        client_id: OpenSky OAuth2 client ID.
        client_secret: OpenSky OAuth2 client secret.

    Returns:
        Bearer access_token string.

    Raises:
        requests.HTTPError: If the token request fails.
    """
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise ValueError("No access_token in token response")
    logger.info("Obtained OpenSky OAuth2 access token")
    return token


def _check_rate_limit(authenticated: bool):
    """Simple rate-limit guard.  Anonymous: 100/day, Authenticated: 4000/day."""
    global _request_count, _request_window_start

    now = time.time()
    # Reset counter every 24 hours
    if now - _request_window_start > 86400:
        _request_count = 0
        _request_window_start = now

    limit = 4000 if authenticated else 100
    if _request_count >= limit:
        logger.warning(
            "OpenSky rate limit reached (%d/%d). Skipping request.", _request_count, limit
        )
        return False

    _request_count += 1
    return True


def fetch_live_states(token: str | None = None, hex_codes: list[str] | None = None) -> list:
    """Fetch current ADS-B state vectors from OpenSky.

    Args:
        token: Optional OAuth2 Bearer token for authenticated access.
        hex_codes: Optional list of ICAO24 hex codes to filter by.

    Returns:
        List of state-vector lists.  Each state vector has 17 elements:
        [icao24, callsign, origin_country, time_position, last_contact,
         longitude, latitude, baro_altitude, on_ground, velocity,
         true_track, vertical_rate, sensors, geo_altitude, squawk, spi,
         position_source, category]
    """
    authenticated = token is not None
    if not _check_rate_limit(authenticated):
        return []

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {}
    if hex_codes:
        # OpenSky accepts icao24 as a comma-separated list
        params["icao24"] = ",".join(h.lower() for h in hex_codes)

    try:
        resp = requests.get(STATES_URL, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            logger.warning("OpenSky rate-limited (HTTP 429). Backing off.")
            return []
        raise

    data = resp.json()
    states = data.get("states") or []
    logger.info("Fetched %d state vectors from OpenSky", len(states))
    return states


def fetch_aircraft_track(token: str, hex_code: str) -> list[dict]:
    """Fetch recent track waypoints for a single aircraft.

    Args:
        token: OAuth2 Bearer token.
        hex_code: ICAO24 hex identifier.

    Returns:
        List of waypoint dicts with keys: time, latitude, longitude,
        baro_altitude, true_track, on_ground.
    """
    if not _check_rate_limit(authenticated=True):
        return []

    headers = {"Authorization": f"Bearer {token}"}
    params = {"icao24": hex_code.lower(), "time": 0}

    try:
        resp = requests.get(TRACKS_URL, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            logger.info("No track data for %s", hex_code)
            return []
        if e.response is not None and e.response.status_code == 429:
            logger.warning("OpenSky rate-limited (HTTP 429). Backing off.")
            return []
        raise

    data = resp.json()
    path = data.get("path") or []
    waypoints = []
    for wp in path:
        # path element: [time, lat, lon, baro_altitude, true_track, on_ground]
        if len(wp) < 6:
            continue
        waypoints.append({
            "time": wp[0],
            "latitude": wp[1],
            "longitude": wp[2],
            "baro_altitude": wp[3],
            "true_track": wp[4],
            "on_ground": wp[5],
        })
    logger.info("Fetched %d waypoints for %s", len(waypoints), hex_code)
    return waypoints


def ingest_live_positions(db_path: str, states: list) -> dict:
    """Upsert flights and insert positions from OpenSky state vectors.

    For each state vector:
      - Look up aircraft by transponder_hex.
      - Create or update a Flight record (is_live=True).
      - Insert a FlightPosition row.

    Args:
        db_path: Path to the SQLite database.
        states: List of OpenSky state-vector arrays.

    Returns:
        Dict with keys: flights_upserted, positions_inserted, skipped.
    """
    conn = get_db_connection(db_path)
    now = now_utc()
    flights_upserted = 0
    positions_inserted = 0
    skipped = 0

    try:
        for sv in states:
            if len(sv) < 17:
                skipped += 1
                continue

            icao24 = (sv[0] or "").strip().upper()
            callsign = (sv[1] or "").strip() or None
            longitude = safe_float(sv[5])
            latitude = safe_float(sv[6])
            baro_altitude_m = safe_float(sv[7])
            on_ground = bool(sv[8]) if sv[8] is not None else False
            velocity_ms = safe_float(sv[9])
            true_track = safe_float(sv[10])
            vertical_rate_ms = safe_float(sv[11])
            geo_altitude_m = safe_float(sv[13])
            squawk = (sv[14] or "").strip() or None

            if not icao24:
                skipped += 1
                continue

            # Skip if no position data
            if latitude is None or longitude is None:
                skipped += 1
                continue

            # Convert units
            # Altitude: meters -> feet (1 m = 3.28084 ft)
            altitude_ft = safe_int(baro_altitude_m * 3.28084) if baro_altitude_m is not None else None
            geo_altitude_ft = safe_int(geo_altitude_m * 3.28084) if geo_altitude_m is not None else None
            # Velocity: m/s -> knots (1 m/s = 1.94384 kts)
            ground_speed_kts = round(velocity_ms * 1.94384, 1) if velocity_ms is not None else None
            # Vertical rate: m/s -> fpm (1 m/s = 196.85 fpm)
            vertical_rate_fpm = safe_int(vertical_rate_ms * 196.85) if vertical_rate_ms is not None else None

            # Look up aircraft by transponder_hex
            row = conn.execute(
                "SELECT id FROM aircraft WHERE transponder_hex = ?", (icao24,)
            ).fetchone()
            aircraft_id = row[0] if row else None

            # Find or create an active (is_live) flight for this hex code
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            ts_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            existing_flight = conn.execute(
                """SELECT id, first_seen FROM flights
                   WHERE transponder_hex = ? AND is_live = 1 AND flight_date = ?
                   ORDER BY last_seen DESC LIMIT 1""",
                (icao24, today),
            ).fetchone()

            if existing_flight:
                flight_id = existing_flight[0]
                # Update last_seen and callsign
                conn.execute(
                    """UPDATE flights SET last_seen = ?, callsign = COALESCE(?, callsign),
                       squawk = COALESCE(?, squawk)
                       WHERE id = ?""",
                    (ts_now, callsign, squawk, flight_id),
                )
            else:
                # Mark any previous live flights for this hex as no longer live
                conn.execute(
                    "UPDATE flights SET is_live = 0 WHERE transponder_hex = ? AND is_live = 1",
                    (icao24,),
                )
                # Create new flight
                cursor = conn.execute(
                    """INSERT INTO flights (
                        aircraft_id, transponder_hex, callsign,
                        first_seen, last_seen, flight_date,
                        squawk, is_live, source, ingested_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
                    (
                        aircraft_id,
                        icao24,
                        callsign,
                        ts_now,
                        ts_now,
                        today,
                        squawk,
                        SOURCE,
                        now,
                    ),
                )
                flight_id = cursor.lastrowid

            flights_upserted += 1

            # Insert position
            conn.execute(
                """INSERT INTO flight_positions (
                    flight_id, timestamp, latitude, longitude,
                    altitude_ft, geo_altitude_ft, ground_speed_kts,
                    track_deg, vertical_rate_fpm, on_ground, squawk
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    flight_id,
                    ts_now,
                    latitude,
                    longitude,
                    altitude_ft,
                    geo_altitude_ft,
                    ground_speed_kts,
                    true_track,
                    vertical_rate_fpm,
                    1 if on_ground else 0,
                    squawk,
                ),
            )
            positions_inserted += 1

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    result = {
        "flights_upserted": flights_upserted,
        "positions_inserted": positions_inserted,
        "skipped": skipped,
    }
    logger.info("Ingested positions: %s", result)
    return result


def run_opensky_etl(db_path: str):
    """One-shot ETL: fetch state vectors for all watchlist aircraft and ingest.

    If OAuth2 credentials are configured, uses authenticated access (higher rate limits).
    Otherwise, falls back to anonymous access.

    Watchlist is determined by aircraft that have transponder_hex values in the database.
    """
    started_at = now_utc()
    conn = get_db_connection(db_path)

    total_processed = 0
    total_inserted = 0
    total_errored = 0

    try:
        # Get token if credentials configured
        token = None
        client_id = settings.OPENSKY_CLIENT_ID
        client_secret = settings.OPENSKY_CLIENT_SECRET
        if client_id and client_secret:
            try:
                token = get_opensky_token(client_id, client_secret)
            except Exception as e:
                logger.warning("Failed to obtain OpenSky token, falling back to anonymous: %s", e)

        # Get hex codes of aircraft we want to track
        rows = conn.execute(
            "SELECT DISTINCT transponder_hex FROM aircraft WHERE transponder_hex IS NOT NULL LIMIT 100"
        ).fetchall()
        hex_codes = [r[0] for r in rows if r[0]]

        conn.close()
        conn = None

        if not hex_codes:
            logger.info("No aircraft with transponder_hex found. Skipping OpenSky ETL.")
            conn = get_db_connection(db_path)
            log_ingestion(
                conn,
                module="opensky",
                source=SOURCE,
                started_at=started_at,
                records_processed=0,
                status="completed",
                error_message="No aircraft to track",
            )
            return

        # Fetch state vectors (batch by 100 hex codes due to API limits)
        all_states = []
        for i in range(0, len(hex_codes), 100):
            batch = hex_codes[i : i + 100]
            states = fetch_live_states(token=token, hex_codes=batch)
            all_states.extend(states)
            # Brief pause between batches to be polite
            if i + 100 < len(hex_codes):
                time.sleep(1)

        total_processed = len(all_states)

        # Ingest positions
        if all_states:
            result = ingest_live_positions(db_path, all_states)
            total_inserted = result["positions_inserted"]
            total_errored = result["skipped"]
        else:
            logger.info("No live state vectors returned for watched aircraft.")

        conn = get_db_connection(db_path)
        log_ingestion(
            conn,
            module="opensky",
            source=SOURCE,
            started_at=started_at,
            records_processed=total_processed,
            records_inserted=total_inserted,
            records_errored=total_errored,
            status="completed",
        )
        logger.info("OpenSky ETL completed successfully.")

    except Exception as e:
        logger.error("OpenSky ETL failed: %s", e)
        if conn is None:
            conn = get_db_connection(db_path)
        log_ingestion(
            conn,
            module="opensky",
            source=SOURCE,
            started_at=started_at,
            records_processed=total_processed,
            records_inserted=total_inserted,
            records_errored=total_errored,
            status="failed",
            error_message=str(e),
        )
        raise
    finally:
        if conn is not None:
            conn.close()


def main(db_path: str = "fleetpulse.db"):
    """CLI entry point for the OpenSky ETL."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_opensky_etl(db_path)


if __name__ == "__main__":
    import sys

    db = sys.argv[1] if len(sys.argv) > 1 else "fleetpulse.db"
    main(db)
