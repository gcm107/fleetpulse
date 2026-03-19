#!/bin/bash
set -e
echo "🛩️  FleetPulse Setup"
echo "===================="

# Backend setup
echo "Setting up backend..."
cd backend
python3 -m venv ../venv 2>/dev/null || python -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
cd ..
python -c "
from backend.database import engine, Base
from backend.models import *
Base.metadata.create_all(bind=engine)
print('Database initialized successfully.')
"

echo ""
echo "Setup complete! Run the following to start:"
echo "  source venv/bin/activate"
echo "  uvicorn backend.main:app --reload --port 8000"
echo ""
echo "Frontend:"
echo "  cd frontend && npm install && npm run dev"
