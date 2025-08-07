# Gmail SMTP Setup for Agreement Emails

## Configuration Steps

### 1. Enable 2-Step Verification
1. Go to [Google Account settings](https://myaccount.google.com)
2. Select "Security"
3. Under "Signing in to Google," enable "2-Step Verification"

### 2. Generate App Password
1. After enabling 2-Step Verification, go back to Security settings
2. Select "2-Step Verification"
3. Scroll down and select "App passwords"
4. Select "Mail" as the app
5. Select your device type
6. Click "Generate"
7. Copy the 16-character password that appears

### 3. Set Environment Variables
Add these to your `.env` file in the backend directory:

```bash
# Gmail SMTP Configuration
GMAIL_EMAIL=linda@adtvmedia.com
GMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Your 16-character app password (no spaces)

# Application Base URL (for agreement links)
APP_BASE_URL=https://your-domain.com  # In production
# or
APP_BASE_URL=http://localhost:3000    # For local testing
```

### 4. Test Email Sending
The system will automatically use these credentials when sending agreement emails.

## Security Notes
- **Never commit the `.env` file to git**
- Use App Passwords, not your regular Gmail password
- Consider using a dedicated email account for automated sending
- Monitor the account for any unusual activity

## Troubleshooting

### "Less secure app access" Error
- This is why we use App Passwords instead of regular passwords
- App Passwords bypass this restriction

### Authentication Failed
- Ensure 2-Step Verification is enabled
- Regenerate the App Password if needed
- Check for typos in the password (no spaces)

### Emails Not Sending
- Check Gmail's sending limits (500 emails/day for regular accounts)
- Verify the sender email matches the authenticated account
- Check spam folder for bounced messages

## Email Features
The system sends professional HTML emails with:
- Agreement details
- Direct link to signing page
- Company branding
- Mobile-responsive design 