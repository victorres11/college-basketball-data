#!/usr/bin/env python3
"""
Validate all 365 teams against bballnet.com.

This script tests that every team in the registry has a valid bballnet slug.

Usage:
    python scripts/validate_bballnet_all_teams.py

Output:
    - Console progress updates
    - JSON report saved to scripts/validation_reports/bballnet_validation.json
"""

import json
import os
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
    Validate a single team against bballnet.com.

    Args:
        team_id: CBB API team ID
        team_data: Team data from registry

    Returns:
        Tuple of (success, bballnet_slug, error_message)
    """
    bballnet_slug = team_data.get('services', {}).get('bballnet')

    if not bballnet_slug:
        return False, None, "No bballnet mapping in registry"

    url = f"https://bballnet.com/teams/{bballnet_slug}"

    try:
        response = requests.get(url, timeout=10, allow_redirects=True)

        if response.status_code == 200:
            # Check if we got redirected to an error page or if content looks valid
            if 'not found' in response.text.lower() or len(response.text) < 500:
                return False, bballnet_slug, f"Page exists but may be invalid (status: {response.status_code})"
            return True, bballnet_slug, None
        elif response.status_code == 404:
            return False, bballnet_slug, f"Team page not found (404)"
        else:
            return False, bballnet_slug, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        return False, bballnet_slug, "Request timed out"
    except requests.exceptions.RequestException as e:
        return False, bballnet_slug, str(e)


def run_validation(delay: float = 0.5) -> dict:
    """
    Run validation for all teams in registry.

    Args:
        delay: Seconds to wait between API calls

    Returns:
        Validation report dictionary
    """
    registry = load_team_registry()
    teams = registry.get('teams', {})
    total = len(teams)

    print(f"\n🏀 bballnet.com Validation for {total} Teams")
    print(f"   Delay: {delay}s between calls")
    print("=" * 50)

    successes = []
    failures = []
    skipped = []

    for i, (team_id, team_data) in enumerate(teams.items(), 1):
        canonical_name = team_data.get('canonical_name', 'Unknown')

        # Check if team has bballnet mapping
        bballnet_slug = team_data.get('services', {}).get('bballnet')
        if not bballnet_slug:
            skipped.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'reason': 'No bballnet mapping in registry'
            })
            print(f"[{i:3d}/{total}] ⏭️  {canonical_name} - No bballnet mapping")
            continue

        # Test bballnet lookup
        success, slug_used, error = validate_team(team_id, team_data)

        if success:
            successes.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'bballnet_slug': slug_used
            })
            print(f"[{i:3d}/{total}] ✅ {canonical_name}")
        else:
            failures.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'bballnet_slug': slug_used,
                'error': error
            })
            print(f"[{i:3d}/{total}] ❌ {canonical_name} - {error}")

        # Rate limiting
        if i < total:
            time.sleep(delay)

    # Build report
    report = {
        'service': 'bballnet',
        'timestamp': datetime.now().isoformat(),
        'total_teams': total,
        'successes': len(successes),
        'failures': len(failures),
        'skipped': len(skipped),
        'success_rate': f"{len(successes) / (total - len(skipped)) * 100:.1f}%" if (total - len(skipped)) > 0 else "N/A",
        'failed_teams': failures,
        'skipped_teams': skipped,
        'successful_teams': successes
    }

    return report


def save_report(report: dict) -> Path:
    """Save validation report to JSON file."""
    reports_dir = project_root / 'scripts' / 'validation_reports'
    reports_dir.mkdir(exist_ok=True)

    report_path = reports_dir / 'bballnet_validation.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report_path


def print_summary(report: dict):
    """Print validation summary."""
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"   Total teams:     {report['total_teams']}")
    print(f"   ✅ Successes:    {report['successes']}")
    print(f"   ❌ Failures:     {report['failures']}")
    print(f"   ⏭️  Skipped:      {report['skipped']}")
    print(f"   Success rate:    {report['success_rate']}")

    if report['failed_teams']:
        print("\n❌ FAILED TEAMS:")
        print("-" * 50)
        for team in report['failed_teams']:
            print(f"   [{team['team_id']:3d}] {team['name']}")
            print(f"         Slug: {team['bballnet_slug']}")
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

    parser = argparse.ArgumentParser(description='Validate all teams against bballnet.com')
    parser.add_argument('--delay', type=float, default=0.5,
                        help='Delay between requests in seconds (default: 0.5)')
    parser.add_argument('--no-save', action='store_true',
                        help='Skip saving report to file')

    args = parser.parse_args()

    # Run validation
    start_time = time.time()
    report = run_validation(delay=args.delay)
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
