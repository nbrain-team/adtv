-- Fix PostStatus enum case issues
-- This updates all existing posts with uppercase status to use lowercase

-- First, show current status distribution
SELECT status, COUNT(*) as count 
FROM social_posts 
GROUP BY status;

-- Update any posts using uppercase status values to lowercase
UPDATE social_posts 
SET status = 'draft' 
WHERE status = 'DRAFT';

UPDATE social_posts 
SET status = 'scheduled' 
WHERE status = 'SCHEDULED';

UPDATE social_posts 
SET status = 'published' 
WHERE status = 'PUBLISHED';

UPDATE social_posts 
SET status = 'failed' 
WHERE status = 'FAILED';

-- Show updated distribution
SELECT status, COUNT(*) as count 
FROM social_posts 
GROUP BY status; 