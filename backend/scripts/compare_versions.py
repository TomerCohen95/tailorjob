#!/usr/bin/env python3
"""
CV Matcher Version Comparator

Compares two test result files to show improvements/regressions
between matcher versions.

Usage:
    python compare_versions.py --baseline test_results/v1.0_review.jsonl --current test_results/v1.1_review.jsonl
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


def load_results(file_path: str) -> Dict[str, Dict]:
    """Load test results from JSONL file"""
    results = {}
    with open(file_path) as f:
        for line in f:
            if line.strip():
                try:
                    test = json.loads(line)
                    if 'test_id' in test and 'match_result' in test:
                        results[test['test_id']] = test
                except json.JSONDecodeError:
                    continue
    return results


def compare_versions(baseline_file: str, current_file: str) -> None:
    """Compare two test result files"""
    
    # Load results
    print(f"📂 Loading baseline: {baseline_file}")
    baseline = load_results(baseline_file)
    
    print(f"📂 Loading current: {current_file}")
    current = load_results(current_file)
    
    if not baseline:
        print(f"❌ Error: No valid results in baseline file")
        sys.exit(1)
    
    if not current:
        print(f"❌ Error: No valid results in current file")
        sys.exit(1)
    
    # Find common tests
    common_tests = set(baseline.keys()) & set(current.keys())
    
    if not common_tests:
        print(f"❌ Error: No common tests between files")
        sys.exit(1)
    
    print(f"✓ Found {len(common_tests)} common tests")
    print()
    
    # Extract versions
    baseline_version = list(baseline.values())[0].get('matcher_version', 'unknown')
    current_version = list(current.values())[0].get('matcher_version', 'unknown')
    
    # Compare scores
    improvements = []
    regressions = []
    unchanged = []
    
    for test_id in sorted(common_tests):
        base_score = baseline[test_id]['match_result']['overall_score']
        curr_score = current[test_id]['match_result']['overall_score']
        diff = curr_score - base_score
        
        if diff > 0:
            improvements.append((test_id, base_score, curr_score, diff))
        elif diff < 0:
            regressions.append((test_id, base_score, curr_score, diff))
        else:
            unchanged.append((test_id, base_score, curr_score, diff))
    
    # Calculate averages
    baseline_avg = sum(baseline[tid]['match_result']['overall_score'] for tid in common_tests) / len(common_tests)
    current_avg = sum(current[tid]['match_result']['overall_score'] for tid in common_tests) / len(common_tests)
    avg_change = current_avg - baseline_avg
    
    # Print comparison report
    print("=" * 70)
    print(f"Version Comparison: {baseline_version} → {current_version}")
    print("=" * 70)
    print()
    
    print("📊 Summary:")
    print(f"  Total tests: {len(common_tests)}")
    print(f"  ✓ Improved: {len(improvements)} ({len(improvements)/len(common_tests)*100:.1f}%)")
    print(f"  ✗ Regressed: {len(regressions)} ({len(regressions)/len(common_tests)*100:.1f}%)")
    print(f"  = Unchanged: {len(unchanged)} ({len(unchanged)/len(common_tests)*100:.1f}%)")
    print()
    print(f"  Average score:")
    print(f"    {baseline_version}: {baseline_avg:.1f}%")
    print(f"    {current_version}: {current_avg:.1f}%")
    
    change_indicator = "↑" if avg_change > 0 else "↓" if avg_change < 0 else "="
    print(f"    Change: {change_indicator} {abs(avg_change):.1f}%")
    print()
    
    # Show significant improvements
    if improvements:
        significant = [imp for imp in improvements if imp[3] >= 10]
        if significant:
            print(f"🎯 Significant Improvements (≥10%):")
            for test_id, base, curr, diff in sorted(significant, key=lambda x: -x[3])[:10]:
                cv_name = test_id.split('_')[0]
                print(f"  {test_id}")
                print(f"    {cv_name}: {base}% → {curr}% (↑{diff}%)")
            print()
    
    # Show significant regressions
    if regressions:
        significant = [reg for reg in regressions if abs(reg[3]) >= 10]
        if significant:
            print(f"⚠️  Significant Regressions (≥10%):")
            for test_id, base, curr, diff in sorted(significant, key=lambda x: x[3])[:10]:
                cv_name = test_id.split('_')[0]
                print(f"  {test_id}")
                print(f"    {cv_name}: {base}% → {curr}% (↓{abs(diff)}%)")
            print()
    
    # Score distribution comparison
    def get_distribution(results, test_ids):
        dist = defaultdict(int)
        for tid in test_ids:
            score = results[tid]['match_result']['overall_score']
            bucket = (score // 20) * 20  # 0-19, 20-39, 40-59, 60-79, 80-100
            dist[bucket] += 1
        return dist
    
    base_dist = get_distribution(baseline, common_tests)
    curr_dist = get_distribution(current, common_tests)
    
    print("📈 Score Distribution:")
    print()
    print(f"{'Range':<12} {baseline_version:<15} {current_version:<15} {'Change':<10}")
    print("-" * 60)
    for bucket in [0, 20, 40, 60, 80]:
        base_count = base_dist.get(bucket, 0)
        curr_count = curr_dist.get(bucket, 0)
        change = curr_count - base_count
        change_str = f"{'↑' if change > 0 else '↓' if change < 0 else '='}{abs(change)}"
        
        range_label = f"{bucket}-{bucket+19}%"
        if bucket == 80:
            range_label = "80-100%"
        
        print(f"{range_label:<12} {base_count:<15} {curr_count:<15} {change_str:<10}")
    
    print()
    print("=" * 70)
    
    # Recommendations
    print()
    print("💡 Recommendations:")
    if avg_change > 5:
        print("  ✅ Great improvement! Version shows clear quality gains.")
    elif avg_change > 0:
        print("  ✓ Modest improvement. Consider further refinements.")
    elif avg_change < -5:
        print("  ⚠️  Significant regression detected. Review changes carefully.")
    elif avg_change < 0:
        print("  ⚠️  Slight regression. May need adjustment.")
    else:
        print("  = No significant change. Try different improvements.")
    
    if regressions:
        print(f"  📋 Review {len(regressions)} regressed cases for unintended side effects.")


def main():
    """Parse arguments and compare versions"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Compare two CV matcher test result files'
    )
    parser.add_argument(
        '--baseline',
        required=True,
        help='Path to baseline results file (earlier version)'
    )
    parser.add_argument(
        '--current',
        required=True,
        help='Path to current results file (newer version)'
    )
    
    args = parser.parse_args()
    
    # Check files exist
    if not Path(args.baseline).exists():
        print(f"❌ Error: Baseline file not found: {args.baseline}")
        sys.exit(1)
    
    if not Path(args.current).exists():
        print(f"❌ Error: Current file not found: {args.current}")
        sys.exit(1)
    
    # Compare
    compare_versions(args.baseline, args.current)


if __name__ == '__main__':
    main()