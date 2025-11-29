"""
Test script to verify search/list page detection in job scraper
"""
import asyncio
import sys
from app.services.job_scraper import job_scraper_service

async def test_microsoft_search_page():
    """Test that Microsoft careers search page is properly detected and rejected"""
    
    # This is a search results page, NOT a direct job posting
    search_url = "https://apply.careers.microsoft.com/careers?start=20&location=Israel%2C+Tel+Aviv%2C+Herzliya&pid=1970393556631650&sort_by=distance&filter_distance=160&filter_include_remote=1"
    
    print("🧪 Testing Microsoft careers search page detection...")
    print(f"📋 URL: {search_url}\n")
    
    try:
        job_data = await job_scraper_service.scrape_job(search_url)
        print("❌ FAILED: Search page was not detected!")
        print(f"   Extracted data: {job_data}")
        return False
    except ValueError as e:
        error_msg = str(e)
        if "search results page" in error_msg.lower():
            print("✅ PASSED: Search page correctly detected!")
            print(f"   Error message: {error_msg}")
            return True
        else:
            print("⚠️  PARTIAL: Error raised but not the expected one")
            print(f"   Error message: {error_msg}")
            return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {type(e).__name__}: {e}")
        return False

async def main():
    success = await test_microsoft_search_page()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())