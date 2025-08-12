# Facebook Automation - Production Deployment Guide

## Quick Answer: Do You Need to Run Scripts?

**First deployment only**: Yes, run `python scripts/init_production.py` once to create your admin user.

**After that**: No! The platform handles everything automatically.

## Deployment Steps

### 1. Environment Variables
Set these in your hosting platform (Render, Heroku, AWS, etc.):

```bash
# Required
DATABASE_URL=postgresql://user:password@host:port/dbname
SECRET_KEY=your-secret-key-here

# Optional (for production admin user)
ADMIN_EMAIL=your-email@domain.com
ADMIN_PASSWORD=your-secure-password

# Facebook API (when ready to connect real accounts)
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
FACEBOOK_VERIFY_TOKEN=your-webhook-verify-token
```

### 2. First-Time Setup

#### Option A: Using Platform Console (Render, Heroku, etc.)
```bash
# In your platform's shell/console
cd backend
python scripts/init_production.py
```

#### Option B: Using Database Migrations (Professional)
If using Alembic or similar:
```bash
# Run migrations
alembic upgrade head

# Create admin user
python scripts/init_production.py
```

### 3. What Happens Automatically

The platform handles these automatically on startup:
- ✅ Creates all database tables if they don't exist
- ✅ Grants permissions to admin users
- ✅ Validates database connections
- ✅ No manual intervention needed after initial setup

### 4. Production vs Development

| Feature | Development (Local) | Production |
|---------|-------------------|------------|
| Database | SQLite with mock data | PostgreSQL/MySQL, empty |
| Users | Test user (danny@nbrain.ai) | Your admin account |
| Facebook Data | Mock realtor data | Real Facebook connections |
| Init Script | `init_db_and_seed.py` | `init_production.py` |

### 5. Common Deployment Platforms

#### Render.com
```yaml
# render.yaml already configured
# Just set environment variables in dashboard
# Run init script in Shell tab after first deploy
```

#### Heroku
```bash
# Set environment variables
heroku config:set DATABASE_URL=...
heroku config:set ADMIN_EMAIL=...

# Run init script
heroku run python backend/scripts/init_production.py
```

#### AWS/Digital Ocean
```bash
# SSH to server
cd /path/to/app/backend
python scripts/init_production.py
```

### 6. Troubleshooting

**Issue: "No DATABASE_URL found"**
- Solution: Ensure DATABASE_URL environment variable is set in your platform

**Issue: Tables not created**
- Solution: The app creates tables on startup, but you can manually run:
  ```python
  from core.database import engine, Base
  Base.metadata.create_all(bind=engine)
  ```

**Issue: Can't access Facebook Automation**
- Solution: Make sure you logged in with the admin account created by init script

### 7. Post-Deployment Checklist

- [ ] Admin user created successfully
- [ ] Can log in to the platform
- [ ] Facebook Automation module visible
- [ ] "Add New Client" button works
- [ ] Ready to connect real Facebook accounts

### 8. Removing Mock Data (If Migrating)

If you accidentally ran the mock data script in production:
```sql
-- Remove all mock data
DELETE FROM facebook_analytics;
DELETE FROM facebook_ad_campaigns;
DELETE FROM facebook_posts;
DELETE FROM facebook_clients WHERE page_name LIKE '%Mock%';
```

## Summary

1. **First deployment**: Run `init_production.py` once
2. **Subsequent deployments**: Just deploy - no scripts needed
3. **Database tables**: Created automatically on app startup
4. **Mock data**: NOT included in production (start clean)

The platform is designed to be zero-maintenance after initial setup! 