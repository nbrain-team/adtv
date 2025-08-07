# Cloudinary Video Editor Setup

## Frontend Configuration

Add this to your frontend `.env` file:
```
REACT_APP_CLOUDINARY_CLOUD_NAME=your-cloud-name
```

## Backend Configuration  

Your backend `.env` already has:
```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## Get Your Cloudinary Credentials

1. Sign up for free at https://cloudinary.com
2. Go to Dashboard
3. Find your Cloud Name, API Key, and API Secret
4. Add them to both frontend and backend `.env` files

## Where Edit Video Button Appears

1. **In Post Modal** - When editing any post with video content
2. **In Campaign Clips** - Direct edit button on each generated clip
3. **For Any Video** - Works with both campaign clips and manually uploaded videos

## Important Notes

- The editor works with videos already uploaded to Cloudinary
- All edits are non-destructive (original video unchanged)
- Transformations are applied via URL parameters (no re-upload needed)
- Edited versions can be saved and reused

## Testing

1. Upload a video to a campaign or post
2. Look for the "Edit Video" button
3. Make changes and see instant preview
4. Save to apply transformations 