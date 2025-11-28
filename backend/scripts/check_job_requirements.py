#!/usr/bin/env python3
"""Check what requirements_matrix was extracted for a job"""
import sys
from app.utils.supabase_client import supabase
import json

job_id = "7e7c8c32-5355-4a4f-9b17-e57ffc2ebff9"

result = supabase.table('jobs').select('id, title, requirements_matrix').eq('id', job_id).single().execute()

if result.data:
    print(f"Job: {result.data['title']}\n")
    print("="*60)
    
    matrix = result.data.get('requirements_matrix')
    if matrix:
        print("\nMUST-HAVE Requirements:")
        for req in matrix.get('must_have', []):
            print(f"  - {req}")
        
        print("\nNICE-TO-HAVE Requirements:")
        for req in matrix.get('nice_to_have', []):
            print(f"  - {req}")
    else:
        print("No requirements_matrix found")
else:
    print("Job not found")