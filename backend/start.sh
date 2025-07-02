#!/bin/bash

# Set environment variables for Chrome and ChromeDriver
export CHROME_BIN=/usr/bin/google-chrome
export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Log the paths for debugging
echo "Chrome binary at: $CHROME_BIN"
echo "ChromeDriver at: $CHROMEDRIVER_PATH"

# Check if they exist
if [ -f "$CHROME_BIN" ]; then
    echo "Chrome found!"
else
    echo "WARNING: Chrome not found at $CHROME_BIN"
fi

if [ -f "$CHROMEDRIVER_PATH" ]; then
    echo "ChromeDriver found!"
else
    echo "WARNING: ChromeDriver not found at $CHROMEDRIVER_PATH"
fi

# Start the application
uvicorn main:app --host 0.0.0.0 --port $PORT 