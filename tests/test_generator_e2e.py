"""End-to-end tests for generator"""
import json
import pytest
from pathlib import Path
import sys

# Import generator
sys.path.insert(0, str(Path(__file__).parent.parent / 'web-ui'))
from generator import generate_team_data
from tests.utils.validators import (
    validate_data_structure,
    validate_subprocess_status
)

@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.parametrize("team_name", ["Oregon", "Western Kentucky", "Arizona State"])
def test_generator_end_to_end(team_name, test_season, test_output_dir, project_root):
    """
    End-to-end test for generator

    Tests:
    - Generator completes successfully
    - All subprocesses succeed (STRICT mode)
    - Output file exists and is valid JSON
    - Data structure is correct
    - Stats are internally consistent
    """

    # Setup progress callback
    progress_callback = {
        'status': 'queued',
        'progress': 0,
        'message': '',
        'dataStatus': []
    }

    # Run generator (without historical stats for speed)
    print(f"\n{'='*70}")
    print(f"Testing: {team_name} ({test_season})")
    print(f"{'='*70}\n")

    result_path = generate_team_data(
        team_name=team_name,
        season=test_season,
        progress_callback=progress_callback,
        include_historical_stats=False  # Skip for speed
    )

    # Validate result path returned
    assert result_path, f"Generator returned None/empty path for {team_name}"

    # Convert to absolute path
    full_path = project_root / result_path

    # Validate file exists
    assert full_path.exists(), f"Output file not found: {full_path}"

    # Validate subprocess statuses (STRICT mode - all must succeed)
    print("\nValidating subprocess statuses...")
    validate_subprocess_status(progress_callback, strict=True)

    # Load and validate JSON
    print("\nValidating JSON structure...")
    with open(full_path) as f:
        data = json.load(f)

    # Validate data structure
    validate_data_structure(data)

    # Print summary
    print(f"\n✅ {team_name} - Test PASSED")
    print(f"   Team: {data['team']}")
    print(f"   Record: {data['totalRecord']['wins']}-{data['totalRecord']['losses']}")
    print(f"   Players: {len(data['players'])}")
    print(f"   Games: {data['totalRecord']['games']}")
    print(f"   API Calls: {data['metadata']['apiCalls']}")

    # Print subprocess summary
    print(f"\n   Subprocess Status:")
    for status in progress_callback['dataStatus']:
        icon = '✅' if status['status'] == 'success' else '❌'
        print(f"   {icon} {status['name']}: {status.get('message', '')}")

def test_all_teams_locally(test_teams, test_season, project_root):
    """
    Convenience test to run all teams at once locally

    Run with: pytest tests/test_generator_e2e.py::test_all_teams_locally -v
    """
    results = {}

    for team in test_teams:
        print(f"\n{'='*70}")
        print(f"Testing: {team}")
        print(f"{'='*70}")

        progress = {'dataStatus': []}

        try:
            result_path = generate_team_data(
                team_name=team,
                season=test_season,
                progress_callback=progress,
                include_historical_stats=False
            )

            full_path = project_root / result_path

            # Validate
            validate_subprocess_status(progress, strict=True)

            with open(full_path) as f:
                data = json.load(f)

            validate_data_structure(data)

            results[team] = 'PASS'
            print(f"✅ {team} - PASS")

        except Exception as e:
            results[team] = f'FAIL: {str(e)}'
            print(f"❌ {team} - FAIL: {e}")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for team, result in results.items():
        icon = '✅' if result == 'PASS' else '❌'
        print(f"{icon} {team}: {result}")

    # Fail if any failed
    failures = [t for t, r in results.items() if r != 'PASS']
    assert not failures, f"Failed teams: {failures}"


@pytest.mark.e2e
@pytest.mark.parametrize("team_name,expected_player,expected_class", [
    ("Northwestern", "Nick Martinelli", "SR"),
    ("Oregon", "Jackson Shelstad", "SO"),
])
def test_player_classes_match_foxsports_cache(team_name, expected_player, expected_class, test_season, project_root):
    """
    Regression test: Verify player classes are correctly loaded from FoxSports cache.

    This test catches bugs where the wrong team's roster cache is used due to
    team ID mismatches (e.g., CBB API returning wrong teamId).
    """
    # Load FoxSports cache for the team
    sys.path.insert(0, str(project_root / 'scripts'))
    from team_lookup import get_team_lookup

    lookup = get_team_lookup()
    team_id = lookup.get_team_id(team_name)
    assert team_id, f"Team '{team_name}' not found in registry"

    # Load the FoxSports cache
    cache_path = project_root / 'foxsports_rosters' / 'rosters_cache' / f'{team_id}_classes.json'
    assert cache_path.exists(), f"FoxSports cache not found: {cache_path}"

    with open(cache_path) as f:
        cached_players = json.load(f)

    # Find the expected player in cache
    cached_class = None
    for player in cached_players:
        if expected_player.lower() in player['name'].lower():
            cached_class = player['class']
            break

    assert cached_class == expected_class, \
        f"FoxSports cache mismatch: {expected_player} should be {expected_class}, got {cached_class}"

    # Now generate data and verify it matches
    progress_callback = {'status': 'queued', 'progress': 0, 'message': '', 'dataStatus': []}

    result_path = generate_team_data(
        team_name=team_name,
        season=test_season,
        progress_callback=progress_callback,
        include_historical_stats=False
    )

    full_path = project_root / result_path
    with open(full_path) as f:
        data = json.load(f)

    # Find the player in generated data
    generated_class = None
    for player in data['players']:
        if expected_player.lower() in player['name'].lower():
            generated_class = player['class']
            break

    assert generated_class == expected_class, \
        f"Generated data mismatch: {expected_player} should be {expected_class}, got {generated_class}. " \
        f"This may indicate the generator used the wrong team's FoxSports cache."

    print(f"✅ {team_name}: {expected_player} correctly shows as {expected_class}")
