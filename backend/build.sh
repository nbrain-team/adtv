#!/bin/bash

echo "Starting build process..."

# Install Chrome dependencies
echo "Installing Chrome dependencies..."
apt-get update && apt-get install -y \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    libgbm-dev \
    libxkbcommon-x11-0 \
    libxshmfence1 \
    curl \
    unzip

# Download and install Chrome (for Selenium)
echo "Installing Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
apt-get update && apt-get install -y google-chrome-stable

# Download ChromeDriver
echo "Installing ChromeDriver..."
# Get Chrome version
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1)
echo "Chrome version: $CHROME_VERSION"

# Get ChromeDriver version URL for new Chrome versions
CHROMEDRIVER_VERSION_URL="https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION}"
CHROMEDRIVER_VERSION=$(curl -s "$CHROMEDRIVER_VERSION_URL")

# If that fails, try the old API
if [ -z "$CHROMEDRIVER_VERSION" ]; then
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
fi

echo "ChromeDriver version: $CHROMEDRIVER_VERSION"

# Download matching ChromeDriver - try new URL format first
CHROMEDRIVER_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip"
if ! wget -q --spider "$CHROMEDRIVER_URL"; then
    # Fall back to old URL format
    CHROMEDRIVER_URL="https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
fi

wget -N "$CHROMEDRIVER_URL" -P ~/
if [ -f ~/chromedriver-linux64.zip ]; then
    unzip ~/chromedriver-linux64.zip -d ~/
    mv ~/chromedriver-linux64/chromedriver /usr/local/bin/
    rm -rf ~/chromedriver-linux64.zip ~/chromedriver-linux64
else
    unzip ~/chromedriver_linux64.zip -d ~/
    mv ~/chromedriver /usr/local/bin/
    rm ~/chromedriver_linux64.zip
fi

chmod +x /usr/local/bin/chromedriver

# Set environment variables
export CHROME_BIN=/usr/bin/google-chrome
export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

echo "Chrome binary at: $CHROME_BIN"
echo "ChromeDriver at: $CHROMEDRIVER_PATH"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright and browsers properly
echo "Installing Playwright with browsers..."
# First ensure playwright is installed
pip install playwright

# Set Playwright browsers path to a writable location
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/.playwright

# Install Playwright browsers with all dependencies
python -m playwright install chromium --with-deps
python -m playwright install-deps chromium

# Verify installation
echo "Verifying Playwright installation..."
python -c "from playwright.sync_api import sync_playwright; print('Playwright imported successfully')"

echo "Running database setup..."
python db_setup.py
echo "Database setup complete."

echo "Build process completed successfully!" 