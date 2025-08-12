# Facebook App Setup Instructions

This guide will help your admin set up the Facebook App required for the Facebook Automation module.

## Prerequisites
- Facebook Business Account
- Admin access to Facebook Business Manager
- SSL-enabled domain for webhook callbacks

## Step 1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Choose "Business" as the app type
4. Fill in:
   - App Name: `[Your Company] Ad Automation`
   - App Contact Email: `admin@yourcompany.com`
   - Business Account: Select your business account

## Step 2: Configure Basic Settings

1. In your app dashboard, go to "Settings" → "Basic"
2. Note down:
   - **App ID**: `XXXXXXXXXXXXXXX`
   - **App Secret**: `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
3. Add these to your `.env` file:
   ```
   FACEBOOK_APP_ID=XXXXXXXXXXXXXXX
   FACEBOOK_APP_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   FACEBOOK_WEBHOOK_VERIFY_TOKEN=your-random-webhook-token
   ```

## Step 3: Add Required Products

### Facebook Login
1. Click "Add Product" and select "Facebook Login"
2. Choose "Web" platform
3. Site URL: `https://yourdomain.com`
4. Valid OAuth Redirect URIs:
   ```
   https://yourdomain.com/facebook-callback
   http://localhost:3000/facebook-callback (for development)
   ```

### Webhooks
1. Add "Webhooks" product
2. Subscribe to "Page" object with these fields:
   - `feed` (for new posts)
   - `mention` (for page mentions)

### Marketing API
1. Add "Marketing API" product
2. This enables ad creation and management

## Step 4: Configure Permissions

1. Go to "App Review" → "Permissions and Features"
2. Request these permissions:
   - `pages_show_list` - See list of Pages you manage
   - `pages_read_engagement` - Read content posted on your Pages
   - `pages_manage_posts` - Create, edit and delete posts
   - `ads_management` - Manage ads and campaigns
   - `business_management` - Manage business assets
   - `pages_manage_ads` - Manage ads associated with Pages
   - `instagram_basic` (optional) - For Instagram integration
   - `instagram_content_publish` (optional) - Post to Instagram

## Step 5: Webhook Configuration

1. In Webhooks settings, set:
   - Callback URL: `https://yourdomain.com/api/facebook-automation/webhook`
   - Verify Token: Same as `FACEBOOK_WEBHOOK_VERIFY_TOKEN` in .env
2. Subscribe to webhook fields:
   - Page → feed
   - Page → mention

## Step 6: Generate Long-Lived Tokens

For production, you'll need to implement token refresh:

1. Exchange short-lived tokens for long-lived ones
2. Long-lived page tokens last ~60 days
3. Implement automatic token refresh before expiry

## Step 7: Test Your Setup

1. Use Graph API Explorer to test permissions
2. Verify webhook is receiving events
3. Test OAuth flow with a test user

## Step 8: App Review (For Production)

Before going live with non-admin users:

1. Submit for App Review
2. Provide:
   - Screencast showing OAuth flow
   - Explanation of each permission use
   - Test user credentials
3. Review typically takes 5-7 business days

## Security Best Practices

1. **Never expose App Secret** - Keep it server-side only
2. **Use HTTPS** for all callbacks and webhooks
3. **Validate webhook signatures** to ensure requests are from Facebook
4. **Implement rate limiting** to avoid API limits
5. **Store tokens encrypted** in your database
6. **Monitor token expiration** and refresh proactively

## API Limits

Be aware of Facebook's rate limits:
- 200 calls per hour per user
- 4800 calls per hour per app
- Batch requests count as single calls

## Troubleshooting

### Common Issues:
1. **"Invalid OAuth redirect URI"**
   - Ensure redirect URI matches exactly (including trailing slashes)
   
2. **"Insufficient permissions"**
   - Check if permissions are approved in App Review
   
3. **Webhook not receiving events**
   - Verify SSL certificate is valid
   - Check webhook subscription is active

### Debug Tools:
- Graph API Explorer: Test API calls
- Access Token Debugger: Verify token permissions
- Webhook Event Log: See received events

## Support Resources

- [Facebook Business Help Center](https://www.facebook.com/business/help)
- [Graph API Documentation](https://developers.facebook.com/docs/graph-api)
- [Marketing API Documentation](https://developers.facebook.com/docs/marketing-api)

## Next Steps

Once setup is complete:
1. Add environment variables to your deployment
2. Deploy the application
3. Test OAuth flow with your Facebook account
4. Monitor logs for any API errors

For any issues, check the Facebook Developer Console for error details and API status. 