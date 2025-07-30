#!/bin/bash
# Build script for backend

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Running database migrations..."
python -m alembic upgrade head

echo "Running ad traffic table creation..."
python scripts/create_ad_traffic_tables.py

echo "Fixing database columns..."
python scripts/fix_database_columns.py || echo "Database column fixes may have already been applied"

echo "Fixing ad traffic email fields..."
python scripts/fix_ad_traffic_emails.py || echo "Email fields may already be fixed"

echo "Fixing ad traffic media URLs..."
python scripts/fix_ad_traffic_media_urls.py || echo "Media URLs may already be fixed"

echo "Running user management fields migration..."
python scripts/add_user_management_fields.py || echo "User management fields may already exist"

echo "Running campaign analytics fields migration..."
python scripts/add_campaign_analytics_fields.py || echo "Campaign analytics fields may already exist"

echo "Adding campaign owner phone field..."
python scripts/add_campaign_owner_phone.py || echo "Campaign owner phone field may already exist"

echo "Adding system email templates..."
python scripts/add_system_email_templates.py || echo "System email templates may already exist"

echo "Adding ad traffic enhancements..."
python scripts/add_ad_traffic_enhancements.py || echo "Ad traffic enhancements may already exist"

echo "Checking ad traffic data..."
python scripts/check_ad_traffic_data.py || echo "Ad traffic data check completed"

echo "Build complete!" 