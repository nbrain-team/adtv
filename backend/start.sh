#!/bin/bash
# Start script for the application

echo "=== Starting ADTV Backend ==="
echo "Port: $PORT"
echo "Python: $(which python)"
echo "Current directory: $(pwd)"

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in $(pwd)"
    echo "Directory contents:"
    ls -la
    exit 1
fi

# Try to import the app to catch any import errors
echo "Testing imports..."
python -c "import main; print('Imports successful')" || {
    echo "ERROR: Failed to import main.py"
    echo "Trying to get more error details..."
    python main.py
    exit 1
}

# Start uvicorn
echo "Starting uvicorn..."
python -m uvicorn main:app --host 0.0.0.0 --port $PORT 