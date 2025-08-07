# Agreement System Troubleshooting Guide

## Common Issue: "Agreement Not Found" Error

### Problem
When clicking an agreement link, you get "Agreement Not Found" error.

### Causes
1. The `agreements` table doesn't exist in the database
2. The agreement wasn't saved properly due to a transaction rollback
3. The agreement ID is incorrect

### Solution Steps

## Step 1: Check if Agreements Table Exists

Connect to your Render service shell and run:

```bash
cd backend
python scripts/check_agreements_table.py
```

This will show:
- If the agreements table exists
- How many agreements are in the database
- Recent agreements
- Whether the specific agreement ID exists

## Step 2: Create Agreements Table (if missing)

If the table doesn't exist:

```bash
cd backend
python scripts/create_agreements_table.py
```

This will create the agreements table with all required columns.

## Step 3: Check Agreement Fields on Contacts

Ensure the contact tracking fields exist:

```bash
cd backend
python scripts/ensure_agreement_fields.py
```

## Step 4: Re-send Agreements

After fixing the table issues:
1. Go back to the RSVP tab in your campaign
2. Select the contacts again
3. Click "Send Agreement" 
4. The new agreements should be created properly

## Understanding the Fix

### What Was Changed:
1. **Immediate Commit**: Agreements are now committed to the database immediately after creation, not at the end of processing all contacts
2. **Better Error Handling**: If one contact fails, it doesn't affect others
3. **URL Accessibility**: Agreement URLs work even if email sending fails

### How It Works Now:
```python
# 1. Create agreement
agreement = Agreement(...)
db.add(agreement)
db.flush()  # Get ID

# 2. Save immediately
db.commit()  # Agreement is now in database!

# 3. Generate URL (will work immediately)
agreement_url = f"{base_url}/agreement/{agreement.id}"

# 4. Try to send email (optional)
# Even if this fails, the agreement URL still works
```

## Manual Database Check

To check directly in the database via Render:

```sql
-- Connect to database
psql $DATABASE_URL

-- Check if table exists
\dt agreements

-- Count agreements
SELECT COUNT(*) FROM agreements;

-- Find specific agreement
SELECT * FROM agreements WHERE id = '0e0a939b-552e-4e98-8bfc-dec035772ed5';

-- Show recent agreements
SELECT id, contact_name, status, created_at 
FROM agreements 
ORDER BY created_at DESC 
LIMIT 10;
```

## Prevention

To prevent this in the future:
1. Always check the backend logs when sending agreements
2. Look for the printed agreement URLs in the logs
3. If an error occurs, check the database before retrying

## Emergency Recovery

If an agreement ID is in the contacts table but not in agreements table:

1. The agreement needs to be recreated
2. Simply re-send the agreement to that contact
3. The new agreement ID will be updated in the contact record 