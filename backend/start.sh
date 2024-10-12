#!/bin/sh

# Run migrations
alembic upgrade head

# Start the application
uvicorn src.main:backend_app --reload --workers 4 --host 0.0.0.0 --port 8000
