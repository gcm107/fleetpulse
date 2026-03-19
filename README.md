# FleetPulse

**Private aviation intelligence platform** built entirely on free, open-source data. Look up any of 310,000+ FAA-registered aircraft, screen against OFAC sanctions, compute safety scores, and track flights -- all in one professional-grade tool.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React_18-61DAFB?style=flat&logo=react&logoColor=black)
![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=flat&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Tailwind](https://img.shields.io/badge/TailwindCSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white)

<!-- Screenshots: replace these with actual screenshots -->
<!-- ![Dashboard](screenshots/dashboard.png) -->
<!-- ![Aircraft Detail](screenshots/aircraft-detail.png) -->
<!-- ![Safety Scoring](screenshots/safety-scoring.png) -->
<!-- ![Sanctions Screening](screenshots/sanctions.png) -->

---

## What It Does

| Module | Description | Data Scale |
|--------|-------------|------------|
| **Aircraft Registry** | FAA N-number lookup with full registration details, ownership, engine type, transponder hex | 310,000+ aircraft |
| **Airport Intelligence** | ICAO/IATA lookup with runways, frequencies, live METAR/TAF weather | 84,000+ airports |
| **Safety Scoring** | Derived 0-100 scores using NTSB accidents, enforcement actions, fleet age, AD exposure | 305,000+ scored |
| **Sanctions Screening** | OFAC SDN cross-reference with confidence scoring and alert dashboard | Automated matching |
| **Flight Tracking** | Real-time positions via OpenSky ADS-B, dark map with aircraft markers | Live tracking |
| **Tail Number History** | Registration timeline showing re-registrations, deregistrations, exports | 382,000+ events |
| **Unified Search** | Single search bar across aircraft and airports | Instant results |

## Tech Stack

**Backend:** Python 3.11 / FastAPI / SQLAlchemy / SQLite (PostgreSQL-ready)
**Frontend:** React 18 / Vite / TailwindCSS / Leaflet / Recharts
**Data Sources:** FAA Aircraft Registry, OurAirports, NTSB, NOAA Aviation Weather, OFAC SDN, OpenSky Network
**API:** 33 REST endpoints with OpenAPI docs at `/docs`

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/gcm107/fleetpulse.git
cd fleetpulse
cp .env.example .env
docker-compose up --build
```

Open http://localhost:3000

### Manual Setup

```bash
git clone https://github.com/gcm107/fleetpulse.git
cd fleetpulse

# Backend
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt

# Initialize database
python3 -c "from backend.database import engine, Base; from backend.models import *; Base.metadata.create_all(bind=engine)"

# Seed data (airports: ~2 min, aircraft registry: ~5 min)
python3 -m backend.etl.airports
python3 -m backend.etl.faa_registry

# Generate sample safety/sanctions data
python3 -c "
from backend.etl.operators import generate_sample_operators
from backend.etl.ntsb import run_ntsb_etl
from backend.etl.enforcement import run_enforcement_etl
from backend.etl.ofac import generate_sample_ofac_data
from backend.etl.safety_scores import compute_operator_scores
generate_sample_operators('fleetpulse.db')
run_ntsb_etl('fleetpulse.db')
run_enforcement_etl('fleetpulse.db')
generate_sample_ofac_data('fleetpulse.db')
compute_operator_scores('fleetpulse.db')
"

# Start backend
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

## Environment Variables

Copy `.env.example` to `.env`:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLAlchemy database URL | No (defaults to SQLite) |
| `OPENSKY_CLIENT_ID` | OpenSky OAuth2 client ID | No (anonymous access works) |
| `OPENSKY_CLIENT_SECRET` | OpenSky OAuth2 client secret | No |
| `FAA_NOTAM_API_KEY` | FAA NOTAM API key | No |
| `ADMIN_API_KEY` | API key for ETL trigger endpoint | No (open in dev mode) |

## API (33 Endpoints)

```
Search & Stats
  GET  /api/search?q={query}                 Unified search across all entities
  GET  /api/stats                            Database counts and health

Airports
  GET  /api/airports/{code}                  Airport by ICAO/IATA/FAA code
  GET  /api/airports/{code}/weather          Live METAR + TAF
  GET  /api/airports/{code}/notams           Active NOTAMs
  GET  /api/airports/{code}/runways          Runway details

Aircraft
  GET  /api/aircraft/{n_number}              Aircraft by N-number
  GET  /api/aircraft/{n_number}/history      Tail number history
  GET  /api/aircraft/{n_number}/ownership    Ownership chain
  GET  /api/aircraft/{n_number}/safety       Safety score + incidents
  GET  /api/aircraft/{n_number}/sanctions    OFAC screening
  GET  /api/aircraft/{n_number}/track        Recent flights

Operators
  GET  /api/operators?q={name}&state={st}    Search operators
  GET  /api/operators/{cert}/fleet           Fleet list
  GET  /api/operators/{cert}/safety          Safety score
  GET  /api/operators/{cert}/enforcement     Enforcement actions

Safety & Sanctions
  GET  /api/safety/compare?operators=1,2,3   Side-by-side comparison
  GET  /api/sanctions/alerts                 Active OFAC alerts
  GET  /api/sanctions/check/{n_number}       Check specific aircraft

Tracking & Weather
  GET  /api/tracking/live                    All tracked aircraft
  POST /api/tracking/watch                   Add to watchlist
  GET  /api/weather/refresh/{station}        Fetch fresh weather

Admin
  POST /api/etl/trigger/{module}             Trigger data ingestion (auth required)
  GET  /api/etl/status                       ETL job history
```

Full OpenAPI docs available at http://localhost:8000/docs

## Architecture

```
fleetpulse/
  backend/
    main.py            FastAPI app with 33 endpoints
    models/            26 SQLAlchemy ORM models
    routers/           8 route modules (airports, aircraft, operators, safety, sanctions, flights, weather, search)
    services/          Business logic (safety scoring engine, sanctions checker, tracking)
    etl/               10 data ingestion pipelines (FAA, NTSB, OFAC, OpenSky, NOAA)
    schemas/           Pydantic request/response models
  frontend/
    src/
      pages/           11 pages (Dashboard, Airport, Aircraft, Operator, Safety, Sanctions, Tracking, Settings, Search, Browse)
      components/      20+ components (ScoreGauge, FlightMap, SafetyScorecard, DataTable, AccidentList, etc.)
      api/             Axios client with typed endpoint functions
```

## Safety Scoring Methodology

FleetPulse computes a derived 0-100 safety score for operators and aircraft using publicly available data:

**Operator Score** (6 weighted components):
- Accident/Incident History (30%) -- NTSB database, 10-year window, fleet-size normalized
- Enforcement History (20%) -- FAA actions with time decay
- SDR Frequency (15%) -- Service Difficulty Reports vs industry average
- Fleet Age (15%) -- Average manufacture year
- Certificate Tenure (10%) -- Years since certificate issuance
- AD Compliance Posture (10%) -- Airworthiness Directive exposure

**Aircraft Score** (6 weighted components):
- Accident History (25%) -- NTSB events for this airframe
- SDR History (25%) -- Maintenance issue frequency
- Airframe Age (15%)
- AD Exposure (15%)
- Operator Score (10%) -- Inherited from current operator
- Ownership Stability (10%) -- Registration change frequency

Scores are relative, not absolute. See the full methodology in the codebase.

## Data Sources (All Free)

| Source | Data | Update Frequency |
|--------|------|-----------------|
| [FAA Aircraft Registry](https://registry.faa.gov/database/ReleasableAircraft.zip) | 310K+ US aircraft registrations | Daily |
| [OurAirports](https://ourairports.com/data/) | 84K+ global airports with runways | Weekly |
| [NTSB](https://data.ntsb.gov/avdata) | Aviation accident/incident database | Quarterly |
| [OFAC SDN](https://sanctionslistservice.ofac.treas.gov/) | Sanctions screening list | As needed |
| [NOAA AWC](https://aviationweather.gov/api/) | METAR/TAF weather observations | Real-time |
| [OpenSky Network](https://opensky-network.org/) | ADS-B flight tracking | Real-time |

## License

Private repository.
