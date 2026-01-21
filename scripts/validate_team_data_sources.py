#!/usr/bin/env python3
"""
Validate that all teams have required data sources configured.

This script checks:
1. Team exists in registry with all service IDs
2. FoxSports roster cache file exists
3. Cached roster file exists (optional)

Run this before generating data to catch missing sources early.

Usage:
    python scripts/validate_team_data_sources.py [team_name]
    python scripts/validate_team_data_sources.py --all
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Add paths
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from team_lookup import get_team_lookup


def validate_team(team_name: str, verbose: bool = True) -> dict:
    """
    Validate data sources for a single team.

    Returns dict with validation results.
    """
    results = {
        'team_name': team_name,
        'valid': True,
        'errors': [],
        'warnings': [],
        'details': {}
    }

    lookup = get_team_lookup()

    # 1. Check team exists in registry
    team_id = lookup.get_team_id(team_name)
    if not team_id:
        results['valid'] = False
        results['errors'].append(f"Team '{team_name}' not found in registry")
        return results

    results['details']['registry_id'] = team_id
    team_info = lookup.get_team(team_id)

    # 2. Check FoxSports ID exists
    foxsports_id = lookup.lookup(team_name, 'foxsports_id')
    if not foxsports_id:
        results['valid'] = False
        results['errors'].append("No foxsports_id in registry")
    else:
        results['details']['foxsports_id'] = foxsports_id

        # 3. Check FoxSports cache file exists
        cache_file = PROJECT_ROOT / 'foxsports_rosters' / 'rosters_cache' / f'{foxsports_id}_classes.json'
        if not cache_file.exists():
            results['valid'] = False
            results['errors'].append(f"FoxSports cache file missing: {cache_file.name}")
        else:
            # Check it has data
            with open(cache_file) as f:
                cache_data = json.load(f)
            if not cache_data:
                results['warnings'].append("FoxSports cache file is empty")
            else:
                results['details']['foxsports_players'] = len(cache_data)

    # 4. Check other service mappings
    services = ['bballnet', 'sports_reference', 'wikipedia_page', 'barttorvik', 'kenpom']
    for service in services:
        value = lookup.lookup(team_name, service)
        if not value:
            results['warnings'].append(f"Missing {service} mapping")
        else:
            results['details'][service] = value

    # 5. Check cached roster file (optional but helpful)
    roster_file = PROJECT_ROOT / 'data' / 'rosters' / '2026' / f'{team_name.lower().replace(" ", "_")}_roster.json'
    if roster_file.exists():
        results['details']['cached_roster'] = True
    else:
        results['details']['cached_roster'] = False
        results['warnings'].append(f"No cached roster file (fallback for classes)")

    if verbose:
        print_results(results)

    return results


def print_results(results: dict):
    """Print validation results."""
    status = "✅ VALID" if results['valid'] else "❌ INVALID"
    print(f"\n{results['team_name']}: {status}")

    if results['errors']:
        print("  Errors:")
        for err in results['errors']:
            print(f"    ❌ {err}")

    if results['warnings']:
        print("  Warnings:")
        for warn in results['warnings']:
            print(f"    ⚠️  {warn}")

    if results['details']:
        print("  Details:")
        for key, value in results['details'].items():
            print(f"    - {key}: {value}")


def validate_all_teams(verbose: bool = False) -> dict:
    """Validate all teams in the registry."""
    lookup = get_team_lookup()

    # Get all teams from registry
    registry_path = PROJECT_ROOT / 'config' / 'team_registry.json'
    with open(registry_path) as f:
        registry = json.load(f)

    all_results = {
        'total': 0,
        'valid': 0,
        'invalid': 0,
        'with_warnings': 0,
        'teams': []
    }

    for team_id, team_data in registry['teams'].items():
        team_name = team_data['canonical_name']
        results = validate_team(team_name, verbose=verbose)
        all_results['total'] += 1

        if results['valid']:
            all_results['valid'] += 1
        else:
            all_results['invalid'] += 1
            all_results['teams'].append(results)

        if results['warnings']:
            all_results['with_warnings'] += 1

    return all_results


def main():
    parser = argparse.ArgumentParser(description='Validate team data sources')
    parser.add_argument('team_name', nargs='?', help='Team name to validate')
    parser.add_argument('--all', action='store_true', help='Validate all teams')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output for --all')

    args = parser.parse_args()

    if args.all:
        print("Validating all teams...")
        results = validate_all_teams(verbose=args.verbose)

        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total teams: {results['total']}")
        print(f"✅ Valid: {results['valid']}")
        print(f"❌ Invalid: {results['invalid']}")
        print(f"⚠️  With warnings: {results['with_warnings']}")

        if results['invalid'] > 0:
            print(f"\nInvalid teams:")
            for team in results['teams']:
                print(f"  - {team['team_name']}: {', '.join(team['errors'])}")
            sys.exit(1)
    elif args.team_name:
        results = validate_team(args.team_name)
        if not results['valid']:
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
