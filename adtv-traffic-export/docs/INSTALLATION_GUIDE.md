# ADTV Traffic Module Installation Guide

## Overview
The ADTV Traffic module is a comprehensive social media campaign management system that:
- Processes long-form videos into 30-second clips
- Analyzes video content using AI vision
- Generates contextual social media captions
- Schedules posts across multiple platforms
- Provides a calendar view for content management

## Architecture

### Backend (FastAPI + SQLAlchemy)
- **API Layer**: RESTful endpoints for campaigns, clients, posts
- **Video Processing**: Multiple processors (Cloudinary preferred, FFmpeg, MoviePy fallback)
- **AI Integration**: Gemini AI for vision analysis and caption generation
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Background Tasks**: Async video processing

### Frontend (React + TypeScript)
- **Dashboard**: Campaign overview and management
- **Calendar View**: Visual post scheduling
- **Upload Workflow**: Step-by-step campaign creation
- **Real-time Updates**: Progress tracking during processing

## Prerequisites

### System Dependencies
```bash
# Ubuntu/Debian
apt-get update
apt-get install -y ffmpeg python3-pip nodejs npm postgresql

# macOS
brew install ffmpeg node postgresql
```

### Environment Variables
Create a `.env` file with:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# AI Services
GEMINI_API_KEY=your_gemini_api_key

# Video Processing (Required for best performance)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Optional: If not using Cloudinary
# FFmpeg will be used as fallback
```

## Backend Installation

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Required packages:
```txt
fastapi==0.115.0
sqlalchemy==2.0.36
pydantic==2.10.3
cloudinary==1.41.0
ffmpeg-python==0.2.0
moviepy==1.0.3
langchain-google-genai==2.0.7
python-multipart==0.0.5
aiofiles==23.2.1
```

### 2. Database Setup

#### Create Tables
Run these SQL commands:
```sql
-- Clients table
CREATE TABLE ad_traffic_clients (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    contact_info TEXT,
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaigns table
CREATE TABLE campaigns (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES ad_traffic_clients(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    original_video_url TEXT,
    platforms TEXT[],
    duration_weeks INTEGER DEFAULT 4,
    status VARCHAR(50) DEFAULT 'PENDING',
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Video clips table
CREATE TABLE video_clips (
    id UUID PRIMARY KEY,
    campaign_id UUID REFERENCES campaigns(id),
    title VARCHAR(255),
    description TEXT,
    duration FLOAT,
    start_time FLOAT,
    end_time FLOAT,
    video_url TEXT,
    thumbnail_url TEXT,
    content_type VARCHAR(50),
    suggested_caption TEXT,
    suggested_hashtags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Social posts table
CREATE TABLE social_posts (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES ad_traffic_clients(id),
    campaign_id UUID REFERENCES campaigns(id),
    video_clip_id UUID REFERENCES video_clips(id),
    content TEXT,
    platforms TEXT[],
    scheduled_time TIMESTAMP,
    published_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'DRAFT',
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_campaigns_client ON campaigns(client_id);
CREATE INDEX idx_clips_campaign ON video_clips(campaign_id);
CREATE INDEX idx_posts_client ON social_posts(client_id);
CREATE INDEX idx_posts_scheduled ON social_posts(scheduled_time);
```

### 3. API Integration

Add to your main FastAPI app:
```python
from ad_traffic.api import router as ad_traffic_router

app.include_router(
    ad_traffic_router,
    prefix="/api/ad-traffic",
    tags=["ad-traffic"]
)
```

### 4. Static Files Setup
Create directories for uploads:
```bash
mkdir -p uploads/campaigns
mkdir -p uploads/clips
mkdir -p uploads/thumbnails
```

Mount static files in FastAPI:
```python
from fastapi.staticfiles import StaticFiles

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```

## Frontend Installation

### 1. Install Dependencies
```bash
npm install @radix-ui/react-* lucide-react date-fns axios
```

### 2. Add Routes
In your React router:
```tsx
import AdTrafficPage from './pages/AdTrafficPage';

<Route path="/ad-traffic" element={<AdTrafficPage />} />
```

### 3. API Configuration
Update your Axios instance to handle the ad-traffic endpoints:
```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
```

## File Structure

```
your-project/
├── backend/
│   ├── ad_traffic/
│   │   ├── __init__.py
│   │   ├── api.py                    # API endpoints
│   │   ├── models.py                 # Database models
│   │   ├── schemas.py                # Pydantic schemas
│   │   ├── services.py               # Business logic
│   │   ├── video_processor.py        # MoviePy processor
│   │   ├── video_processor_ffmpeg.py # FFmpeg processor
│   │   └── video_processor_cloudinary.py # Cloudinary processor
│   └── core/
│       └── llm_handler.py            # AI integration
├── frontend/
│   └── src/
│       ├── components/
│       │   └── AdTraffic/
│       │       ├── AdTrafficDashboard.tsx
│       │       ├── CampaignsList.tsx
│       │       ├── ClientManager.tsx
│       │       ├── PostCalendar.tsx
│       │       ├── PostCard.tsx
│       │       ├── PostModal.tsx
│       │       └── VideoUploadWizard.tsx
│       └── pages/
│           └── AdTrafficPage.tsx
└── uploads/                          # File storage
```

## Configuration

### Video Processing Priority
The system automatically selects processors in this order:
1. **Cloudinary** (if configured) - Cloud-based, most reliable
2. **FFmpeg** (if available) - Local processing, fast
3. **MoviePy** (fallback) - Python-based, slower

### AI Caption Generation
- Extracts frames from video clips
- Analyzes content using Gemini Vision
- Generates contextual captions based on actual content
- Includes relevant hashtags and emojis

## Testing

### 1. Test Video Upload
```bash
curl -X POST http://localhost:8000/api/ad-traffic/check-video-processor
```

### 2. Create Test Campaign
Use the UI or API to create a campaign with a test video.

### 3. Monitor Processing
Check logs for processing status:
```bash
tail -f app.log | grep "video processing"
```

## Troubleshooting

### Common Issues

1. **Video Processing Fails**
   - Check FFmpeg installation: `ffmpeg -version`
   - Verify Cloudinary credentials
   - Check file permissions on uploads directory

2. **AI Captions Not Generating**
   - Verify GEMINI_API_KEY is set
   - Check API quota limits

3. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check PostgreSQL is running
   - Ensure tables are created

### Debug Endpoints
- `GET /api/ad-traffic/check-video-processor` - Check processor status
- `POST /api/ad-traffic/campaigns/{id}/reprocess` - Retry failed campaign

## Performance Optimization

1. **Use Cloudinary** for production - handles large files better
2. **Set up Redis** for background task queue (optional)
3. **Configure CDN** for serving video clips
4. **Database indexes** are crucial for calendar performance

## Security Considerations

1. **File Upload Validation**
   - Max file size: 500MB (configurable)
   - Allowed formats: MP4, MOV, AVI
   - Virus scanning recommended

2. **API Authentication**
   - Implement user authentication
   - Add rate limiting
   - Validate user permissions

3. **Storage Security**
   - Use signed URLs for Cloudinary
   - Implement access controls
   - Regular cleanup of old files 