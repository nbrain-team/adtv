#!/usr/bin/env bash
# exit on error
set -o errexit

# --- Install Python Dependencies ---
pip install -r requirements.txt

echo "Running database setup..."
python db_setup.py
echo "Database setup complete." 