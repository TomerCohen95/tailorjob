# Apply CV Primary Flag Migration

## Steps to Apply Migration

1. **Go to Supabase Dashboard**
   - Navigate to your project at https://supabase.com/dashboard
   - Go to the SQL Editor section

2. **Run the Migration SQL**
   - Copy the contents of `supabase/migrations/20251124000000_add_cv_primary_flag.sql`
   - Paste into the SQL Editor
   - Click "Run" to execute

3. **Verify Migration**
   Run this query to check if the column was added:
   ```sql
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'cvs' AND column_name = 'is_primary';
   ```

4. **Restart Backend Server**
   ```bash
   cd backend
   # Stop the running server (Ctrl+C)
   # Start it again
   uvicorn app.main:app --reload --port 8000
   ```

5. **Test the Feature**
   - Go to the Dashboard
   - Click "View history" if you have multiple CVs
   - Click "Set as Primary" on any CV
   - The selected CV should show "Active" badge

## What This Migration Does

- Adds `is_primary` boolean column to the `cvs` table
- Creates a database trigger that ensures only one CV can be primary per user
- Automatically sets the most recent CV as primary for existing users
- Creates an index for better query performance

## Troubleshooting

If you get errors about the column already existing:
```sql
-- Check if column exists
SELECT * FROM information_schema.columns 
WHERE table_name = 'cvs' AND column_name = 'is_primary';

-- If it exists but trigger doesn't, run just the trigger part from the migration