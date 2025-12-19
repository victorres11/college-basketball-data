#!/usr/bin/env python3
"""
Validate all 365 teams against KenPom API.

This script tests that every team in the registry can be found in KenPom.
It helps identify mapping issues before they cause production failures.

Usage:
    python scripts/validate_kenpom_all_teams.py

Output:
    - Console progress updates
    - JSON report saved to scripts/validation_reports/kenpom_validation.json
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'misc_data_sources' / 'kenpom' / 'scripts'))

from kenpom_api import get_team_id, load_api_key


def load_team_registry() -> dict:
    """Load the team registry JSON file."""
    registry_path = project_root / 'config' / 'team_registry.json'
    with open(registry_path) as f:
        return json.load(f)


def validate_team(team_id: str, team_data: dict, season: int = 2026) -> tuple[bool, str, str]:
    """
    Validate a single team against KenPom API.

    Args:
        team_id: CBB API team ID
        team_data: Team data from registry
        season: Season year

    Returns:
        Tuple of (success, kenpom_name_used, error_message)
    """
    kenpom_name = team_data.get('services', {}).get('kenpom')

    if not kenpom_name:
        return False, None, "No KenPom mapping in registry"

    try:
        kenpom_team_id = get_team_id(kenpom_name, season)

        if kenpom_team_id:
            return True, kenpom_name, None
        else:
            return False, kenpom_name, f"Team '{kenpom_name}' not found in KenPom API"

    except Exception as e:
        return False, kenpom_name, str(e)


def run_validation(delay: float = 0.3, season: int = 2026) -> dict:
    """
    Run validation for all teams in registry.

    Args:
        delay: Seconds to wait between API calls
        season: Season year

    Returns:
        Validation report dictionary
    """
    # Verify API key is available
    try:
        load_api_key()
    except Exception as e:
        print(f"❌ Cannot run validation: {e}")
        sys.exit(1)

    registry = load_team_registry()
    teams = registry.get('teams', {})
    total = len(teams)

    print(f"\n🏀 KenPom Validation for {total} Teams")
    print(f"   Season: {season}")
    print(f"   Delay: {delay}s between calls")
    print("=" * 50)

    successes = []
    failures = []
    skipped = []

    for i, (team_id, team_data) in enumerate(teams.items(), 1):
        canonical_name = team_data.get('canonical_name', 'Unknown')

        # Check if team has KenPom mapping
        kenpom_name = team_data.get('services', {}).get('kenpom')
        if not kenpom_name:
            skipped.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'reason': 'No KenPom mapping in registry'
            })
            print(f"[{i:3d}/{total}] ⏭️  {canonical_name} - No KenPom mapping")
            continue

        # Test KenPom lookup
        success, name_used, error = validate_team(team_id, team_data, season)

        if success:
            successes.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'kenpom_name': name_used
            })
            print(f"[{i:3d}/{total}] ✅ {canonical_name}")
        else:
            failures.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'kenpom_name': name_used,
                'error': error
            })
            print(f"[{i:3d}/{total}] ❌ {canonical_name} - {error}")

        # Rate limiting (skip delay for skipped teams)
        if i < total:
            time.sleep(delay)

    # Build report
    report = {
        'service': 'kenpom',
        'timestamp': datetime.now().isoformat(),
        'season': season,
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

    report_path = reports_dir / 'kenpom_validation.json'
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
            print(f"         KenPom name: {team['kenpom_name']}")
            print(f"         Error: {team['error']}")

    if report['skipped_teams']:
        print(f"\n⏭️  SKIPPED TEAMS ({len(report['skipped_teams'])}):")
        print("-" * 50)
        for team in report['skipped_teams'][:10]:  # Show first 10
            print(f"   [{team['team_id']:3d}] {team['name']} - {team['reason']}")
        if len(report['skipped_teams']) > 10:
            print(f"   ... and {len(report['skipped_teams']) - 10} more")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate all teams against KenPom API')
    parser.add_argument('--delay', type=float, default=0.3,
                        help='Delay between API calls in seconds (default: 0.3)')
    parser.add_argument('--season', type=int, default=2026,
                        help='Season year (default: 2026)')
    parser.add_argument('--no-save', action='store_true',
                        help='Skip saving report to file')

    args = parser.parse_args()

    # Run validation
    start_time = time.time()
    report = run_validation(delay=args.delay, season=args.season)
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
