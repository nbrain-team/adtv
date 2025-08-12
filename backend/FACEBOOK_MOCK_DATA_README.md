# Facebook Automation Mock Data

The Facebook Automation module includes comprehensive mock data for testing and development when Facebook API credentials are not configured.

## How It Works

When the environment variables `FACEBOOK_APP_ID` and `FACEBOOK_APP_SECRET` are not set, the system automatically switches to mock mode.

## Mock Data Includes

### 1. Mock Realtor Clients (3 total)
- **Sarah Johnson - Premier Real Estate**: Active, auto-convert enabled, $75/day budget
- **Mike Chen - Luxury Homes Specialist**: Active, manual conversion, $100/day budget  
- **The Davis Team - Your Local Experts**: Active, auto-convert enabled, $50/day budget

### 2. Mock Facebook Posts (15 per client)
Realistic realtor content including:
- New listing announcements
- Open house invitations
- Market updates
- Client testimonials
- First-time buyer tips
- Success stories (SOLD posts)
- Educational content

Each post includes:
- Realistic engagement metrics (likes, comments, shares)
- AI quality scores (70-99)
- AI-generated improvement suggestions
- Professional real estate images from Unsplash

### 3. Mock Ad Campaigns (8 per client)
- Various objectives: REACH, TRAFFIC, ENGAGEMENT, LEAD_GENERATION
- Realistic performance metrics (CTR, CPC, ROAS)
- Different statuses: active, paused, completed, draft
- Campaign names relevant to real estate marketing

### 4. Mock Analytics
- Aggregated performance data
- Top performing campaigns
- Demographic breakdowns
- Device usage statistics

## Testing Flow

1. Start the application without Facebook credentials
2. Navigate to Facebook Automation module
3. Click "Connect Facebook Page"
4. You'll be redirected immediately with mock credentials
5. The system creates 3 mock realtor pages
6. Each page has 15 pre-generated posts
7. Posts can be converted to ads
8. Analytics show realistic performance data

## Visual Indicator

When in mock mode, a yellow banner appears at the top:
```
🧪 Mock Mode Active
You're viewing test data. Connect to Facebook to see real data.
```

## Benefits

- **No Setup Required**: Test immediately without Facebook App configuration
- **Realistic Data**: All content is tailored to real estate marketing
- **Full Feature Testing**: Test all features including post-to-ad conversion
- **Safe Environment**: No risk of accidentally creating real ads

## Switching to Production

To use real Facebook data:
1. Set up Facebook App (see FACEBOOK_SETUP_INSTRUCTIONS.md)
2. Add environment variables:
   ```
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   FACEBOOK_WEBHOOK_VERIFY_TOKEN=your_webhook_token
   ```
3. Restart the application
4. Mock mode will automatically disable 