#!/bin/bash

# Set the DATABASE_URL to use the local SQLite database
export DATABASE_URL="sqlite:///$(pwd)/local_test.db"

echo "Starting backend with local database..."
echo "Database: $DATABASE_URL"

# Run the FastAPI app
uvicorn main:app --reload --host 0.0.0.0 --port 8000 