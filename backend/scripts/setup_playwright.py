#!/usr/bin/env python3
"""
Setup script to install Playwright browsers
Run this after installing playwright package
"""

import subprocess
import sys

def setup_playwright():
    """Install Playwright browsers"""
    try:
        print("Installing Playwright browsers...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("Playwright setup complete!")
    except subprocess.CalledProcessError as e:
        print(f"Error setting up Playwright: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_playwright() 