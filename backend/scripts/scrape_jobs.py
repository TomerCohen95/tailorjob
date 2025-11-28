#!/usr/bin/env python3
"""
Job URL Scraper for CV Matcher Testing

Reads a list of job URLs from a file and scrapes them using the existing
job_scraper_service. Outputs results to JSONL format for batch testing.

Usage:
    python scrape_jobs.py --urls test_data/job_urls.txt --output test_data/jobs.jsonl
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Import existing service
from app.services.job_scraper import job_scraper_service


async def scrape_jobs_from_urls(
    url_file: str,
    output_file: str,
    skip_existing: bool = True
) -> None:
    """
    Scrape jobs from URLs using existing job_scraper_service
    
    Args:
        url_file: Path to file containing job URLs (one per line)
        output_file: Path to output JSONL file
        skip_existing: Skip URLs that already exist in output file
    """
    # Read URLs
    url_path = Path(url_file)
    if not url_path.exists():
        print(f"❌ Error: URL file not found: {url_file}")
        sys.exit(1)
    
    with open(url_path) as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    
    if not urls:
        print(f"❌ Error: No URLs found in {url_file}")
        sys.exit(1)
    
    print(f"📋 Found {len(urls)} URLs to scrape")
    
    # Check for existing output
    existing_urls = set()
    output_path = Path(output_file)
    if skip_existing and output_path.exists():
        print(f"📂 Loading existing results from {output_file}")
        with open(output_path) as f:
            for line in f:
                if line.strip():
                    try:
                        job = json.loads(line)
                        if 'url' in job:
                            existing_urls.add(job['url'])
                    except json.JSONDecodeError:
                        continue
        if existing_urls:
            print(f"✓ Found {len(existing_urls)} already scraped jobs")
    
    # Filter URLs
    urls_to_scrape = [url for url in urls if url not in existing_urls]
    if not urls_to_scrape:
        print(f"✅ All jobs already scraped!")
        return
    
    print(f"🌐 Scraping {len(urls_to_scrape)} new jobs...")
    print()
    
    # Scrape jobs
    results = []
    errors = []
    
    for i, url in enumerate(urls_to_scrape, 1):
        try:
            print(f"[{i}/{len(urls_to_scrape)}] Scraping: {url[:60]}...")
            
            # Call existing scraper service
            job_data = await job_scraper_service.scrape_job(url)
            
            # Add URL and timestamp
            job_data['url'] = url
            job_data['scraped_at'] = datetime.utcnow().isoformat()
            
            # Generate ID if not present
            if 'id' not in job_data or not job_data['id']:
                # Use job_id from scraper if available, otherwise generate
                if job_data.get('job_id'):
                    job_data['id'] = job_data['job_id']
                else:
                    job_data['id'] = f"job-{i:03d}"
            
            results.append(job_data)
            
            title = job_data.get('title', 'Unknown')
            company = job_data.get('company', 'Unknown')
            print(f"    ✓ {title} @ {company}")
            print()
            
        except Exception as e:
            error_msg = str(e)
            errors.append({'url': url, 'error': error_msg})
            print(f"    ✗ Failed: {error_msg}")
            print()
    
    # Save results
    if results:
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append to existing file or create new
        mode = 'a' if output_path.exists() else 'w'
        with open(output_path, mode, encoding='utf-8') as f:
            for job in results:
                f.write(json.dumps(job, ensure_ascii=False) + '\n')
        
        print(f"✅ Successfully scraped {len(results)} jobs")
        print(f"📁 Saved to: {output_file}")
    
    # Report errors
    if errors:
        print()
        print(f"⚠️  Failed to scrape {len(errors)} jobs:")
        for err in errors:
            print(f"   - {err['url'][:60]}...")
            print(f"     Error: {err['error']}")
        
        # Save errors to log
        error_log = output_path.parent / 'scrape_errors.log'
        with open(error_log, 'a', encoding='utf-8') as f:
            f.write(f"\n=== Scraping run: {datetime.utcnow().isoformat()} ===\n")
            for err in errors:
                f.write(f"URL: {err['url']}\n")
                f.write(f"Error: {err['error']}\n\n")
        print(f"📝 Errors logged to: {error_log}")
    
    # Summary
    print()
    print("=" * 60)
    print(f"Summary:")
    print(f"  Total URLs: {len(urls_to_scrape)}")
    print(f"  ✓ Successful: {len(results)}")
    print(f"  ✗ Failed: {len(errors)}")
    print(f"  Success rate: {len(results)/len(urls_to_scrape)*100:.1f}%")
    print("=" * 60)


def main():
    """Parse arguments and run scraper"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scrape job postings from URLs for CV matcher testing'
    )
    parser.add_argument(
        '--urls',
        required=True,
        help='Path to file containing job URLs (one per line)'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to output JSONL file'
    )
    parser.add_argument(
        '--no-skip',
        action='store_true',
        help='Rescrape all URLs even if already in output file'
    )
    
    args = parser.parse_args()
    
    # Run scraper
    asyncio.run(scrape_jobs_from_urls(
        url_file=args.urls,
        output_file=args.output,
        skip_existing=not args.no_skip
    ))


if __name__ == '__main__':
    main()