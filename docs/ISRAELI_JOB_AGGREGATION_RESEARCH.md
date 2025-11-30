# Israeli Job Aggregation Research

**Date:** 2024-11-30  
**Status:** Research Complete

## Summary

Research into job aggregation options for Israeli tech market, including APIs, sitemaps, and scraping approaches.

---

## Key Findings

### ✅ What Works

1. **Adzuna API** (Global, NOT Israel)
   - Status: ✅ Working perfectly
   - Credentials: App ID `8cd13b3f`, App Key `ca313f07...`
   - Tested: 5,883 results for "Software Engineer" in New York
   - **Issue:** Israel (IL) not supported
   - Supported countries: at, au, be, br, ca, ch, de, es, fr, gb, in, it, mx, nl, nz, pl, sg, us, za
   - Rate limit: 1 request/second (free tier)
   - Documentation: https://developer.adzuna.com/

2. **Workday Sitemaps** (Company-Specific)
   - Tested: Vanguard (`https://vanguard.wd5.myworkdayjobs.com/en-US/vanguard_external/siteMap.xml`)
   - Result: ✅ 100 jobs fetched successfully
   - Format: XML with job metadata (title, location, date_posted, description)
   - Memory-efficient streaming parsing available

---

## ❌ What Doesn't Work

### Israeli Job Boards (Anti-Bot Protected)

1. **AllJobs.co.il**
   - RSS URL: `https://www.alljobs.co.il/RSS/rssNewJobs.aspx`
   - Status: ❌ 404 (RSS feed removed)
   - Anti-bot: Stormcaster protection
   - No public API

2. **Drushim.co.il**
   - RSS URL: `https://www.drushim.co.il/rss/jobs.asp`
   - Status: ❌ Redirects, anti-bot protection
   - Anti-bot: Stormcaster protection
   - No public API

### Israeli Tech Companies (No Public Sitemaps)

Tested 10 major Israeli companies:
- ❌ Wix: No sitemap found
- ❌ Mobileye: No sitemap found
- ❌ monday.com: No sitemap found
- ❌ ironSource: No sitemap found
- ❌ JFrog: No sitemap found
- ❌ Checkmarx: No sitemap found
- ❌ Fiverr: No sitemap found
- ❌ AppsFlyer: No sitemap found
- ❌ Minute Media: No sitemap found
- ❌ Via: No sitemap found

### LinkedIn Scraping
- Status: ❌ Not recommended
- Issues: Illegal (ToS violation), complex anti-bot, expensive proxies
- See: `docs/LINKEDIN_JOB_SCRAPING_GUIDE.md`

---

## 📊 Recommended Approach for TailorJob

### Option 1: Manual Job Entry + Workday Sitemaps (Recommended)
**Best for MVP with limited resources**

- Users manually paste job URLs or descriptions
- Backend scrapes individual job pages when needed
- Optional: Add Workday sitemap crawler for specific companies
- Pros: Simple, legal, works immediately
- Cons: Requires user input

### Option 2: Adzuna API for Global Jobs
**Best for international expansion**

- Use Adzuna for US, UK, Europe, Australia jobs
- 18 supported countries (not Israel)
- Free tier: 1 request/second
- Pros: Official API, reliable, large dataset
- Cons: No Israeli jobs

### Option 3: Custom Israeli Job Board Integration
**Best for Israeli market (requires partnerships)**

- Contact AllJobs.co.il, Drushim.co.il for API access
- Potentially paid partnerships
- Pros: Direct access to Israeli jobs
- Cons: Requires business relationships, potential costs

### Option 4: RapidAPI LinkedIn Services
**Best if you need LinkedIn data legally**

- Services like `linkedin-data-api` on RapidAPI
- Paid (starts $0.001/request)
- Legal alternative to scraping
- Pros: Legal, reliable
- Cons: Ongoing costs

---

## 🛠️ Implementation Files Created

1. **temp_sitemap_fetcher.py**
   - Basic XML sitemap parser
   - Successfully fetched Vanguard jobs

2. **streaming_sitemap_parser.py**
   - Memory-efficient iterparse approach
   - Line-by-line search without loading full XML
   - Location filtering

3. **fetch_israel_jobs.py**
   - Tests 10 Israeli tech companies
   - Checks for Workday sitemaps

4. **test_adzuna_api.py**
   - Adzuna API integration
   - Configured with user credentials
   - Multiple search scenarios

---

## 💡 Current TailorJob Implementation

Based on `backend/app/services/job_scraper.py`:

```python
class JobScraperService:
    async def scrape_job(self, url: str) -> Dict:
        """Scrapes individual job page on-demand"""
        # Supports: LinkedIn, Indeed, Glassdoor, generic sites
        # Uses BeautifulSoup + Playwright for JS-heavy sites
```

**Current approach:** Users paste job URLs → Backend scrapes on-demand

**Recommended next steps:**
1. Keep current manual approach for MVP
2. Add Workday sitemap support for specific companies
3. Consider Adzuna for US/international expansion
4. Explore partnerships with Israeli job boards for native support

---

## 📈 Market Comparison

| Source | Coverage | Cost | Difficulty | Israeli Jobs |
|--------|----------|------|------------|--------------|
| Manual Entry | User-provided | Free | Easy | ✅ Yes |
| Workday Sitemaps | Select companies | Free | Medium | ⚠️ Some |
| Adzuna API | 18 countries | Free/Paid | Easy | ❌ No |
| Israeli Job Boards | Israel-focused | Negotiated | High | ✅ Yes |
| RapidAPI LinkedIn | Global | Paid | Medium | ✅ Yes |

---

## 🔗 References

- Adzuna Documentation: https://developer.adzuna.com/
- Workday Sitemap Example: https://vanguard.wd5.myworkdayjobs.com/en-US/vanguard_external/siteMap.xml
- LinkedIn Job Scraping Analysis: `docs/LINKEDIN_JOB_SCRAPING_GUIDE.md`
- Adzuna Setup Guide: `docs/ADZUNA_SETUP_GUIDE.md`

---

## ✅ Conclusion

**For Israeli market:**
- Current manual approach is best for MVP
- No free, easy API exists for Israeli jobs
- Partnerships with AllJobs/Drushim required for native support

**For global expansion:**
- Adzuna API is production-ready
- Already have working credentials
- Can support 18 countries immediately

**Recommended MVP approach:**
1. Continue with manual job URL entry
2. Add optional Workday sitemap support
3. Focus on CV matching quality over job aggregation quantity