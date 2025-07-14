#!/bin/bash

echo "Starting build process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
python -m playwright install chromium || echo "Playwright browser installation skipped"

# Run database setup
echo "Running database setup..."
cd /opt/render/project/src/backend
python db_setup.py || echo "Database setup skipped - will run on startup"

# Run any additional migrations
echo "Running database migrations..."
python scripts/add_agent_website_column.py || echo "Migration skipped"
python scripts/add_step2_fields.py || echo "Migration skipped"

echo "Database migrations complete."
echo "Build process completed successfully!" 