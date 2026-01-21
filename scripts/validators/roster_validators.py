#!/usr/bin/env python3
"""
Roster Validators

Essential validators for catching data quality issues related to roster data.
These catch the Northwestern bug class where wrong team's data is applied.

Validators:
- validate_foxsports_roster_match: Cross-validate FoxSports cache against API roster
- validate_class_year_coverage: Ensure enough players have class year data
- validate_roster_size: Verify reasonable roster size
"""

import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any, Dict, List
from data_quality import Severity, ValidationResult, normalize_name


def validate_foxsports_roster_match(collected_data: Dict[str, Any]) -> List[ValidationResult]:
    """
    CRITICAL: Cross-validate FoxSports cache players against CBB API roster.

    This is the primary validator for catching the Northwestern bug where
    wrong team's FoxSports cache was loaded (different team ID).

    Severity levels:
    - CRITICAL: <50% match (strongly suggests wrong team's cache)
    - ERROR: 50-70% match (significant discrepancy)
    - WARNING: 70-90% match (some players missing)
    - INFO: >90% match (healthy)

    Args:
        collected_data: Dict containing:
            - api_roster_players: List of players from CBB API roster
            - foxsports_players: List of players from FoxSports cache
            - foxsports_id: The FoxSports team ID used
            - foxsports_source: 'cache' or 'fetched' (whether on-demand fetch occurred)
            - team_name: Team name for error messages

    Returns:
        List of ValidationResult objects
    """
    results = []

    api_roster = collected_data.get('api_roster_players', [])
    foxsports_players = collected_data.get('foxsports_players', [])
    team_name = collected_data.get('team_name', 'Unknown')
    foxsports_id = collected_data.get('foxsports_id')
    foxsports_source = collected_data.get('foxsports_source', 'unknown')

    # Handle case where FoxSports data is not available
    if not foxsports_players:
        results.append(ValidationResult(
            validator_name="FoxSports Roster Match",
            severity=Severity.WARNING,
            message="No FoxSports roster data available for comparison",
            details={
                'foxsports_id': foxsports_id,
                'foxsports_source': foxsports_source
            },
            remediation=f"Check that foxsports_id '{foxsports_id}' exists in team_registry.json "
                       f"and cache file rosters_cache/{foxsports_id}_classes.json exists."
        ))
        return results

    # Handle case where API roster is not available
    if not api_roster:
        results.append(ValidationResult(
            validator_name="FoxSports Roster Match",
            severity=Severity.ERROR,
            message="No API roster data to compare against FoxSports",
            details={'api_roster_count': 0},
            remediation="Check CBB API roster endpoint returned data for this team."
        ))
        return results

    # Normalize names for comparison
    api_names = set()
    for p in api_roster:
        name = p.get('name', '')
        if name:
            api_names.add(normalize_name(name))

    foxsports_names = set()
    for p in foxsports_players:
        name = p.get('name', '')
        if name:
            foxsports_names.add(normalize_name(name))

    # Calculate match statistics
    matched_names = api_names & foxsports_names
    api_only = api_names - foxsports_names
    foxsports_only = foxsports_names - api_names

    match_rate = len(matched_names) / len(api_names) if api_names else 0

    # Determine severity based on match rate
    if match_rate < 0.5:
        # CRITICAL: This strongly suggests wrong team's cache was loaded
        results.append(ValidationResult(
            validator_name="FoxSports Roster Match",
            severity=Severity.CRITICAL,
            message=f"Only {match_rate:.0%} of API roster players found in FoxSports cache! "
                   f"This strongly suggests wrong team's roster cache was loaded.",
            details={
                'match_rate': round(match_rate * 100, 1),
                'matched_count': len(matched_names),
                'api_roster_count': len(api_names),
                'foxsports_count': len(foxsports_names),
                'matched_players': sorted(list(matched_names))[:10],
                'api_only_players': sorted(list(api_only))[:10],
                'foxsports_only_players': sorted(list(foxsports_only))[:10],
                'foxsports_id': foxsports_id,
                'foxsports_source': foxsports_source,
            },
            remediation=f"URGENT: Verify foxsports_id '{foxsports_id}' in config/team_registry.json "
                       f"is correct for '{team_name}'. The cache file may belong to a different team. "
                       f"Check rosters_cache/{foxsports_id}_classes.json contents."
        ))
    elif match_rate < 0.7:
        # ERROR: Significant discrepancy
        results.append(ValidationResult(
            validator_name="FoxSports Roster Match",
            severity=Severity.ERROR,
            message=f"Only {match_rate:.0%} roster match with FoxSports cache - significant discrepancy",
            details={
                'match_rate': round(match_rate * 100, 1),
                'matched_count': len(matched_names),
                'api_roster_count': len(api_names),
                'unmatched_api_players': sorted(list(api_only)),
                'unmatched_foxsports_players': sorted(list(foxsports_only))[:10],
                'foxsports_id': foxsports_id,
            },
            remediation="Review unmatched players - may indicate transfers, name mismatches, "
                       "or stale cache. Consider refreshing the FoxSports cache."
        ))
    elif match_rate < 0.9:
        # WARNING: Some players missing
        results.append(ValidationResult(
            validator_name="FoxSports Roster Match",
            severity=Severity.WARNING,
            message=f"{match_rate:.0%} roster match - some players missing class data",
            details={
                'match_rate': round(match_rate * 100, 1),
                'unmatched_players': sorted(list(api_only)),
                'foxsports_id': foxsports_id,
            },
            remediation="Some players may have different names in FoxSports. "
                       "These players will have 'N/A' for class year."
        ))
    else:
        # INFO: Healthy match
        results.append(ValidationResult(
            validator_name="FoxSports Roster Match",
            severity=Severity.INFO,
            message=f"Roster match: {match_rate:.0%} ({len(matched_names)}/{len(api_names)} players)",
            details={
                'match_rate': round(match_rate * 100, 1),
                'matched_count': len(matched_names),
                'foxsports_id': foxsports_id,
            }
        ))

    # Additional warning if roster was fetched on-demand (cache was missing)
    if foxsports_source == 'fetched':
        results.append(ValidationResult(
            validator_name="FoxSports Cache Source",
            severity=Severity.WARNING,
            message="FoxSports roster was fetched on-demand (cache was missing or stale)",
            details={
                'foxsports_id': foxsports_id,
                'team_name': team_name
            },
            remediation="The FoxSports cache for this team was missing. "
                       "Fresh data was fetched successfully, but consider investigating "
                       "why the cache was not pre-populated."
        ))

    return results


def validate_class_year_coverage(collected_data: Dict[str, Any]) -> List[ValidationResult]:
    """
    Validate that enough players have class year data.

    Low coverage indicates FoxSports mapping issues or missing cache.

    Severity levels:
    - ERROR: <50% coverage (major data quality issue)
    - WARNING: 50-80% coverage (some players missing)
    - INFO: >80% coverage (acceptable)

    Args:
        collected_data: Dict containing:
            - players: List of processed player objects with 'class' field

    Returns:
        List of ValidationResult objects
    """
    results = []

    players = collected_data.get('players', [])

    if not players:
        # No players to validate - skip
        return results

    # Count players with valid class year
    players_with_class = []
    players_without_class = []

    for p in players:
        player_class = p.get('class', '')
        player_name = p.get('name', 'Unknown')

        if player_class and player_class not in ('N/A', '', 'n/a', 'Unknown'):
            players_with_class.append(player_name)
        else:
            players_without_class.append(player_name)

    coverage_rate = len(players_with_class) / len(players) if players else 0

    # Determine severity
    if coverage_rate < 0.5:
        results.append(ValidationResult(
            validator_name="Class Year Coverage",
            severity=Severity.ERROR,
            message=f"Only {coverage_rate:.0%} of players have class year data",
            details={
                'coverage_rate': round(coverage_rate * 100, 1),
                'with_class': len(players_with_class),
                'without_class': len(players_without_class),
                'total_players': len(players),
                'missing_class_players': players_without_class[:10]
            },
            remediation="Check FoxSports mapping in team_registry.json. "
                       "The foxsports_id may be incorrect or the cache may be empty. "
                       "Run: python foxsports_rosters/foxsports_scraper.py <team_name>"
        ))
    elif coverage_rate < 0.8:
        results.append(ValidationResult(
            validator_name="Class Year Coverage",
            severity=Severity.WARNING,
            message=f"{coverage_rate:.0%} class year coverage - some players missing",
            details={
                'coverage_rate': round(coverage_rate * 100, 1),
                'missing_class_players': players_without_class[:10]
            },
            remediation="Some players may have name mismatches with FoxSports roster. "
                       "These players show 'N/A' for class year."
        ))
    else:
        results.append(ValidationResult(
            validator_name="Class Year Coverage",
            severity=Severity.INFO,
            message=f"Class year coverage: {coverage_rate:.0%} ({len(players_with_class)}/{len(players)} players)",
            details={
                'coverage_rate': round(coverage_rate * 100, 1),
                'with_class': len(players_with_class),
                'total_players': len(players)
            }
        ))

    return results


def validate_roster_size(collected_data: Dict[str, Any]) -> List[ValidationResult]:
    """
    Validate roster has reasonable player count.

    Expected D1 roster size: 10-17 players.
    Unusual sizes may indicate data issues.

    Severity levels:
    - ERROR: <5 players (likely data fetch failure)
    - WARNING: 5-9 players (unusually small) or >20 players (unusually large)
    - INFO: 10-20 players (normal range)

    Args:
        collected_data: Dict containing:
            - players: List of processed player objects
            - team_name: Team name for error messages

    Returns:
        List of ValidationResult objects
    """
    results = []

    players = collected_data.get('players', [])
    team_name = collected_data.get('team_name', 'Unknown')

    player_count = len(players)

    if player_count < 5:
        results.append(ValidationResult(
            validator_name="Roster Size",
            severity=Severity.ERROR,
            message=f"Unusually small roster: {player_count} players",
            details={
                'player_count': player_count,
                'expected_range': '10-17',
                'players': [p.get('name', 'Unknown') for p in players]
            },
            remediation=f"Check CBB API roster endpoint returned data for '{team_name}'. "
                       "A roster this small likely indicates a data fetch failure or wrong team."
        ))
    elif player_count < 10:
        results.append(ValidationResult(
            validator_name="Roster Size",
            severity=Severity.WARNING,
            message=f"Small roster: {player_count} players (expected 10-17)",
            details={
                'player_count': player_count,
                'expected_range': '10-17'
            },
            remediation="Roster is smaller than typical. May be early season or data issue."
        ))
    elif player_count > 20:
        results.append(ValidationResult(
            validator_name="Roster Size",
            severity=Severity.WARNING,
            message=f"Large roster: {player_count} players (expected 10-17)",
            details={
                'player_count': player_count,
                'expected_range': '10-17'
            },
            remediation="Roster is larger than typical. May include walk-ons or redshirts."
        ))
    else:
        results.append(ValidationResult(
            validator_name="Roster Size",
            severity=Severity.INFO,
            message=f"Roster size: {player_count} players (normal)",
            details={
                'player_count': player_count,
                'expected_range': '10-17'
            }
        ))

    return results
