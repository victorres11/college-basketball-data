#!/usr/bin/env python3
"""
Validate all 365 teams against sports-reference.com.

This script tests that every team in the registry has a valid sports-reference slug.

Usage:
    python scripts/validate_sports_ref_all_teams.py

Output:
    - Console progress updates
    - JSON report saved to scripts/validation_reports/sports_ref_validation.json
"""

import json
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_team_registry() -> dict:
    """Load the team registry JSON file."""
    registry_path = project_root / 'config' / 'team_registry.json'
    with open(registry_path) as f:
        return json.load(f)


def validate_team(team_id: str, team_data: dict) -> tuple[bool, str, str]:
    """
    Validate a single team against sports-reference.com.

    Args:
        team_id: CBB API team ID
        team_data: Team data from registry

    Returns:
        Tuple of (success, sports_ref_slug, error_message)
    """
    sports_ref_slug = team_data.get('services', {}).get('sports_reference')

    if not sports_ref_slug:
        return False, None, "No sports_reference mapping in registry"

    # Sports Reference team page URL
    url = f"https://www.sports-reference.com/cbb/schools/{sports_ref_slug}/men/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)

        if response.status_code == 200:
            # Check if we got a valid team page (not a 404 page with 200 status)
            if 'Page Not Found' in response.text or 'not found' in response.text.lower()[:500]:
                return False, sports_ref_slug, "Page exists but shows 'not found'"
            return True, sports_ref_slug, None
        elif response.status_code == 404:
            return False, sports_ref_slug, "Team page not found (404)"
        elif response.status_code == 429:
            return False, sports_ref_slug, "Rate limited (429) - try again later"
        else:
            return False, sports_ref_slug, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, sports_ref_slug, "Request timed out"
    except requests.exceptions.RequestException as e:
        return False, sports_ref_slug, str(e)


def run_validation(delay: float = 1.0, start: int = 0, limit: int = None) -> dict:
    """
    Run validation for all teams in registry.

    Args:
        delay: Seconds to wait between requests (sports-reference has strict rate limits)
        start: Starting index for batch processing (0-based)
        limit: Number of teams to validate (None = all remaining)

    Returns:
        Validation report dictionary
    """
    registry = load_team_registry()
    all_teams = list(registry.get('teams', {}).items())
    total_all = len(all_teams)

    # Apply batch slicing
    end = start + limit if limit else total_all
    teams_to_validate = all_teams[start:end]
    total = len(teams_to_validate)

    print(f"\n🏀 sports-reference.com Validation")
    print(f"   Batch: {start+1} to {start+total} of {total_all} teams")
    print(f"   Delay: {delay}s between calls (sports-ref has strict rate limits)")
    print("=" * 50)

    successes = []
    failures = []
    skipped = []

    for i, (team_id, team_data) in enumerate(teams_to_validate, 1):
        canonical_name = team_data.get('canonical_name', 'Unknown')

        # Check if team has sports_reference mapping
        sports_ref_slug = team_data.get('services', {}).get('sports_reference')
        if not sports_ref_slug:
            skipped.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'reason': 'No sports_reference mapping in registry'
            })
            print(f"[{i:3d}/{total}] ⏭️  {canonical_name} - No sports_reference mapping")
            continue

        # Test sports-reference lookup
        success, slug_used, error = validate_team(team_id, team_data)

        if success:
            successes.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'sports_ref_slug': slug_used
            })
            print(f"[{i:3d}/{total}] ✅ {canonical_name}")
        else:
            failures.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'sports_ref_slug': slug_used,
                'error': error
            })
            print(f"[{i:3d}/{total}] ❌ {canonical_name} - {error}")

        # Rate limiting - sports-reference is strict
        if i < total:
            time.sleep(delay)

    # Build report
    tested = total - len(skipped)
    report = {
        'service': 'sports_reference',
        'timestamp': datetime.now().isoformat(),
        'batch_start': start,
        'batch_size': total,
        'total_teams_in_registry': total_all,
        'successes': len(successes),
        'failures': len(failures),
        'skipped': len(skipped),
        'success_rate': f"{len(successes) / tested * 100:.1f}%" if tested > 0 else "N/A",
        'failed_teams': failures,
        'skipped_teams': skipped,
        'successful_teams': successes
    }

    return report


def save_report(report: dict) -> Path:
    """Save validation report to JSON file."""
    reports_dir = project_root / 'scripts' / 'validation_reports'
    reports_dir.mkdir(exist_ok=True)

    # Use batch-specific filename if this is a batch run
    start = report.get('batch_start', 0)
    size = report.get('batch_size', 0)
    if start > 0 or size < report.get('total_teams_in_registry', 365):
        filename = f'sports_ref_validation_batch_{start}_{start+size}.json'
    else:
        filename = 'sports_ref_validation.json'

    report_path = reports_dir / filename
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report_path


def print_summary(report: dict):
    """Print validation summary."""
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    start = report.get('batch_start', 0)
    size = report.get('batch_size', 0)
    total_all = report.get('total_teams_in_registry', size)
    print(f"   Batch:           {start+1} to {start+size} of {total_all}")
    print(f"   ✅ Successes:    {report['successes']}")
    print(f"   ❌ Failures:     {report['failures']}")
    print(f"   ⏭️  Skipped:      {report['skipped']}")
    print(f"   Success rate:    {report['success_rate']}")

    if report['failed_teams']:
        print("\n❌ FAILED TEAMS:")
        print("-" * 50)
        for team in report['failed_teams']:
            print(f"   [{team['team_id']:3d}] {team['name']}")
            print(f"         Slug: {team['sports_ref_slug']}")
            print(f"         Error: {team['error']}")

    if report['skipped_teams']:
        print(f"\n⏭️  SKIPPED TEAMS ({len(report['skipped_teams'])}):")
        print("-" * 50)
        for team in report['skipped_teams'][:10]:
            print(f"   [{team['team_id']:3d}] {team['name']} - {team['reason']}")
        if len(report['skipped_teams']) > 10:
            print(f"   ... and {len(report['skipped_teams']) - 10} more")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate all teams against sports-reference.com')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between requests in seconds (default: 1.0, sports-ref has strict limits)')
    parser.add_argument('--start', type=int, default=0,
                        help='Start index (0-based) for batch processing')
    parser.add_argument('--limit', type=int, default=None,
                        help='Number of teams to validate (default: all)')
    parser.add_argument('--no-save', action='store_true',
                        help='Skip saving report to file')

    args = parser.parse_args()

    # Run validation
    start_time = time.time()
    report = run_validation(delay=args.delay, start=args.start, limit=args.limit)
    elapsed = time.time() - start_time

    # Add timing to report
    report['elapsed_seconds'] = round(elapsed, 1)

    # Save report
    if not args.no_save:
        report_path = save_report(report)
        print(f"\n📁 Report saved to: {report_path}")

    # Print summary
    print_summary(report)

    print(f"\n⏱️  Completed in {elapsed:.1f} seconds")

    # Exit with error code if there were failures
    if report['failures'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
