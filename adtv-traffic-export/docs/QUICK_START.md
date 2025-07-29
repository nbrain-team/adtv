# ADTV Traffic Module - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Copy Files
```bash
# Copy backend files
cp -r adtv-traffic-export/backend/ad_traffic your-project/backend/

# Copy frontend files  
cp -r adtv-traffic-export/frontend/components/AdTraffic your-project/frontend/src/components/
cp adtv-traffic-export/frontend/pages/AdTrafficPage.tsx your-project/frontend/src/pages/
```

### 2. Install Dependencies
```bash
# Backend
cd your-project/backend
pip install cloudinary ffmpeg-python moviepy langchain-google-genai

# Frontend
cd your-project/frontend
npm install @radix-ui/react-dialog @radix-ui/react-select lucide-react date-fns
```

### 3. Database Setup
```sql
-- Run this SQL in your PostgreSQL database
CREATE TABLE ad_traffic_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    contact_info TEXT,
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES ad_traffic_clients(id) ON DELETE CASCADE,
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

CREATE TABLE video_clips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
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

CREATE TABLE social_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES ad_traffic_clients(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    video_clip_id UUID REFERENCES video_clips(id) ON DELETE SET NULL,
    content TEXT,
    platforms TEXT[],
    scheduled_time TIMESTAMP,
    published_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'DRAFT',
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. Backend Integration
```python
# In your main.py or app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from ad_traffic.api import router as ad_traffic_router

app = FastAPI()

# Mount the API routes
app.include_router(
    ad_traffic_router,
    prefix="/api/ad-traffic",
    tags=["ad-traffic"]
)

# Mount static files for video serving
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```

### 5. Frontend Integration
```tsx
// In your App.tsx or router file
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AdTrafficPage from './pages/AdTrafficPage';

function App() {
  return (
    <Router>
      <Routes>
        {/* Your existing routes */}
        <Route path="/ad-traffic" element={<AdTrafficPage />} />
      </Routes>
    </Router>
  );
}
```

### 6. Environment Setup
```bash
# Create .env file in your backend directory
cp adtv-traffic-export/env.example backend/.env

# Edit with your values:
GEMINI_API_KEY=your_key_here
CLOUDINARY_CLOUD_NAME=your_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret
```

### 7. Create Upload Directories
```bash
mkdir -p uploads/campaigns uploads/clips uploads/thumbnails
chmod 755 uploads/
```

## ✅ Test Your Installation

### Backend Test:
```bash
curl http://localhost:8000/api/ad-traffic/check-video-processor
```

### Frontend Test:
1. Navigate to `http://localhost:3000/ad-traffic`
2. You should see the Ad Traffic dashboard

## 🎉 Success!

You can now:
- Create clients
- Upload videos
- Generate AI-powered social media campaigns
- Schedule posts with contextual captions

## 🔧 Common Issues

### "Module not found" Error
```bash
# Make sure __init__.py exists
touch backend/ad_traffic/__init__.py
```

### Video Processing Fails
```bash
# Install system dependency
sudo apt-get install ffmpeg  # Linux
brew install ffmpeg          # macOS
```

### Database Connection Error
- Check your DATABASE_URL in .env
- Ensure PostgreSQL is running
- Verify user has CREATE TABLE permissions

## 📚 Next Steps

1. **Configure Cloudinary** (Recommended)
   - Sign up at cloudinary.com
   - Add credentials to .env
   - Enables reliable cloud video processing

2. **Customize Auth**
   - Update `get_current_user` in api.py
   - Match your authentication system

3. **Style Integration**
   - Update Tailwind config
   - Customize component colors
   - Add your brand fonts

## 🆘 Need Help?

Check the full documentation:
- `INSTALLATION_GUIDE.md` - Detailed setup
- `CURSOR_PROMPT.md` - AI assistance guide
- Backend code comments - Implementation details 