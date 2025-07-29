# ADTV Traffic Module - Cursor Installation Prompt

## Initial Setup Prompt

```
I need to install the ADTV Traffic module into my existing FastAPI/React application. This module provides video processing, AI-powered social media caption generation, and campaign management features.

The module files are located in: `adtv-traffic-export/`

Please help me:
1. Integrate the backend ad_traffic module into my FastAPI app
2. Set up the required database tables
3. Configure the frontend components
4. Set up environment variables
5. Test the installation

My current tech stack:
- Backend: FastAPI with SQLAlchemy
- Frontend: React with TypeScript
- Database: PostgreSQL
- File storage: Local filesystem

Please analyze the provided files and guide me through the integration step by step.
```

## File References for Cursor

### Backend Files to Analyze:
- `backend/ad_traffic/__init__.py` - Module initialization
- `backend/ad_traffic/api.py` - All API endpoints
- `backend/ad_traffic/models.py` - SQLAlchemy models
- `backend/ad_traffic/schemas.py` - Pydantic schemas
- `backend/ad_traffic/services.py` - Business logic
- `backend/ad_traffic/video_processor.py` - MoviePy processor
- `backend/ad_traffic/video_processor_ffmpeg.py` - FFmpeg processor
- `backend/ad_traffic/video_processor_cloudinary.py` - Cloudinary processor (recommended)
- `backend/core/llm_handler.py` - AI integration (partial - needs generate_text and analyze_image methods)

### Frontend Files to Analyze:
- `frontend/pages/AdTrafficPage.tsx` - Main page component
- `frontend/components/AdTraffic/AdTrafficDashboard.tsx` - Dashboard container
- `frontend/components/AdTraffic/CampaignsList.tsx` - Campaign management
- `frontend/components/AdTraffic/ClientManager.tsx` - Client CRUD operations
- `frontend/components/AdTraffic/PostCalendar.tsx` - Calendar view
- `frontend/components/AdTraffic/PostCard.tsx` - Individual post display
- `frontend/components/AdTraffic/PostModal.tsx` - Post detail/edit modal
- `frontend/components/AdTraffic/VideoUploadWizard.tsx` - Campaign creation workflow

### Documentation:
- `docs/INSTALLATION_GUIDE.md` - Complete installation instructions
- `docs/CURSOR_PROMPT.md` - This file

## Key Integration Points

### 1. Database Models
The module requires these tables:
- `ad_traffic_clients` - Client management
- `campaigns` - Campaign tracking
- `video_clips` - Processed video segments
- `social_posts` - Scheduled social media posts

### 2. API Routes
Mount the router at `/api/ad-traffic`:
```python
from ad_traffic.api import router as ad_traffic_router
app.include_router(ad_traffic_router, prefix="/api/ad-traffic")
```

### 3. Dependencies
Critical Python packages:
- `cloudinary` - Video processing (recommended)
- `ffmpeg-python` - Local video processing
- `moviepy` - Fallback processor
- `langchain-google-genai` - AI captions

### 4. Environment Variables
Required:
- `DATABASE_URL` - PostgreSQL connection
- `GEMINI_API_KEY` - For AI features
- `CLOUDINARY_*` - For video processing (highly recommended)

### 5. File Upload Handling
The module expects:
- `/uploads` static file mount
- `uploads/campaigns/` directory for videos
- Multipart form handling

## Common Customizations

### Adapting to Your Auth System
Replace `user_id` references in:
- `backend/ad_traffic/api.py` - Update `get_current_user` dependency
- `backend/ad_traffic/services.py` - Adjust user filtering

### Styling Integration
The components use:
- Radix UI primitives
- Tailwind CSS classes
- Lucide React icons

Update theme variables in components to match your design system.

### Database Integration
If using different ORM or database:
1. Convert SQLAlchemy models to your ORM
2. Update service layer queries
3. Maintain the same schema structure

## Testing Checklist

1. **Backend API**
   - [ ] Create client via POST `/api/ad-traffic/clients`
   - [ ] Upload video campaign
   - [ ] Check video processing status
   - [ ] Verify calendar endpoints

2. **Frontend Flow**
   - [ ] Access `/ad-traffic` route
   - [ ] Create new client
   - [ ] Upload campaign video
   - [ ] View calendar with generated posts
   - [ ] Edit post content

3. **Video Processing**
   - [ ] Verify FFmpeg installed: `ffmpeg -version`
   - [ ] Test with small video file
   - [ ] Check clip generation
   - [ ] Verify AI captions

## Troubleshooting Tips

1. **Import Errors**
   - Ensure `__init__.py` files exist
   - Check Python path includes backend directory
   - Verify all dependencies installed

2. **Database Errors**
   - Run all CREATE TABLE statements
   - Check foreign key relationships
   - Verify user permissions

3. **Video Processing Issues**
   - Start with Cloudinary if possible
   - Check FFmpeg installation
   - Monitor memory usage
   - Check file permissions

4. **Frontend 404s**
   - Verify API route prefix matches
   - Check CORS configuration
   - Ensure authentication headers

## Success Criteria

The module is successfully installed when:
1. ✅ Can create and manage clients
2. ✅ Video upload creates campaign
3. ✅ Video processes into clips
4. ✅ AI generates contextual captions
5. ✅ Calendar shows scheduled posts
6. ✅ Can edit/delete posts
7. ✅ Progress tracking works during processing

## Additional Context for Cursor

When analyzing these files, pay attention to:
- The video processing fallback chain (Cloudinary → FFmpeg → MoviePy)
- The AI vision analysis for contextual captions
- The calendar scheduling algorithm
- The real-time progress updates
- The campaign state management

The module is designed to be self-contained but requires:
- User authentication system
- File upload handling
- Background task processing
- Static file serving

## Questions to Ask Cursor

1. "Can you analyze my current FastAPI app structure and show me exactly where to integrate the ad_traffic module?"
2. "How should I modify the authentication in the ad_traffic module to work with my existing auth system?"
3. "Can you help me create a migration script for the required database tables?"
4. "How do I integrate the AdTraffic React components with my existing routing?"
5. "Can you help me set up the video processing pipeline with my infrastructure?" 