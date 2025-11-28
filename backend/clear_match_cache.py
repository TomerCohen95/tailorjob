"""Clear all cached match scores to force re-analysis with new matcher"""
from app.utils.supabase_client import get_supabase

supabase = get_supabase()

# Delete all cached matches by selecting all and deleting
try:
    # First, get all matches
    all_matches = supabase.table('cv_job_matches').select('id').execute()
    
    if all_matches.data and len(all_matches.data) > 0:
        # Delete each one
        for match in all_matches.data:
            supabase.table('cv_job_matches').delete().eq('id', match['id']).execute()
        
        print(f"✅ Cleared {len(all_matches.data)} cached match scores")
        print("All future match requests will use the new v2.3 matcher")
        print("\n📋 v2.3 Improvements:")
        print("  • Category-based scoring (Skills/Experience/Qualifications calculated separately)")
        print("  • Enhanced evidence with specific CV references (roles, companies, years)")
        print("  • More detailed and actionable match analysis")
    else:
        print("ℹ️  No cached matches found")
        
except Exception as e:
    print(f"❌ Error clearing cache: {e}")
