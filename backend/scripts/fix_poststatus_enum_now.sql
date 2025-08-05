-- Add missing values to poststatus enum
-- Run this on Render PostgreSQL database

-- First check what values exist
SELECT enumlabel FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'poststatus')
ORDER BY enumsortorder;

-- Add the missing values
ALTER TYPE poststatus ADD VALUE IF NOT EXISTS 'pending_approval';
ALTER TYPE poststatus ADD VALUE IF NOT EXISTS 'approved'; 