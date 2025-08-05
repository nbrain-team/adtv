-- Check current enum values
SELECT enumlabel FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'poststatus') 
ORDER BY enumsortorder;

-- Add missing uppercase values if they don't exist
ALTER TYPE poststatus ADD VALUE IF NOT EXISTS 'PENDING_APPROVAL';
ALTER TYPE poststatus ADD VALUE IF NOT EXISTS 'APPROVED';

-- Verify the values were added
SELECT enumlabel FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'poststatus') 
ORDER BY enumsortorder; 