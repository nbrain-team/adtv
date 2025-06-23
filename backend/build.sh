#!/usr/bin/env bash
# exit on error
set -o errexit

# --- Install System Dependencies ---
apt-get update && apt-get install -y ffmpeg

# --- Install Python Dependencies ---
pip install -r requirements.txt

echo "Running database setup..."
python db_setup.py
echo "Database setup complete." 