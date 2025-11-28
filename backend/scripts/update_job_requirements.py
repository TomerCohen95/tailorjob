"""Update job in database with requirements_matrix from scraped data"""
import json
from app.utils.supabase_client import get_supabase

supabase = get_supabase()

# Load the Microsoft Security job from test data
with open('test_data/jobs.jsonl', 'r') as f:
    jobs = [json.loads(line) for line in f]

# Find the Microsoft Security job
security_job = next(j for j in jobs if 'Security for AI' in j['title'])

print(f"📋 Found job: {security_job['title']}")
print(f"   Job ID: {security_job['id']}")
print(f"   Requirements matrix: {len(security_job['requirements_matrix']['must_have'])} must-haves, {len(security_job['requirements_matrix']['nice_to_have'])} nice-to-haves")

# Find the job in database by ID (UUID format: 32bdf071-d870-400a-a55e-862bc125285b from logs)
# Or by title if ID doesn't match
try:
    # Try by title containing key words
    result = supabase.table('jobs').select('*').ilike('title', '%Security for AI%').execute()
    
    if not result.data or len(result.data) == 0:
        print("❌ Job not found in database by title")
        print(f"   Searching for title containing: 'Security for AI'")
        print(f"\n🔍 Listing all jobs in database:")
        all_jobs = supabase.table('jobs').select('id, title, url').execute()
        for job in all_jobs.data[:10]:
            print(f"   • {job['title'][:60]}... (ID: {job['id']})")
        exit(1)
    
    db_job = result.data[0]
    print(f"\n✅ Found job in database:")
    print(f"   Database ID: {db_job['id']}")
    print(f"   Title: {db_job['title']}")
    print(f"   Has requirements_matrix: {'requirements_matrix' in db_job and db_job['requirements_matrix'] is not None}")
    
    # Update the job with requirements matrix
    update_data = {
        'requirements_matrix': security_job['requirements_matrix']
    }
    
    supabase.table('jobs').update(update_data).eq('id', db_job['id']).execute()
    
    print(f"\n✅ Updated job with requirements matrix")
    print(f"   Must-have requirements: {security_job['requirements_matrix']['must_have']}")
    print(f"   Nice-to-have requirements: {security_job['requirements_matrix']['nice_to_have']}")
    
except Exception as e:
    print(f"❌ Error updating job: {e}")
    import traceback
    traceback.print_exc()