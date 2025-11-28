#!/usr/bin/env python3
"""
CV Matcher Batch Tester

Tests multiple CVs against multiple job descriptions using existing
cv_parser_service and cv_matcher_service. Exports results to JSONL
format for evaluation by CV Judge mode.

Usage:
    python test_matcher.py --cvs test_data/cvs --jobs test_data/jobs.jsonl --output test_results/review.jsonl
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

# Import existing services
from app.services.cv_parser import cv_parser_service
from app.services.cv_matcher import cv_matcher_service


async def parse_cv_from_file(cv_path: Path) -> Optional[Dict[str, Any]]:
    """
    Parse a CV PDF file using existing cv_parser_service
    
    Args:
        cv_path: Path to CV PDF file
        
    Returns:
        Parsed CV data or None if parsing fails
    """
    try:
        print(f"  📄 Parsing {cv_path.name}...")
        
        # Read PDF file
        with open(cv_path, 'rb') as f:
            file_content = f.read()
        
        # Extract text from PDF
        cv_text = cv_parser_service.extract_text_from_pdf(file_content)
        
        # Parse CV text with AI
        cv_data = await cv_parser_service.parse_cv_text(cv_text)
        
        print(f"     ✓ Parsed successfully")
        return cv_data
        
    except Exception as e:
        print(f"     ✗ Failed to parse: {e}")
        return None


async def run_matcher_tests(
    cvs_folder: str,
    jobs_file: str,
    output_file: str,
    version: str = "1.0",
    resume_from: Optional[str] = None
) -> None:
    """
    Run CV matcher against all CV×Job combinations
    
    Args:
        cvs_folder: Path to folder containing CV PDF files
        jobs_file: Path to JSONL file containing scraped jobs
        output_file: Path to output JSONL file for results
        version: Matcher version tag for tracking improvements
        resume_from: Path to existing results file to resume from
    """
    start_time = time.time()
    
    # Load CVs
    cvs_path = Path(cvs_folder)
    if not cvs_path.exists():
        print(f"❌ Error: CVs folder not found: {cvs_folder}")
        sys.exit(1)
    
    cv_files = sorted(cvs_path.glob('*.pdf'))
    if not cv_files:
        print(f"❌ Error: No PDF files found in {cvs_folder}")
        sys.exit(1)
    
    print(f"📋 Found {len(cv_files)} CV files")
    print()
    
    # Parse all CVs
    print("🔍 Parsing CVs...")
    cvs = []
    for cv_file in cv_files:
        cv_data = await parse_cv_from_file(cv_file)
        if cv_data:
            cvs.append({
                'identifier': cv_file.name,
                'file_path': str(cv_file),
                'parsed_data': cv_data
            })
    
    if not cvs:
        print(f"❌ Error: No CVs could be parsed successfully")
        sys.exit(1)
    
    print()
    print(f"✅ Successfully parsed {len(cvs)}/{len(cv_files)} CVs")
    print()
    
    # Load jobs
    jobs_path = Path(jobs_file)
    if not jobs_path.exists():
        print(f"❌ Error: Jobs file not found: {jobs_file}")
        sys.exit(1)
    
    jobs = []
    with open(jobs_path) as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    job = json.loads(line)
                    jobs.append(job)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Warning: Invalid JSON on line {line_num}: {e}")
    
    if not jobs:
        print(f"❌ Error: No valid jobs found in {jobs_file}")
        sys.exit(1)
    
    print(f"📋 Loaded {len(jobs)} jobs")
    print()
    
    # Check for existing results to resume from
    completed_tests = set()
    if resume_from and Path(resume_from).exists():
        print(f"📂 Loading existing results from {resume_from}")
        with open(resume_from) as f:
            for line in f:
                if line.strip():
                    try:
                        result = json.loads(line)
                        completed_tests.add(result['test_id'])
                    except json.JSONDecodeError:
                        continue
        if completed_tests:
            print(f"✓ Found {len(completed_tests)} completed tests")
            print()
    
    # Calculate total tests
    total_tests = len(cvs) * len(jobs)
    tests_to_run = total_tests - len(completed_tests)
    
    print("=" * 60)
    print(f"Test Configuration:")
    print(f"  CVs: {len(cvs)}")
    print(f"  Jobs: {len(jobs)}")
    print(f"  Total combinations: {total_tests}")
    if completed_tests:
        print(f"  Already completed: {len(completed_tests)}")
        print(f"  Remaining: {tests_to_run}")
    print(f"  Matcher version: {version}")
    print("=" * 60)
    print()
    
    if tests_to_run == 0:
        print("✅ All tests already completed!")
        return
    
    # Run tests
    print(f"🎯 Running {tests_to_run} matcher tests...")
    print()
    
    # Prepare output file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Open output file in append mode
    results_count = 0
    errors_count = 0
    
    with open(output_path, 'a', encoding='utf-8') as out_f:
        test_num = 0
        for cv in cvs:
            for job in jobs:
                test_num += 1
                
                # Generate test ID
                cv_id = cv['identifier'].replace('.pdf', '').replace(' ', '_')
                job_id = job.get('id', f"job-{test_num}")
                test_id = f"{cv_id}_{job_id}"
                
                # Skip if already completed
                if test_id in completed_tests:
                    continue
                
                try:
                    # Progress indicator
                    progress = (test_num / total_tests) * 100
                    print(f"[{test_num}/{total_tests}] ({progress:.1f}%) Testing:")
                    print(f"  CV: {cv['identifier']}")
                    print(f"  Job: {job.get('title', 'Unknown')} @ {job.get('company', 'Unknown')}")
                    
                    # Run matcher using existing service
                    match_start = time.time()
                    match_result = await cv_matcher_service.analyze_match(
                        cv_data=cv['parsed_data'],
                        job_data=job
                    )
                    match_time = int((time.time() - match_start) * 1000)
                    
                    # Build complete test case
                    test_case = {
                        'test_id': test_id,
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'matcher_version': version,
                        'cv': {
                            'identifier': cv['identifier'],
                            'file_path': cv['file_path'],
                            'parsed_data': cv['parsed_data']
                        },
                        'job': job,
                        'match_result': match_result,
                        'metadata': {
                            'execution_time_ms': match_time,
                            'model': 'gpt-4',
                            'temperature': 0
                        }
                    }
                    
                    # Write to output file immediately
                    out_f.write(json.dumps(test_case, ensure_ascii=False) + '\n')
                    out_f.flush()  # Ensure it's written
                    
                    results_count += 1
                    
                    # Show result
                    score = match_result.get('overall_score', 0)
                    print(f"  ✓ Match score: {score}% (took {match_time}ms)")
                    print()
                    
                except Exception as e:
                    errors_count += 1
                    print(f"  ✗ Error: {e}")
                    print()
                    
                    # Log error but continue
                    error_entry = {
                        'test_id': test_id,
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'error': str(e),
                        'cv_identifier': cv['identifier'],
                        'job_id': job.get('id', 'unknown')
                    }
                    out_f.write(json.dumps(error_entry, ensure_ascii=False) + '\n')
                    out_f.flush()
    
    # Calculate execution time
    total_time = time.time() - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    # Summary
    print()
    print("=" * 60)
    print("Test Results Summary:")
    print(f"  ✓ Successful: {results_count}")
    print(f"  ✗ Failed: {errors_count}")
    print(f"  Success rate: {results_count/(results_count+errors_count)*100:.1f}%")
    print(f"  Total time: {minutes}m {seconds}s")
    print(f"  Output saved to: {output_file}")
    print("=" * 60)
    
    # Show next steps
    print()
    print("📊 Next Steps:")
    print("  1. Review results file:")
    print(f"     cat {output_file} | jq '.match_result.overall_score'")
    print()
    print("  2. Switch to CV Judge mode to evaluate results:")
    print("     Switch to '🔍 CV Matcher Judge' mode")
    print(f"     Open file: {output_file}")
    print()
    print("  3. Or view in human-readable format:")
    print(f"     cat {output_file} | jq -r '.cv.identifier + \" × \" + .job.title + \": \" + (.match_result.overall_score|tostring) + \"%\"'")


def main():
    """Parse arguments and run tests"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run CV matcher tests for all CV×Job combinations'
    )
    parser.add_argument(
        '--cvs',
        required=True,
        help='Path to folder containing CV PDF files'
    )
    parser.add_argument(
        '--jobs',
        required=True,
        help='Path to JSONL file containing scraped jobs'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to output JSONL file for results'
    )
    parser.add_argument(
        '--version',
        default='1.0',
        help='Matcher version tag (default: 1.0)'
    )
    parser.add_argument(
        '--resume',
        help='Resume from existing results file (skip completed tests)'
    )
    
    args = parser.parse_args()
    
    # Run tests
    asyncio.run(run_matcher_tests(
        cvs_folder=args.cvs,
        jobs_file=args.jobs,
        output_file=args.output,
        version=args.version,
        resume_from=args.resume
    ))


if __name__ == '__main__':
    main()