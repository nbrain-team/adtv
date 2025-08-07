# Cloudinary Setup Instructions

## Backend Configuration

In your backend `.env` file (for Render or local development), add:

```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## Frontend Configuration

In your frontend directory, create a `.env` file (or `.env.local`) with:

```
VITE_CLOUDINARY_CLOUD_NAME=your-cloud-name
```

**Note:** For Vite projects, environment variables must be prefixed with `VITE_` to be accessible in the browser.

### Getting Your Cloudinary Cloud Name

1. Log in to your [Cloudinary Dashboard](https://cloudinary.com/console)
2. Your cloud name is displayed at the top of the dashboard
3. It's also visible in any Cloudinary URL: `https://res.cloudinary.com/YOUR-CLOUD-NAME/...`

## Where the Edit Video Button Appears

The "Edit Video" button is now available in two locations:

1. **Post Modal** - When creating or editing a social media post that contains video
2. **Client Detail View** - On each video clip in the "Generated Clips" section

## Features Available

Once configured, the video editor allows:

### Effects
- Fade in/out transitions
- Blur, brightness, contrast, saturation adjustments  
- Playback speed control

### Text Overlays
- Custom text with font, size, color options
- Multiple positioning options
- Optional background for text

### Filters
- Sepia, B&W, Vignette
- Oil Paint, Cartoon, Outline effects
- Artistic filters

### Logo/Watermark
- Add logo or watermark overlay
- Control position, size, and opacity

### Audio
- Volume control
- Mute option
- Background music overlay (requires audio file in Cloudinary)

## Automatic Cloud Name Detection

If the environment variable is not set, the video editor will try to automatically extract the cloud name from the video URL. This provides a fallback but it's recommended to set the environment variable for consistency. 