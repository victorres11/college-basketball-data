#!/usr/bin/env python3
"""
Validate all 365 teams against barttorvik.com.

This script tests that every team in the registry has a valid barttorvik name
by fetching all teams once and then validating local matches.

Usage:
    python scripts/validate_barttorvik_all_teams.py

Output:
    - Console progress updates
    - JSON report saved to scripts/validation_reports/barttorvik_validation.json
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'misc_data_sources' / 'barttorvik' / 'scripts'))

try:
    from barttorvik_teamsheets import get_teamsheets_data_structured, normalize_team_name, BARTTORVIK_TEAM_MAPPING
    BARTTORVIK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import barttorvik module: {e}")
    BARTTORVIK_AVAILABLE = False


def load_team_registry() -> dict:
    """Load the team registry JSON file."""
    registry_path = project_root / 'config' / 'team_registry.json'
    with open(registry_path) as f:
        return json.load(f)


def find_team_match(team_name: str, all_teams: list) -> tuple[bool, str]:
    """
    Try to find a team in the barttorvik data using the same logic as the scraper.

    Args:
        team_name: Team name to search for
        all_teams: List of all teams from barttorvik

    Returns:
        Tuple of (found, matched_name_or_error)
    """
    # Check if team name has a direct mapping
    team_name_lower = team_name.lower()
    if team_name_lower in BARTTORVIK_TEAM_MAPPING:
        team_name = BARTTORVIK_TEAM_MAPPING[team_name_lower]

    # Normalize the search team name
    normalized_search = normalize_team_name(team_name)

    # Track potential matches with scores
    matches = []

    for team in all_teams:
        team_name_from_data = team.get('team', '')
        normalized_team = normalize_team_name(team_name_from_data)

        # Exact match
        if normalized_search == normalized_team:
            return True, team_name_from_data

        # Check if search name is contained in team name
        if normalized_search in normalized_team:
            length_ratio = len(normalized_search) / len(normalized_team) if normalized_team else 0
            score = 100 + length_ratio * 50
            matches.append((score, team_name_from_data))
        # Check if team name is contained in search name
        elif normalized_team in normalized_search:
            length_ratio = len(normalized_team) / len(normalized_search) if normalized_search else 0
            score = 80 + length_ratio * 50
            matches.append((score, team_name_from_data))
        else:
            # Word-based matching
            search_words = set(normalized_search.split())
            team_words = set(normalized_team.split())
            common_words = search_words & team_words
            if common_words:
                score = len(common_words) * 30
                if len(common_words) >= 2:
                    score += 20
                matches.append((score, team_name_from_data))

    # Return best match if score is high enough
    if matches:
        matches.sort(reverse=True, key=lambda x: x[0])
        best_score, best_match = matches[0]
        if best_score >= 80:  # Threshold for acceptance
            return True, best_match

    return False, f"No match found for '{team_name}' (normalized: '{normalized_search}')"


def run_validation(year: int = 2026) -> dict:
    """
    Run validation for all teams in registry.

    Args:
        year: Season year

    Returns:
        Validation report dictionary
    """
    if not BARTTORVIK_AVAILABLE:
        return {
            'service': 'barttorvik',
            'error': 'barttorvik module not available',
            'timestamp': datetime.now().isoformat()
        }

    registry = load_team_registry()
    teams = registry.get('teams', {})
    total = len(teams)

    print(f"\n🏀 barttorvik.com Validation for {total} Teams")
    print(f"   Season: {year}")
    print("=" * 50)

    # Fetch all teams once
    print("\n📥 Fetching all teams from barttorvik.com...")
    try:
        all_barttorvik_teams = get_teamsheets_data_structured(year=year, conference='All')
        print(f"   Found {len(all_barttorvik_teams)} teams")
    except Exception as e:
        return {
            'service': 'barttorvik',
            'error': f'Failed to fetch barttorvik data: {e}',
            'timestamp': datetime.now().isoformat()
        }

    print("\n🔍 Validating registry teams...")
    print("-" * 50)

    successes = []
    failures = []
    skipped = []

    for i, (team_id, team_data) in enumerate(teams.items(), 1):
        canonical_name = team_data.get('canonical_name', 'Unknown')

        # Check if team has barttorvik mapping
        barttorvik_name = team_data.get('services', {}).get('barttorvik')
        if not barttorvik_name:
            skipped.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'reason': 'No barttorvik mapping in registry'
            })
            print(f"[{i:3d}/{total}] ⏭️  {canonical_name} - No barttorvik mapping")
            continue

        # Test barttorvik lookup
        found, result = find_team_match(barttorvik_name, all_barttorvik_teams)

        if found:
            successes.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'barttorvik_name': barttorvik_name,
                'matched_to': result
            })
            print(f"[{i:3d}/{total}] ✅ {canonical_name}")
        else:
            failures.append({
                'team_id': int(team_id),
                'name': canonical_name,
                'barttorvik_name': barttorvik_name,
                'error': result
            })
            print(f"[{i:3d}/{total}] ❌ {canonical_name} - {result}")

    # Build report
    report = {
        'service': 'barttorvik',
        'timestamp': datetime.now().isoformat(),
        'season': year,
        'total_teams': total,
        'barttorvik_teams_found': len(all_barttorvik_teams),
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

    report_path = reports_dir / 'barttorvik_validation.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    return report_path


def print_summary(report: dict):
    """Print validation summary."""
    if 'error' in report:
        print(f"\n❌ Validation failed: {report['error']}")
        return

    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"   Total teams:     {report['total_teams']}")
    print(f"   ✅ Successes:    {report['successes']}")
    print(f"   ❌ Failures:     {report['failures']}")
    print(f"   ⏭️  Skipped:      {report['skipped']}")
    print(f"   Success rate:    {report['success_rate']}")

    if report.get('failed_teams'):
        print("\n❌ FAILED TEAMS:")
        print("-" * 50)
        for team in report['failed_teams']:
            print(f"   [{team['team_id']:3d}] {team['name']}")
            print(f"         Barttorvik name: {team['barttorvik_name']}")
            print(f"         Error: {team['error']}")

    if report.get('skipped_teams'):
        print(f"\n⏭️  SKIPPED TEAMS ({len(report['skipped_teams'])}):")
        print("-" * 50)
        for team in report['skipped_teams'][:10]:
            print(f"   [{team['team_id']:3d}] {team['name']} - {team['reason']}")
        if len(report['skipped_teams']) > 10:
            print(f"   ... and {len(report['skipped_teams']) - 10} more")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate all teams against barttorvik.com')
    parser.add_argument('--season', type=int, default=2026,
                        help='Season year (default: 2026)')
    parser.add_argument('--no-save', action='store_true',
                        help='Skip saving report to file')

    args = parser.parse_args()

    # Run validation
    start_time = time.time()
    report = run_validation(year=args.season)
    elapsed = time.time() - start_time

    # Add timing to report
    report['elapsed_seconds'] = round(elapsed, 1)

    # Save report
    if not args.no_save and 'error' not in report:
        report_path = save_report(report)
        print(f"\n📁 Report saved to: {report_path}")

    # Print summary
    print_summary(report)

    print(f"\n⏱️  Completed in {elapsed:.1f} seconds")

    # Exit with error code if there were failures
    if report.get('failures', 0) > 0 or 'error' in report:
        sys.exit(1)


if __name__ == '__main__':
    main()
