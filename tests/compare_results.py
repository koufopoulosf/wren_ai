"""
Compare Evaluation Results

Compares performance metrics between two evaluation runs (e.g., baseline vs improved).

Usage:
    python tests/compare_results.py baseline_20241115_120000.json phase1_20241115_130000.json
"""

import json
import sys
from pathlib import Path


def compare_results(baseline_file: str, improved_file: str):
    """
    Compare two result files.

    Args:
        baseline_file: Path to baseline results JSON
        improved_file: Path to improved results JSON
    """
    # Load results
    with open(baseline_file, 'r') as f:
        baseline = json.load(f)

    with open(improved_file, 'r') as f:
        improved = json.load(f)

    # Print comparison
    print("="*70)
    print("📊 PERFORMANCE COMPARISON")
    print("="*70)
    print(f"Baseline: {Path(baseline_file).name}")
    print(f"Improved: {Path(improved_file).name}")
    print("="*70)

    # Metrics to compare
    metrics = [
        ('Success Rate', 'success_rate', '%'),
        ('SQL Generation', 'sql_generation_rate', '%'),
        ('Validation Rate', 'validation_rate', '%'),
        ('Execution Rate', 'execution_rate', '%'),
        ('Avg Execution Time', 'avg_execution_time', 's')
    ]

    for label, key, unit in metrics:
        baseline_val = baseline.get(key, 0)
        improved_val = improved.get(key, 0)

        if unit == '%':
            baseline_val *= 100
            improved_val *= 100
            diff = improved_val - baseline_val
            symbol = "📈" if diff > 0 else ("📉" if diff < 0 else "➡️")
            print(f"{label:20s}: {baseline_val:6.1f}% → {improved_val:6.1f}% ({symbol} {diff:+.1f}%)")
        else:
            diff = improved_val - baseline_val
            symbol = "📉" if diff < 0 else ("📈" if diff > 0 else "➡️")  # For time, lower is better
            print(f"{label:20s}: {baseline_val:6.2f}{unit} → {improved_val:6.2f}{unit} ({symbol} {diff:+.2f}{unit})")

    print("="*70)

    # Difficulty-based comparison
    baseline_results = baseline.get('results', [])
    improved_results = improved.get('results', [])

    if baseline_results and improved_results:
        print("\n📈 Performance by Difficulty:")
        print("-"*70)

        # Group by difficulty
        for difficulty in ['easy', 'medium', 'hard']:
            baseline_diff = [r for r in baseline_results if r.get('difficulty') == difficulty]
            improved_diff = [r for r in improved_results if r.get('difficulty') == difficulty]

            if not baseline_diff:
                continue

            baseline_success = sum(1 for r in baseline_diff if r['success'])
            improved_success = sum(1 for r in improved_diff if r['success'])

            baseline_rate = baseline_success / len(baseline_diff) * 100
            improved_rate = improved_success / len(improved_diff) * 100 if improved_diff else 0

            diff = improved_rate - baseline_rate
            symbol = "📈" if diff > 0 else ("📉" if diff < 0 else "➡️")

            print(f"{difficulty.capitalize():10s}: {baseline_rate:5.1f}% → {improved_rate:5.1f}% ({symbol} {diff:+.1f}%)")

        print("="*70)

    # New successes
    if baseline_results and improved_results:
        baseline_failed_ids = {r['id'] for r in baseline_results if not r['success']}
        improved_success_ids = {r['id'] for r in improved_results if r['success']}

        newly_fixed = baseline_failed_ids & improved_success_ids

        if newly_fixed:
            print(f"\n✅ Newly Fixed Queries ({len(newly_fixed)}):")
            for query_id in sorted(newly_fixed):
                # Find the query
                for r in improved_results:
                    if r['id'] == query_id:
                        print(f"  [{query_id}] {r['question'][:60]}...")
                        break

        # New failures
        baseline_success_ids = {r['id'] for r in baseline_results if r['success']}
        improved_failed_ids = {r['id'] for r in improved_results if not r['success']}

        newly_broken = baseline_success_ids & improved_failed_ids

        if newly_broken:
            print(f"\n❌ Newly Failed Queries ({len(newly_broken)}):")
            for query_id in sorted(newly_broken):
                # Find the query
                for r in improved_results:
                    if r['id'] == query_id:
                        print(f"  [{query_id}] {r['question'][:60]}...")
                        print(f"       Error: {r.get('error', 'Unknown')[:80]}")
                        break

        print("="*70)

    # Summary
    success_improvement = (improved['success_rate'] - baseline['success_rate']) * 100

    print(f"\n🎯 Overall Improvement: {success_improvement:+.1f}%")

    if success_improvement >= 10:
        print("🌟 Excellent improvement!")
    elif success_improvement >= 5:
        print("👍 Good improvement")
    elif success_improvement > 0:
        print("📈 Some improvement")
    elif success_improvement == 0:
        print("➡️  No change")
    else:
        print("⚠️  Performance degraded")

    print()


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python compare_results.py <baseline.json> <improved.json>")
        print("\nExample:")
        print("  python compare_results.py tests/results/baseline_*.json tests/results/phase1_*.json")
        sys.exit(1)

    baseline_file = sys.argv[1]
    improved_file = sys.argv[2]

    # Check files exist
    if not Path(baseline_file).exists():
        print(f"❌ Baseline file not found: {baseline_file}")
        sys.exit(1)

    if not Path(improved_file).exists():
        print(f"❌ Improved file not found: {improved_file}")
        sys.exit(1)

    compare_results(baseline_file, improved_file)


if __name__ == "__main__":
    main()
