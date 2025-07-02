#!/bin/bash

# Set environment variables for Chrome and ChromeDriver
export CHROME_BIN=/usr/bin/google-chrome
export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Set Playwright browsers path
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.playwright

# Log the paths for debugging
echo "=== Chrome/ChromeDriver Debug Info ==="
echo "Chrome binary at: $CHROME_BIN"
echo "ChromeDriver at: $CHROMEDRIVER_PATH"
echo "Playwright browsers at: $PLAYWRIGHT_BROWSERS_PATH"

# Check if they exist
if [ -f "$CHROME_BIN" ]; then
    echo "Chrome found!"
    $CHROME_BIN --version
else
    echo "WARNING: Chrome not found at $CHROME_BIN"
    # Try to find Chrome
    echo "Searching for Chrome..."
    which google-chrome || which google-chrome-stable || which chromium || which chromium-browser || echo "No Chrome found in PATH"
fi

if [ -f "$CHROMEDRIVER_PATH" ]; then
    echo "ChromeDriver found!"
    $CHROMEDRIVER_PATH --version
else
    echo "WARNING: ChromeDriver not found at $CHROMEDRIVER_PATH"
    # Try to find ChromeDriver
    echo "Searching for ChromeDriver..."
    which chromedriver || echo "No ChromeDriver found in PATH"
    
    # List what's in common locations
    echo "Checking /usr/local/bin:"
    ls -la /usr/local/bin/ | grep -i chrome || echo "No chrome-related files in /usr/local/bin"
    
    echo "Checking /usr/bin:"
    ls -la /usr/bin/ | grep -i chrome || echo "No chrome-related files in /usr/bin"
fi

# Check Playwright installation
echo "=== Playwright Debug Info ==="
python -c "import playwright; print(f'Playwright version: {playwright.__version__}')" || echo "Playwright not installed"
echo "Playwright browsers location:"
ls -la $PLAYWRIGHT_BROWSERS_PATH 2>/dev/null || echo "No Playwright cache found at $PLAYWRIGHT_BROWSERS_PATH"

# Check if Playwright browsers are installed in default location too
echo "Checking default Playwright location:"
ls -la ~/.cache/ms-playwright/ 2>/dev/null || echo "No Playwright cache in default location"

echo "=== Starting Application ==="

# Start the application
uvicorn main:app --host 0.0.0.0 --port $PORT 