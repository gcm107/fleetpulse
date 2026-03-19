#!/bin/bash
set -e
echo "🛩️  Seeding demo data..."
source venv/bin/activate 2>/dev/null || true
python -c "
from backend.etl.airports import run_airport_etl
import os
db_path = 'fleetpulse.db'
print('Ingesting airports from OurAirports...')
run_airport_etl(db_path)
print('Demo data seeded!')
"
