# Smart Video Cropping for ADTV Traffic Module

## Overview

The ADTV Traffic module now uses **AI-powered smart cropping** when converting videos to different aspect ratios for various social media platforms. Instead of simply cropping to the center (which often cuts off important subjects), the system intelligently detects and focuses on the most important parts of your video.

## How It Works

### Before (Center Cropping)
- 🎯 Always crops to the exact center
- ❌ Often cuts off faces or important subjects
- ❌ Loses context when converting landscape to portrait

### After (Smart Cropping) 
- 🧠 AI detects faces, subjects, and points of interest
- ✅ Keeps important content in frame
- ✅ Adapts cropping based on content and target aspect ratio

## Automatic Aspect Ratio Optimization

The system automatically applies different AI strategies based on the target aspect ratio:

| Aspect Ratio | Platform Use | AI Strategy |
|-------------|--------------|-------------|
| **9:16** (Vertical) | TikTok, Instagram Reels/Stories | `auto:subject` - Focuses on main subject/object |
| **1:1** (Square) | Instagram/Facebook Feed | `auto:faces` - Prioritizes faces, falls back to auto |
| **16:9** (Horizontal) | Facebook Desktop, YouTube | `auto` - Detects most interesting areas |

## Cloudinary AI Gravity Options

The system uses Cloudinary's advanced gravity detection:

- **`auto`** - Automatically detects the most interesting part of the frame
- **`auto:faces`** - Focuses on faces with automatic fallback if no faces detected
- **`auto:subject`** - Identifies and focuses on the main subject/object
- **`auto:subject_face`** - Combines subject and face detection for optimal results
- **`face`** - Strictly focuses on faces (no fallback)
- **`faces`** - Optimizes for multiple faces in frame

## Examples

### Converting Landscape to Portrait (9:16)
- **Old Way**: Crops center 9:16 section, often missing the subject
- **Smart Way**: AI tracks the main subject throughout the video

### Converting to Square (1:1)
- **Old Way**: Takes center square, may cut off people on sides
- **Smart Way**: Ensures all faces remain in frame when possible

## Configuration

### Default Behavior
The system automatically uses smart cropping - no configuration needed!

### Testing Different Strategies
You can override the gravity setting for testing via environment variable:

```bash
# In your Render environment or .env file
CLOUDINARY_GRAVITY_OVERRIDE=auto:subject_face
```

### Available Override Options
- `auto` - General smart detection
- `auto:faces` - Face priority
- `auto:subject` - Subject priority  
- `auto:subject_face` - Combined detection
- `center` - Revert to old center cropping
- `north`, `south`, `east`, `west` - Directional cropping

## Performance Notes

- Smart cropping is processed by Cloudinary's servers, not locally
- No performance impact on your application
- Processing happens on-demand when videos are accessed
- Results are cached for subsequent views

## Troubleshooting

### Video still seems centered?
1. Ensure you've deployed the latest code
2. Check Cloudinary dashboard to confirm AI add-ons are enabled
3. Try a video with clear faces or subjects for best results

### Want to revert to center cropping?
Set the environment variable:
```bash
CLOUDINARY_GRAVITY_OVERRIDE=center
```

## Benefits

1. **Better Engagement** - Videos keep important content in frame
2. **Professional Results** - No more awkwardly cropped videos
3. **Time Saving** - No manual adjustment needed
4. **Platform Optimized** - Each platform gets ideal cropping

## Technical Implementation

The smart cropping is implemented in:
- `backend/ad_traffic/video_processor_cloudinary.py`
- Function: `get_smart_gravity(aspect_ratio)`
- Applied during platform version generation

This feature works automatically for all new campaigns and video processing! 