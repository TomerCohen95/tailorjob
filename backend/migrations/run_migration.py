#!/usr/bin/env python3
"""
Run database migration to add requirements_matrix column.
This script uses the existing Supabase connection to execute SQL directly.
"""
import sys
from app.utils.supabase_client import supabase

def run_migration():
    """Execute the migration SQL"""
    
    migration_sql = """
    -- Add requirements_matrix column to jobs table
    ALTER TABLE jobs 
    ADD COLUMN IF NOT EXISTS requirements_matrix JSONB;
    
    -- Create GIN index for efficient JSONB queries
    CREATE INDEX IF NOT EXISTS idx_jobs_requirements_matrix 
    ON jobs USING GIN (requirements_matrix);
    """
    
    print("🔄 Running migration to add requirements_matrix column...")
    
    try:
        # Execute the SQL
        result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
        print("✅ Migration completed successfully!")
        
        # Verify the column exists
        verify_sql = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'jobs' 
        AND column_name = 'requirements_matrix';
        """
        
        verify_result = supabase.rpc('exec_sql', {'sql': verify_sql}).execute()
        
        if verify_result.data:
            print("✅ Column 'requirements_matrix' verified in jobs table")
            print(f"   Type: {verify_result.data[0].get('data_type', 'jsonb')}")
        else:
            print("⚠️ Could not verify column - it may still exist")
            
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        # Check if it's just because exec_sql function doesn't exist
        if 'function' in error_msg.lower() and 'exec_sql' in error_msg.lower():
            print("⚠️ Cannot run migration programmatically (exec_sql function not available)")
            print("\n📋 Please run this SQL manually in Supabase SQL Editor:")
            print("-" * 60)
            print(migration_sql)
            print("-" * 60)
            print("\n🔗 Go to: https://supabase.com/dashboard → SQL Editor")
            return False
        else:
            print(f"❌ Migration failed: {e}")
            return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)