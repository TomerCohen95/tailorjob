import httpx
from bs4 import BeautifulSoup
from openai import AsyncAzureOpenAI
from app.config import settings
import json
import re

class JobScraperService:
    """
    Hybrid job scraper using BeautifulSoup preprocessing + Azure OpenAI extraction.
    Cost-effective approach that reduces AI token usage.
    
    For JavaScript-heavy sites (LinkedIn, Indeed), tries to extract from page metadata
    and JSON-LD structured data first before falling back to full AI extraction.
    """
    
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
    
    async def scrape_job(self, url: str) -> dict:
        """
        Scrape job posting from URL.
        
        Process:
        1. Fetch HTML with httpx
        2. Try to extract from structured data (JSON-LD, Open Graph)
        3. If insufficient, clean HTML and send to AI
        
        Args:
            url: Job posting URL
            
        Returns:
            dict: {title, company, description}
        """
        # Step 1: Fetch HTML
        html = await self._fetch_html(url)
        
        # Step 2: Try structured data extraction first (cheaper)
        structured_data = self._extract_structured_data(html)
        if structured_data and self._is_complete_job_data(structured_data):
            # Validate before returning
            self._validate_job_page(html, structured_data)
            print(f"✅ Extracted from structured data: {structured_data.get('title', 'N/A')}")
            return structured_data
        
        # Step 3: Fall back to AI extraction with cleaned text
        clean_text = self._extract_clean_text(html)
        
        # If we have partial structured data, pass it as a hint to AI
        job_data = await self._extract_job_data(clean_text, hint=structured_data)
        
        # Step 4: Validate the extracted data
        print(f"🔍 Validating job data: title='{job_data.get('title', 'N/A')}'")
        self._validate_job_page(html, job_data)
        
        return job_data
    
    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML from URL with proper headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                print(f"🌐 Fetching URL: {url}")
                response = await client.get(url, headers=headers)
                print(f"📥 Response status: {response.status_code}")
                response.raise_for_status()
                return response.text
        except httpx.TimeoutException as e:
            print(f"⏱️ Timeout error fetching {url}: {str(e)}")
            raise ValueError(f"Connection timeout while fetching job posting. The site may be slow or unreachable.")
        except httpx.HTTPStatusError as e:
            print(f"🚫 HTTP error {e.response.status_code} for {url}")
            raise ValueError(f"Failed to fetch job posting: HTTP {e.response.status_code}")
        except httpx.ConnectError as e:
            print(f"🔌 Connection error for {url}: {str(e)}")
            raise ValueError(f"Cannot connect to job posting site. Please check the URL and try again.")
        except Exception as e:
            print(f"❌ Unexpected error fetching {url}: {type(e).__name__}: {str(e)}")
            raise ValueError(f"Failed to fetch job posting: {str(e)}")
    
    def _extract_structured_data(self, html: str) -> dict | None:
        """
        Extract job data from structured metadata (JSON-LD, Open Graph, meta tags).
        Works well for LinkedIn, Indeed, and other professional sites.
        """
        soup = BeautifulSoup(html, 'html.parser')
        job_data = {}
        
        # Try JSON-LD structured data (best source)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                    job_data['title'] = data.get('title', '')
                    job_data['company'] = data.get('hiringOrganization', {}).get('name', '')
                    job_data['description'] = data.get('description', '')
                    print(f"📊 Found JSON-LD job posting data")
                    return job_data
            except:
                continue
        
        # Try Open Graph meta tags
        og_title = soup.find('meta', property='og:title')
        og_description = soup.find('meta', property='og:description')
        
        if og_title:
            job_data['title'] = og_title.get('content', '')
        if og_description:
            # OG description often has company info
            desc = og_description.get('content', '')
            job_data['description'] = desc
            # Try to extract company from description
            if ' at ' in desc:
                parts = desc.split(' at ', 1)
                if len(parts) == 2:
                    job_data['company'] = parts[1].split(' ·')[0].strip()
        
        # Try standard meta tags
        if not job_data.get('title'):
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.string or ''
                # Often format: "Job Title - Company | Site"
                job_data['title'] = title_text.split('|')[0].split('-')[0].strip()
        
        # Try to find company in meta
        company_meta = soup.find('meta', attrs={'name': 'company'}) or \
                      soup.find('meta', attrs={'property': 'og:site_name'})
        if company_meta and not job_data.get('company'):
            job_data['company'] = company_meta.get('content', '')
        
        return job_data if job_data else None
    
    def _is_complete_job_data(self, data: dict | None) -> bool:
        """Check if we have complete job data (title, company, description)"""
        if not data:
            return False
        return bool(data.get('title') and data.get('company') and
                   data.get('description') and len(data.get('description', '')) > 100)
    
    def _validate_job_page(self, html: str, job_data: dict) -> None:
        """
        Validate that the page is actually a job posting, not a login/error page.
        Raises ValueError with user-friendly message if invalid.
        """
        title = str(job_data.get('title', '')).lower()
        company = str(job_data.get('company', '')).lower()
        description = str(job_data.get('description', '')).lower()
        
        # Red flags in title that indicate non-job pages (be specific to avoid false positives)
        invalid_title_patterns = [
            'login', 'sign in', 'sign up', 'log in', 'signin',
            'register', 'authentication',
            'error', '404', '403', 'access denied', 'page not found',
            'redirect', 'loading', 'please wait'
        ]
        
        # Only flag if the keyword is a significant part of the title
        for keyword in invalid_title_patterns:
            # Check if keyword appears as whole word or with common separators
            if re.search(rf'\b{keyword}\b', title) or f' {keyword} ' in f' {title} ':
                # Extra check: if it's "login" but also has job-related words, it's probably a real job
                job_keywords = ['engineer', 'developer', 'manager', 'analyst', 'designer', 'lead', 'senior', 'junior']
                has_job_keyword = any(job_word in title for job_word in job_keywords)
                
                if not has_job_keyword:
                    raise ValueError(
                        f"Invalid job posting - the page title contains '{keyword}'. "
                        f"This appears to be a login, error, or navigation page. "
                        f"Please use a direct link to a specific job posting."
                    )
        
        # Check if company is same as title (common for login pages)
        if company and title and company == title and 'linkedin' in company:
            raise ValueError(
                "Invalid job posting - this appears to be a site navigation page, not a job posting. "
                "Please use a direct link to a specific job posting."
            )
        
        # Check for login-specific phrases in description (need multiple matches to be sure)
        login_phrases = [
            'user agreement', 'privacy policy', 'cookie policy',
            'forgot password', 'create account', 'sign in with',
            'enter your email', 'enter your password', 'reset password'
        ]
        
        login_phrase_count = sum(1 for phrase in login_phrases if phrase in description)
        if login_phrase_count >= 3:  # Raised threshold from 2 to 3
            raise ValueError(
                "This appears to be a login or authentication page, not a job posting. "
                "Please use the direct job posting URL instead of a collection or list page."
            )
        
        # LinkedIn-specific: Check URL structure (only check for obvious login forms)
        if 'linkedin.com' in html.lower():
            soup = BeautifulSoup(html, 'html.parser')
            
            # Only flag if we find BOTH email AND password inputs (clear login page)
            email_input = soup.find('input', {'type': 'email'}) or soup.find('input', {'name': re.compile(r'^(email|username)$', re.I)})
            password_input = soup.find('input', {'type': 'password'})
            login_button = soup.find('button', string=re.compile(r'sign in|log in', re.I))
            
            if email_input and password_input and login_button:
                raise ValueError(
                    "This LinkedIn URL requires login. "
                    "Please open the job in LinkedIn, then copy the direct job URL "
                    "(it should look like: linkedin.com/jobs/view/[job-id])"
                )
        
        # Only validate description length if it's extremely short (clearly not a job)
        if len(description) < 50:
            raise ValueError(
                "The job description is missing or extremely short. "
                "This may not be a valid job posting URL. "
                "Please use the direct link to a specific job posting."
            )
    
    def _extract_clean_text(self, html: str) -> str:
        """
        Extract clean text from HTML using BeautifulSoup.
        Removes scripts, styles, navigation, footers - keeps only content.
        This reduces token usage by ~90% compared to sending raw HTML.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            element.decompose()
        
        # Remove common noise classes/ids
        noise_selectors = [
            '[class*="cookie"]', '[class*="banner"]', '[class*="modal"]',
            '[class*="popup"]', '[class*="advertisement"]', '[id*="cookie"]',
            '[class*="navigation"]', '[class*="menu"]', '[class*="sidebar"]'
        ]
        for selector in noise_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Extract text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)
        
        # Limit to ~8000 chars (roughly 2000 tokens) to stay well under limits
        if len(clean_text) > 8000:
            clean_text = clean_text[:8000] + "..."
        
        return clean_text
    
    async def _extract_job_data(self, text: str, hint: dict | None = None) -> dict:
        """
        Use Azure OpenAI to extract structured job data from clean text.
        Organizes data into categories useful for CV tailoring.
        
        Args:
            text: Cleaned text from page
            hint: Optional partial data from structured metadata
        """
        hint_text = ""
        if hint:
            hint_text = f"\nPartial data found: {json.dumps(hint)}\nUse this as a starting point but extract full details from the text."
        
        prompt = f"""Extract and structure the job posting information from the following text.{hint_text}

Create a comprehensive job description organized into clear sections for CV tailoring.

Return a JSON object with these fields:
- title: Job title
- company: Company name
- description: A well-structured description with the following sections:

## About the Role
[Brief overview of the position]

## Key Responsibilities
- [Bullet point 1]
- [Bullet point 2]
...

## Required Qualifications
- [Must-have qualification 1]
- [Must-have qualification 2]
...

## Preferred Qualifications
- [Nice-to-have skill 1]
- [Nice-to-have skill 2]
...

## Technical Skills
- [Technical skill 1]
- [Technical skill 2]
...

Extract all relevant information and organize it properly. Be comprehensive - include ALL qualifications, requirements, and skills mentioned.

Text:
{text}

Return ONLY valid JSON with the structure: {{"title": "...", "company": "...", "description": "..."}}"""

        try:
            print(f"🤖 Calling Azure OpenAI with deployment: {self.deployment}")
            print(f"🔑 Endpoint configured: {settings.AZURE_OPENAI_ENDPOINT or '(empty)'}")
            print(f"🔑 API key configured: {'Yes' if settings.AZURE_OPENAI_KEY else 'No (empty)'}")
            
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from job postings. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result.startswith('```'):
                result = result.split('```')[1]
                if result.startswith('json'):
                    result = result[4:]
                result = result.strip()
            
            # Parse JSON
            job_data = json.loads(result)
            
            # Validate required fields
            if not all(key in job_data for key in ['title', 'company', 'description']):
                raise ValueError("Missing required fields in extracted data")
            
            return job_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse AI response as JSON: {e}")
            raise ValueError("Failed to extract job data: Invalid AI response format")
        except Exception as e:
            print(f"❌ Error extracting job data: {e}")
            raise ValueError(f"Failed to extract job data: {str(e)}")


# Singleton instance
job_scraper_service = JobScraperService()