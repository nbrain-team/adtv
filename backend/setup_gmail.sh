#!/bin/bash

echo "============================================"
echo "Gmail SMTP Setup for ADTV Agreement System"
echo "============================================"
echo ""
echo "IMPORTANT: Gmail requires an App Password for SMTP access"
echo ""
echo "Step 1: Enable 2-Step Verification"
echo "--------------------------------"
echo "1. Go to: https://myaccount.google.com/security"
echo "2. Sign in with: linda@adtvmedia.com"
echo "3. Click on '2-Step Verification'"
echo "4. Follow the setup process"
echo ""
echo "Step 2: Generate App Password"
echo "-----------------------------"
echo "1. After enabling 2-Step Verification, go to:"
echo "   https://myaccount.google.com/apppasswords"
echo "2. Select 'Mail' from the dropdown"
echo "3. Select your device type"
echo "4. Click 'Generate'"
echo "5. Copy the 16-character password (looks like: xxxx xxxx xxxx xxxx)"
echo ""
echo "Step 3: Update Environment Variables"
echo "-----------------------------------"
read -p "Enter the 16-character App Password (with or without spaces): " app_password

# Remove spaces from the password
app_password_clean="${app_password// /}"

# Update or create .env file
if [ -f .env ]; then
    # Backup existing .env
    cp .env .env.backup
    echo "Backed up existing .env to .env.backup"
fi

# Write Gmail configuration to .env
cat > .env.gmail << EOF
# Gmail SMTP Configuration
GMAIL_EMAIL=linda@adtvmedia.com
GMAIL_PASSWORD=$app_password_clean

# Application Base URL (update for production)
APP_BASE_URL=http://localhost:3000
EOF

echo ""
echo "Configuration saved to .env.gmail"
echo ""
echo "To use this configuration:"
echo "1. Copy the contents of .env.gmail to your main .env file"
echo "2. Or rename .env.gmail to .env if you don't have other settings"
echo ""
echo "Testing email connection..."

# Simple Python test script
python3 << EOF
import smtplib
import os

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('linda@adtvmedia.com', '$app_password_clean')
    server.quit()
    print("✅ Gmail SMTP connection successful!")
    print("Your agreement emails are ready to send.")
except Exception as e:
    print("❌ Connection failed:", str(e))
    print("Please check your App Password and try again.")
EOF

echo ""
echo "Setup complete!" 