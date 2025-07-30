#!/bin/bash
# Build script for backend

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Running database migrations..."
python -m alembic upgrade head

echo "Running ad traffic table creation..."
python scripts/create_ad_traffic_tables.py

echo "Running user management fields migration..."
python scripts/add_user_management_fields.py || echo "User management fields may already exist"

echo "Running campaign analytics fields migration..."
python scripts/add_campaign_analytics_fields.py || echo "Campaign analytics fields may already exist"

echo "Adding campaign owner phone field..."
python scripts/add_campaign_owner_phone.py || echo "Campaign owner phone field may already exist"

echo "Adding system email templates..."
python scripts/add_system_email_templates.py || echo "System email templates may already exist"

echo "Build complete!" 