# Adzuna API Setup Guide

## Quick Start (5 minutes)

### Step 1: Get Free API Credentials

1. Go to https://developer.adzuna.com/
2. Click "Sign Up" (top right)
3. Fill in your details:
   - Name
   - Email
   - Company (can put "Personal Project")
   - Purpose: "Job aggregation for CV matching app"
4. Verify your email
5. Create an app to get your credentials:
   - App Name: "TailorJob"
   - Description: "CV tailoring and job matching application"
6. Copy your **App ID** and **App Key**

### Step 2: Test the API

```bash
# Quick test with curl (replace with your credentials)
curl "https://api.adzuna.com/v1/api/jobs/il/search/1?app_id=YOUR_APP_ID&app_key=YOUR_APP_KEY&what=software+engineer&results_per_page=5"
```

### Step 3: Run Test Script

```bash
# Edit test_adzuna_api.py and add your credentials
python3 test_adzuna_api.py
```

## API Limits & Pricing

### Free Tier (Perfect for MVP)
- **250 API calls per month** (FREE)
- Rate limit: 1 request per second
- No credit card required
- Access to all job data

### Paid Tiers (If you need more)
- **Starter**: $249/month - 5,000 calls
- **Professional**: $499/month - 10,000 calls
- **Enterprise**: Custom pricing

## API Endpoints for Israel

### Base URL
```
https://api.adzuna.com/v1/api/jobs/il
```

### Search Jobs
```
GET /search/{page}
```

**Parameters:**
- `app_id` (required): Your App ID
- `app_key` (required): Your App Key  
- `what`: Keywords (e.g., "python developer")
- `where`: Location (e.g., "tel aviv", "jerusalem")
- `results_per_page`: Number of results (max 50)
- `category`: Job category
- `salary_min`: Minimum salary filter
- `salary_max`: Maximum salary filter
- `sort_by`: "date" (newest first) or "relevance"

**Example:**
```bash
curl "https://api.adzuna.com/v1/api/jobs/il/search/1?app_id=YOUR_ID&app_key=YOUR_KEY&what=software+engineer&where=tel+aviv&results_per_page=10"
```

### Get Job Details
```
GET /jobs/{adref}
```

### Top Companies
```
GET /top_companies
```

### Categories (Browse)
```
GET /categories
```

## Response Format

```json
{
  "count": 1523,
  "mean": 12000,
  "results": [
    {
      "id": "3456789012",
      "created": "2024-01-15T10:30:00Z",
      "title": "Senior Python Developer",
      "location": {
        "area": ["Israel", "Tel Aviv"],
        "display_name": "Tel Aviv, Israel"
      },
      "description": "We are looking for...",
      "company": {
        "display_name": "Tech Company Ltd"
      },
      "salary_min": 15000,
      "salary_max": 25000,
      "redirect_url": "https://www.adzuna.co.il/land/ad/...",
      "category": {
        "label": "IT Jobs",
        "tag": "it-jobs"
      }
    }
  ]
}
```

## Integration Example

```python
import requests

class AdzunaClient:
    def __init__(self, app_id: str, app_key: str):
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://api.adzuna.com/v1/api/jobs/il"
    
    def search_jobs(self, keyword: str, location: str = None, page: int = 1):
        url = f"{self.base_url}/search/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": keyword,
            "results_per_page": 50
        }
        
        if location:
            params["where"] = location
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

# Usage
client = AdzunaClient("YOUR_APP_ID", "YOUR_APP_KEY")
jobs = client.search_jobs("python developer", "tel aviv")

for job in jobs["results"]:
    print(f"{job['title']} at {job['company']['display_name']}")
```

## Best Practices

### 1. Cache Results
```python
import redis
import json

# Cache for 1 hour
cache = redis.Redis()
cache_key = f"adzuna:{keyword}:{location}"
cached = cache.get(cache_key)

if cached:
    return json.loads(cached)
else:
    results = search_jobs(keyword, location)
    cache.setex(cache_key, 3600, json.dumps(results))
    return results
```

### 2. Rate Limiting
```python
import time
from datetime import datetime, timedelta

last_request = None
MIN_INTERVAL = 1.0  # 1 second between requests

def rate_limited_search(*args, **kwargs):
    global last_request
    
    if last_request:
        elapsed = (datetime.now() - last_request).total_seconds()
        if elapsed < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - elapsed)
    
    result = search_jobs(*args, **kwargs)
    last_request = datetime.now()
    return result
```

### 3. Error Handling
```python
try:
    jobs = search_jobs("python", "tel aviv")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        print("Rate limit exceeded")
    elif e.response.status_code == 401:
        print("Invalid credentials")
    else:
        print(f"HTTP Error: {e}")
except requests.exceptions.Timeout:
    print("Request timeout")
except Exception as e:
    print(f"Error: {e}")
```

## Add to Your Backend

### 1. Add to requirements.txt
```txt
requests==2.31.0
```

### 2. Add environment variables
```bash
# .env
ADZUNA_APP_ID=your_app_id_here
ADZUNA_APP_KEY=your_app_key_here
```

### 3. Create service file
```python
# backend/app/services/adzuna_service.py
import os
import requests
from typing import List, Dict, Optional

class AdzunaService:
    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        self.base_url = "https://api.adzuna.com/v1/api/jobs/il"
    
    def search_jobs(
        self,
        keyword: str,
        location: Optional[str] = None,
        page: int = 1,
        results_per_page: int = 20
    ) -> Dict:
        url = f"{self.base_url}/search/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": keyword,
            "results_per_page": min(results_per_page, 50),
            "sort_by": "date"
        }
        
        if location:
            params["where"] = location
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
```

### 4. Add API endpoint
```python
# backend/app/main.py
from app.services.adzuna_service import AdzunaService

adzuna = AdzunaService()

@app.get("/api/jobs/search")
async def search_jobs(
    keyword: str,
    location: str = None,
    page: int = 1
):
    try:
        results = adzuna.search_jobs(keyword, location, page)
        return {
            "success": True,
            "count": results.get("count", 0),
            "jobs": results.get("results", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Monitoring Usage

Track your API usage to stay within free tier:

```python
# Simple counter
import redis

redis_client = redis.Redis()

def track_api_call():
    month_key = f"adzuna:calls:{datetime.now().strftime('%Y-%m')}"
    redis_client.incr(month_key)
    redis_client.expire(month_key, 32 * 24 * 3600)  # 32 days

def get_monthly_usage():
    month_key = f"adzuna:calls:{datetime.now().strftime('%Y-%m')}"
    return int(redis_client.get(month_key) or 0)

# Check before making call
if get_monthly_usage() >= 250:
    raise Exception("Monthly API limit reached")
```

## Common Issues

### 401 Unauthorized
- Check your App ID and App Key
- Make sure they're not expired

### 429 Rate Limited  
- You're making requests too fast
- Wait 1 second between requests

### Empty Results
- Try broader keywords
- Check if location spelling is correct
- Israel market might have fewer listings for some positions

## Next Steps

1. ✅ Get API credentials
2. ✅ Test with curl or Python script
3. ✅ Add to backend service
4. ✅ Implement caching
5. ✅ Add rate limiting
6. ✅ Monitor usage
7. ✅ Combine with other sources (Workday, etc.)

## Support

- Documentation: https://developer.adzuna.com/docs/search
- Contact: developers@adzuna.com
- Status: https://status.adzuna.com/