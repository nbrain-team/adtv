#!/bin/bash
# Minimal build script to work with Render's cached configuration

echo "=== Starting Python dependency installation ==="

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
echo "Installing requirements.txt..."
pip install -r requirements.txt

# Run environment test
echo "Testing Python environment..."
python test_env.py

# Run database migrations
echo "Running database migrations..."
python scripts/add_agent_website_column.py || echo "Agent website column already exists or migration failed"
python scripts/add_step2_fields.py || echo "Step 2 fields already exist or migration failed"
python scripts/create_campaign_tables.py || echo "Campaign tables already exist or migration failed"

# Setup Playwright browsers

echo "=== Build completed successfully ===" 