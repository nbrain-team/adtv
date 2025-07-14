#!/bin/bash
# Start script for the application

echo "=== Starting ADTV Backend ==="
echo "Port: $PORT"

# Start uvicorn
python -m uvicorn main:app --host 0.0.0.0 --port $PORT 