#!/usr/bin/env python3
"""
TailorJob API Test Suite

This script tests all backend endpoints to verify they're working correctly.
Run after starting the backend server.

Usage:
    python test_api.py [TOKEN]

If TOKEN is not provided, will prompt for it.
"""

import sys
import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(name: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}📝 {name}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

def test_health():
    """Test the /health endpoint (no auth required)"""
    print_test("Testing /health endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to backend. Is it running on http://localhost:8000?")
        print_info("Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_list_cvs(token: str):
    """Test GET /api/cv/ endpoint"""
    print_test("Testing GET /api/cv/ (List CVs)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/cv/", headers=headers, timeout=5)
        
        if response.status_code == 200:
            cvs = response.json()
            print_success(f"Successfully retrieved CVs: {len(cvs)} found")
            if cvs:
                print_info(f"First CV: {json.dumps(cvs[0], indent=2)}")
            return True, cvs
        elif response.status_code == 401:
            print_error("Unauthorized. Check your token is valid.")
            return False, []
        else:
            print_error(f"Failed with status {response.status_code}: {response.text}")
            return False, []
    except Exception as e:
        print_error(f"Error: {e}")
        return False, []

def test_create_job(token: str) -> Optional[str]:
    """Test POST /api/jobs/ endpoint"""
    print_test("Testing POST /api/jobs/ (Create Job)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    job_data = {
        "title": "Senior Backend Engineer",
        "company": "TechTest Corp",
        "description": "We're looking for an experienced backend engineer with Python, FastAPI, and PostgreSQL skills.",
        "url": "https://example.com/jobs/test-123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/",
            headers=headers,
            json=job_data,
            timeout=5
        )
        
        if response.status_code == 200:
            job = response.json()
            print_success(f"Successfully created job with ID: {job['id']}")
            print_info(f"Job details:\n{json.dumps(job, indent=2)}")
            return job['id']
        else:
            print_error(f"Failed with status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None

def test_list_jobs(token: str):
    """Test GET /api/jobs/ endpoint"""
    print_test("Testing GET /api/jobs/ (List Jobs)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/jobs/", headers=headers, timeout=5)
        
        if response.status_code == 200:
            jobs = response.json()
            print_success(f"Successfully retrieved jobs: {len(jobs)} found")
            for i, job in enumerate(jobs[:3], 1):  # Show first 3
                print_info(f"Job {i}: {job['title']} at {job['company']}")
            return True, jobs
        else:
            print_error(f"Failed with status {response.status_code}: {response.text}")
            return False, []
    except Exception as e:
        print_error(f"Error: {e}")
        return False, []

def test_get_job(token: str, job_id: str):
    """Test GET /api/jobs/{id} endpoint"""
    print_test(f"Testing GET /api/jobs/{job_id} (Get Specific Job)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/jobs/{job_id}",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            job = response.json()
            print_success(f"Successfully retrieved job: {job['title']}")
            return True
        elif response.status_code == 404:
            print_error("Job not found")
            return False
        else:
            print_error(f"Failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_update_job(token: str, job_id: str):
    """Test PUT /api/jobs/{id} endpoint"""
    print_test(f"Testing PUT /api/jobs/{job_id} (Update Job)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    update_data = {
        "title": "Senior Backend Engineer (Updated)",
        "company": "TechTest Corp",
        "description": "Updated description with more details about the role.",
        "status": "active"
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/jobs/{job_id}",
            headers=headers,
            json=update_data,
            timeout=5
        )
        
        if response.status_code == 200:
            job = response.json()
            print_success(f"Successfully updated job: {job['title']}")
            return True
        else:
            print_error(f"Failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_upload_cv(token: str):
    """Test POST /api/cv/upload endpoint with dummy file"""
    print_test("Testing POST /api/cv/upload (Upload CV)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""
    
    files = {
        'file': ('test-cv.pdf', pdf_content, 'application/pdf')
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cv/upload",
            headers=headers,
            files=files,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Successfully uploaded CV: {result['filename']}")
            print_info(f"CV ID: {result['id']}")
            print_info(f"Status: {result['status']}")
            return True, result['id']
        else:
            print_error(f"Failed with status {response.status_code}: {response.text}")
            return False, None
    except Exception as e:
        print_error(f"Error: {e}")
        return False, None

def test_delete_job(token: str, job_id: str):
    """Test DELETE /api/jobs/{id} endpoint"""
    print_test(f"Testing DELETE /api/jobs/{job_id} (Delete Job)")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/jobs/{job_id}",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print_success("Successfully deleted job")
            return True
        else:
            print_error(f"Failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def get_token_instructions():
    """Print instructions for getting a token"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}How to get your JWT token:{Colors.END}\n")
    print("1. Open your frontend: http://localhost:5173")
    print("2. Sign in with Google")
    print("3. Open browser console (F12)")
    print("4. Run this command:")
    print(f"{Colors.GREEN}   const {{ data }} = await supabase.auth.getSession(){Colors.END}")
    print(f"{Colors.GREEN}   console.log(data.session.access_token){Colors.END}")
    print("5. Copy the token and paste it below")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}\n")

def main():
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  TailorJob API Test Suite")
    print("=" * 60)
    print(f"{Colors.END}")
    
    # Get token
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print(f"\n{Colors.GREEN}✓ Using token from command line{Colors.END}")
    else:
        get_token_instructions()
        token = input(f"{Colors.BOLD}Enter your JWT token: {Colors.END}").strip()
    
    if not token:
        print_error("No token provided. Exiting.")
        sys.exit(1)
    
    print(f"\n{Colors.BOLD}Starting tests...{Colors.END}")
    print(f"Base URL: {BASE_URL}")
    print(f"Token: {token[:20]}...")
    
    # Track results
    results = []
    
    # Test 1: Health check (no auth)
    results.append(("Health Check", test_health()))
    
    if not results[0][1]:
        print_error("\n❌ Backend is not running. Please start it first.")
        sys.exit(1)
    
    # Test 2: List CVs
    success, cvs = test_list_cvs(token)
    results.append(("List CVs", success))
    
    # Test 3: Create Job
    job_id = test_create_job(token)
    results.append(("Create Job", job_id is not None))
    
    # Test 4: List Jobs
    success, jobs = test_list_jobs(token)
    results.append(("List Jobs", success))
    
    # Test 5: Get specific job
    if job_id:
        results.append(("Get Job", test_get_job(token, job_id)))
    
    # Test 6: Update job
    if job_id:
        results.append(("Update Job", test_update_job(token, job_id)))
    
    # Test 7: Upload CV
    success, cv_id = test_upload_cv(token)
    results.append(("Upload CV", success))
    
    # Test 8: Delete job (cleanup)
    if job_id:
        results.append(("Delete Job", test_delete_job(token, job_id)))
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Test Results Summary:{Colors.END}\n")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if success else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Backend is working correctly.{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed. Check the output above for details.{Colors.END}")
    
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
        sys.exit(0)