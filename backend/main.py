import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func

from backend.config import settings
from backend.database import SessionLocal, engine, Base
from backend.models import (
    Aircraft,
    Airport,
    EnforcementAction,
    Flight,
    IngestionLog,
    NOTAM,
    NTSBAccident,
    OFACSDN,
    Operator,
    TFR,
)
from backend.routers.aircraft import router as aircraft_router
from backend.routers.airports import router as airports_router
from backend.routers.flights import router as flights_router
from backend.routers.operators import router as operators_router
from backend.routers.safety import router as safety_router
from backend.routers.sanctions import router as sanctions_router
from backend.routers.search import router as search_router
from backend.routers.weather import router as weather_router

app = FastAPI(
    title="FleetPulse API",
    version=settings.APP_VERSION,
    description="Aviation intelligence platform providing comprehensive fleet, safety, and operational data.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(aircraft_router)
app.include_router(airports_router)
app.include_router(flights_router)
app.include_router(operators_router)
app.include_router(safety_router)
app.include_router(sanctions_router)
app.include_router(search_router)
app.include_router(weather_router)


@app.on_event("startup")
def on_startup():
    import backend.models  # noqa: F401 — ensure all models are registered
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Aviation intelligence platform API",
    }


@app.get("/api/stats")
def get_stats():
    db = SessionLocal()
    try:
        stats = {
            "airports": db.query(func.count(Airport.id)).scalar() or 0,
            "aircraft": db.query(func.count(Aircraft.id)).scalar() or 0,
            "operators": db.query(func.count(Operator.id)).scalar() or 0,
            "flights": db.query(func.count(Flight.id)).scalar() or 0,
            "ntsb_accidents": db.query(func.count(NTSBAccident.id)).scalar() or 0,
            "enforcement_actions": db.query(func.count(EnforcementAction.id)).scalar() or 0,
            "notams": db.query(func.count(NOTAM.id)).scalar() or 0,
            "tfrs": db.query(func.count(TFR.id)).scalar() or 0,
            "ofac_sdn": db.query(func.count(OFACSDN.id)).scalar() or 0,
        }
        return stats
    finally:
        db.close()


_admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def require_admin_key(api_key: str = Security(_admin_key_header)):
    """Verify the admin API key for protected endpoints."""
    expected = settings.ADMIN_API_KEY
    if not expected:
        # No key configured — allow access (dev mode)
        return True
    if not api_key or api_key != expected:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key")
    return True


@app.post("/api/etl/trigger/{module}")
def trigger_etl(module: str, _auth: bool = Depends(require_admin_key)):
    """Manually trigger an ETL job. Requires X-Admin-Key header when ADMIN_API_KEY is set."""
    import threading
    db_url = settings.DATABASE_URL
    db_path = db_url.replace("sqlite:///", "").replace("./", "")
    if module == "airports":
        from backend.etl.airports import run_airport_etl
        thread = threading.Thread(target=run_airport_etl, args=(db_path,))
        thread.start()
        return {"status": "started", "module": module}
    elif module == "faa_registry":
        from backend.etl.faa_registry import run_faa_registry_etl
        thread = threading.Thread(target=run_faa_registry_etl, args=(db_path,))
        thread.start()
        return {"status": "started", "module": module}
    elif module == "operators_sample":
        from backend.etl.operators import generate_sample_operators
        thread = threading.Thread(target=generate_sample_operators, args=(db_path,))
        thread.start()
        return {"status": "started", "module": module}
    elif module == "ntsb":
        from backend.etl.ntsb import run_ntsb_etl
        thread = threading.Thread(target=run_ntsb_etl, args=(db_path,))
        thread.start()
        return {"status": "started", "module": module}
    elif module == "enforcement":
        from backend.etl.enforcement import run_enforcement_etl
        thread = threading.Thread(target=run_enforcement_etl, args=(db_path,))
        thread.start()
        return {"status": "started", "module": module}
    elif module == "safety_scores":
        from backend.etl.safety_scores import run_safety_scores_etl
        thread = threading.Thread(target=run_safety_scores_etl, args=(db_path,))
        thread.start()
        return {"status": "started", "module": module}
    elif module == "ofac":
        from backend.etl.ofac import run_ofac_etl
        thread = threading.Thread(target=run_ofac_etl, args=(db_path,))
        thread.start()
        return {"status": "started", "module": module}
    elif module == "ofac_sample":
        from backend.etl.ofac import generate_sample_ofac_data
        thread = threading.Thread(target=generate_sample_ofac_data, args=(db_path,))
        thread.start()
        return {"status": "started", "module": module}
    elif module == "weather":
        from backend.etl.weather import run_weather_etl
        thread = threading.Thread(target=run_weather_etl, args=(db_path,))
        thread.start()
        return {"status": "started", "module": module}
    elif module == "opensky":
        from backend.etl.opensky import run_opensky_etl
        thread = threading.Thread(target=run_opensky_etl, args=(db_path,))
        thread.start()
        return {"status": "started", "module": module}
    return {"status": "error", "message": f"Unknown module: {module}"}


@app.get("/api/etl/status")
def get_etl_status():
    db = SessionLocal()
    try:
        recent_logs = (
            db.query(IngestionLog)
            .order_by(IngestionLog.started_at.desc())
            .limit(20)
            .all()
        )
        return [
            {
                "id": log.id,
                "module": log.module,
                "source": log.source,
                "started_at": str(log.started_at),
                "completed_at": str(log.completed_at) if log.completed_at else None,
                "records_processed": log.records_processed,
                "records_inserted": log.records_inserted,
                "records_updated": log.records_updated,
                "records_errored": log.records_errored,
                "status": log.status,
                "error_message": log.error_message,
                "source_file": log.source_file,
                "source_date": str(log.source_date) if log.source_date else None,
            }
            for log in recent_logs
        ]
    finally:
        db.close()


# Serve frontend static files in production (when built frontend exists at /app/static)
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """Serve the React SPA for any non-API route."""
        file_path = _static_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_static_dir / "index.html"))
