# ADTV Traffic Module Export Package

## 🎬 What is ADTV Traffic?

A comprehensive social media campaign management system that automatically:
- Splits long videos into 30-second clips
- Analyzes video content using AI vision
- Generates contextual social media captions
- Schedules posts across multiple platforms
- Provides an intuitive calendar interface

## 📦 Package Contents

```
adtv-traffic-export/
├── backend/
│   ├── ad_traffic/          # Complete backend module
│   └── core/
│       └── llm_handler.py   # AI integration utilities
├── frontend/
│   ├── components/          # React components
│   └── pages/               # Page components
├── docs/
│   ├── INSTALLATION_GUIDE.md  # Detailed setup instructions
│   ├── CURSOR_PROMPT.md       # AI assistant integration
│   └── QUICK_START.md         # 5-minute setup guide
├── requirements.txt         # Python dependencies
├── env.example             # Environment template
└── README.md               # This file
```

## 🚀 Quick Installation

```bash
# 1. Copy files to your project
cp -r adtv-traffic-export/* your-project/

# 2. Install dependencies
pip install -r requirements.txt
npm install @radix-ui/react-* lucide-react date-fns

# 3. Set up database (PostgreSQL)
psql -U your_user -d your_db < docs/schema.sql

# 4. Configure environment
cp env.example .env
# Edit .env with your API keys

# 5. Integrate with your app
# See QUICK_START.md for code examples
```

## 🔑 Key Features

### Video Processing
- **Automatic Clipping**: Splits videos into optimal 30-second segments
- **Smart Thumbnails**: Generates preview images for each clip
- **Multiple Processors**: Cloudinary (cloud), FFmpeg (local), MoviePy (fallback)

### AI-Powered Content
- **Vision Analysis**: Analyzes video frames to understand content
- **Contextual Captions**: Generates captions based on what's actually shown
- **Smart Hashtags**: Relevant tags for better reach

### Campaign Management
- **Client Organization**: Manage multiple clients and campaigns
- **Calendar View**: Visual scheduling interface
- **Platform Support**: Facebook, Instagram, Twitter, LinkedIn, TikTok
- **Progress Tracking**: Real-time processing updates

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **Cloudinary** - Cloud video processing
- **Gemini AI** - Content generation

### Frontend
- **React** - UI framework
- **TypeScript** - Type safety
- **Radix UI** - Accessible components
- **Tailwind CSS** - Styling

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- FFmpeg (for local processing)
- Gemini API key (for AI features)

## 🔧 Configuration Options

### Video Processing
```env
# Use Cloudinary (Recommended)
CLOUDINARY_CLOUD_NAME=your_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret

# Or use local FFmpeg (automatically detected)
```

### AI Features
```env
GEMINI_API_KEY=your_gemini_key  # Required for captions
```

## 📚 Documentation

1. **[QUICK_START.md](docs/QUICK_START.md)** - Get running in 5 minutes
2. **[INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)** - Comprehensive setup
3. **[CURSOR_PROMPT.md](docs/CURSOR_PROMPT.md)** - Use with Cursor AI

## 🤝 Integration Examples

### Adding to FastAPI App
```python
from ad_traffic.api import router as ad_traffic_router

app.include_router(
    ad_traffic_router,
    prefix="/api/ad-traffic"
)
```

### Adding to React App
```tsx
import AdTrafficPage from './pages/AdTrafficPage';

<Route path="/ad-traffic" element={<AdTrafficPage />} />
```

## ⚡ Performance Tips

1. **Use Cloudinary** for production - handles large files efficiently
2. **Enable caching** for processed videos
3. **Set up CDN** for video delivery
4. **Use background workers** for processing

## 🔒 Security Notes

- Validates file uploads (type, size)
- Requires user authentication
- Supports role-based access
- Sanitizes user input

## 🐛 Troubleshooting

### Common Issues:
- **"Module not found"** - Check Python path and __init__.py files
- **"Video processing failed"** - Verify FFmpeg installation
- **"AI captions not generating"** - Check Gemini API key and quota

### Debug Tools:
- `GET /api/ad-traffic/check-video-processor` - Test setup
- Check logs for detailed error messages
- Use CURSOR_PROMPT.md for AI assistance

## 📈 Success Metrics

When properly installed, you can:
- ✅ Upload videos and see progress
- ✅ View generated clips with thumbnails
- ✅ See AI-generated captions matching content
- ✅ Schedule posts on calendar
- ✅ Edit and manage campaigns

## 🎯 Use Cases

Perfect for:
- Marketing agencies
- Content creators
- Social media managers
- Real estate professionals
- Small businesses

## 💡 Pro Tips

1. **Batch Processing**: Upload multiple videos at once
2. **Template Captions**: Save successful caption styles
3. **Scheduling Strategy**: Space posts 2-3 days apart
4. **A/B Testing**: Try different caption styles

## 🆘 Support

- Check documentation files
- Review code comments
- Use CURSOR_PROMPT.md with AI
- Examine error logs

---

Built with ❤️ for ADTV by the nBrain team 