# Residential Proxy Setup Guide

## Quick Start

### 1. Sign up for a proxy service

Recommended services:
- **Smartproxy**: https://smartproxy.com (Good for beginners)
- **Bright Data**: https://brightdata.com (Most reliable)
- **IPRoyal**: https://iproyal.com (Budget option)

### 2. Get your proxy credentials

After signing up, you'll receive:
- Proxy endpoint (e.g., `gate.smartproxy.com:10000`)
- Username
- Password

### 3. Set environment variable

On your local machine:
```bash
export RESIDENTIAL_PROXY_URL="http://username:password@gate.smartproxy.com:10000"
```

On Render.com:
1. Go to your service dashboard
2. Click "Environment" tab
3. Add new environment variable:
   - Key: `RESIDENTIAL_PROXY_URL`
   - Value: `http://username:password@gate.smartproxy.com:10000`

### 4. Test locally

```bash
cd backend/realtor_importer
python proxy_scraper.py
```

## Proxy Service Details

### Smartproxy Setup
1. Sign up at https://smartproxy.com
2. Choose "Residential Proxies"
3. Select "Pay As You Go" plan
4. Get endpoint from dashboard:
   ```
   http://username:password@gate.smartproxy.com:10000
   ```

### Bright Data Setup
1. Sign up at https://brightdata.com
2. Create a "Residential Zone"
3. Get credentials from zone settings:
   ```
   http://username-session-rand12345:password@zproxy.lum-superproxy.io:22225
   ```

### IPRoyal Setup
1. Sign up at https://iproyal.com
2. Choose "Residential Proxies"
3. Generate proxy list
4. Format as:
   ```
   http://username:password@geo.iproyal.com:12321
   ```

## Important Notes

- **Costs**: Residential proxies charge by data usage (GB)
- **Rotation**: Most services auto-rotate IPs
- **Location**: Some services let you choose specific countries/cities
- **Speed**: Residential proxies are slower than datacenter proxies

## Troubleshooting

### Test your proxy:
```python
import requests

proxy_url = "http://username:password@proxy.server.com:port"
proxies = {'http': proxy_url, 'https': proxy_url}

response = requests.get('http://httpbin.org/ip', proxies=proxies)
print(response.json())  # Should show proxy IP
```

### Common issues:
1. **Authentication failed**: Check username/password
2. **Connection timeout**: Try different proxy endpoint
3. **Still getting 403**: Contact proxy provider support 