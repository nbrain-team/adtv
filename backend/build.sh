#!/usr/bin/env bash
# exit on error
set -o errexit

# --- Install Google Chrome for Selenium ---
echo "Installing Google Chrome..."
apt-get update
apt-get install -y wget
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb
echo "Google Chrome installation complete."

# --- Install Python Dependencies ---
pip install -r requirements.txt

echo "Running database setup..."
python db_setup.py
echo "Database setup complete." 