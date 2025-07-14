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

echo "=== Build completed successfully ===" 