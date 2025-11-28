# How to Apply requirements_matrix Migration

## Quick Instructions

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Select your project
   - Click "SQL Editor" in the left sidebar

2. **Run This SQL**
   ```sql
   -- Add requirements_matrix column to jobs table
   ALTER TABLE jobs 
   ADD COLUMN IF NOT EXISTS requirements_matrix JSONB;
   
   -- Create GIN index for efficient JSONB queries
   CREATE INDEX IF NOT EXISTS idx_jobs_requirements_matrix 
   ON jobs USING GIN (requirements_matrix);
   ```

3. **Verify It Worked**
   ```sql
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'jobs' 
   AND column_name = 'requirements_matrix';
   ```
   
   You should see:
   ```
   column_name          | data_type
   ---------------------|----------
   requirements_matrix  | jsonb
   ```

## Test v2.4 Detailed Recommendations

After migration:

1. **Delete existing job** (it doesn't have requirements_matrix populated)
2. **Re-add the job** by pasting the URL
3. **Click "Re-analyze Match"**
4. **See detailed recommendations** like:
   - "Add 'AI Security' to your Skills section under Security Technologies"
   - "In your Security Researcher role, add a bullet about ML model security testing"
   - "Rewrite your Professional Summary to emphasize 8+ years in cyber security R&D"

## Why This Is Needed

The `requirements_matrix` column:
- Stores structured job requirements (must_have/nice_to_have)
- Enables v2.3+ deterministic scoring
- Powers v2.4 detailed AI recommendations
- Required for automatic CV tailoring features

## Files Involved

- **Migration SQL**: `backend/apply_requirements_matrix_migration.sql`
- **Supabase Migration**: `supabase/migrations/20251127000000_add_requirements_matrix.sql`
- **Scraper Fix**: `backend/app/api/routes/jobs.py` (line 150)
- **Matcher v2.4**: `backend/app/services/cv_matcher.py` (line 594)

## Troubleshooting

### "Column already exists"
That's fine! The SQL uses `IF NOT EXISTS` so it's safe to run multiple times.

### "Still showing legacy matching"
The job in your database was created before the column existed. Delete and re-add it.

### "Still generic recommendations"
Clear the match cache:
```bash
cd backend
source venv/bin/activate
python clear_match_cache.py
```

## Alternative: Use Supabase CLI

If you prefer command line (won't work if migrations are out of sync):
```bash
cd supabase
npx supabase db push
```

## What Happens Next

Once the column exists:
1. New jobs scraped will have `requirements_matrix` populated
2. CV matcher will use v2.3+ structured matching
3. Recommendations will be detailed and actionable (v2.4)
4. You can use these for automatic CV tailoring