# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python backend + serve frontend static files
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy seed script
COPY scripts/seed_on_start.py ./scripts/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./static/

# Create data directory
RUN mkdir -p /app/data

ENV DATABASE_URL=sqlite:////app/data/fleetpulse.db

EXPOSE 8000

CMD ["sh", "-c", "python scripts/seed_on_start.py && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
