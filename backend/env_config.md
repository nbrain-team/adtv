# Environment Configuration for ADTV Backend

## Required Environment Variables

### Database
```bash
DATABASE_URL=postgresql://username:password@host/database
```

### Application URLs
```bash
# Automatically detected on Render, but can be overridden
APP_BASE_URL=https://adtv-frontend.onrender.com  # Frontend URL for agreement links
```

### Gmail Configuration (for sending agreement emails)
```bash
GMAIL_EMAIL=linda@adtvmedia.com
GMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # 16-character App Password (no spaces)
```

### API Keys
```bash
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...
SERP_API_KEY=...  # For contact enrichment
```

## Render-Specific Variables

Render automatically sets these:
- `RENDER=true` - Indicates the app is running on Render
- `PORT` - The port to bind to
- `RENDER_SERVICE_NAME` - The name of the service

## Production vs Development

The application automatically detects if it's running on Render and adjusts URLs accordingly:

- **Production (Render)**: Uses `https://adtv-frontend.onrender.com`
- **Development (Local)**: Uses `http://localhost:3000` or `APP_BASE_URL` if set

## Setting Environment Variables on Render

1. Go to your Render dashboard
2. Select your backend service
3. Navigate to "Environment" tab
4. Add each variable as a key-value pair
5. Save and deploy

## Gmail Setup

1. Enable 2-Step Verification for linda@adtvmedia.com
2. Generate an App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and generate
   - Copy the 16-character password
3. Add to Render environment variables 