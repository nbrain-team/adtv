-- Check current status values
SELECT status, COUNT(*) as count 
FROM social_posts 
GROUP BY status
ORDER BY status;

-- Update all lowercase status values to uppercase
UPDATE social_posts 
SET status = 'DRAFT' 
WHERE status = 'draft';

UPDATE social_posts 
SET status = 'SCHEDULED' 
WHERE status = 'scheduled';

UPDATE social_posts 
SET status = 'PENDING_APPROVAL' 
WHERE status = 'pending_approval';

UPDATE social_posts 
SET status = 'APPROVED' 
WHERE status = 'approved';

UPDATE social_posts 
SET status = 'PUBLISHED' 
WHERE status = 'published';

UPDATE social_posts 
SET status = 'FAILED' 
WHERE status = 'failed';

-- Verify the update
SELECT status, COUNT(*) as count 
FROM social_posts 
GROUP BY status
ORDER BY status; 