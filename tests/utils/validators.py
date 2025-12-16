"""Validation utilities for generator output"""
import json
from typing import Dict, List, Any

def validate_required_keys(data: Dict, required_keys: List[str]) -> None:
    """Validate required top-level keys exist"""
    missing = set(required_keys) - set(data.keys())
    assert not missing, f"Missing required keys: {missing}"

def validate_team_record_consistency(data: Dict) -> None:
    """Validate team records are internally consistent"""
    total = data['totalRecord']

    # Wins + Losses = Games
    assert total['wins'] + total['losses'] == total['games'], \
        f"Record inconsistent: {total['wins']}W + {total['losses']}L ≠ {total['games']}G"

    # Check split records only if they exist (some older/newer files may not have them)
    home = data.get('homeRecord')
    away = data.get('awayRecord')
    neutral = data.get('neutralRecord')

    if home and away and neutral:
        # Home + Away + Neutral = Total
        total_wins = home['wins'] + away['wins'] + neutral['wins']
        total_losses = home['losses'] + away['losses'] + neutral['losses']
        total_games = home['games'] + away['games'] + neutral['games']

        assert total_wins == total['wins'], \
            f"Wins don't sum: {total_wins} (H+A+N) ≠ {total['wins']} (total)"
        assert total_losses == total['losses'], \
            f"Losses don't sum: {total_losses} (H+A+N) ≠ {total['losses']} (total)"
        assert total_games == total['games'], \
            f"Games don't sum: {total_games} (H+A+N) ≠ {total['games']} (total)"

def validate_player_stats(player: Dict) -> None:
    """Validate individual player statistics"""
    stats = player['seasonTotals']
    name = player['name']

    # Games played must be reasonable
    games = stats['games']
    assert 0 <= games <= 40, f"{name}: Invalid games count: {games}"

    if games > 0:
        # Per-game stats should match totals (with small tolerance for rounding)
        ppg_calculated = round(stats['points'] / games, 1)
        assert abs(stats['ppg'] - ppg_calculated) < 0.2, \
            f"{name}: PPG mismatch: {stats['ppg']} vs calculated {ppg_calculated}"

        # Rebounds might be a dict or int
        rebounds_total = stats['rebounds']['total'] if isinstance(stats['rebounds'], dict) else stats['rebounds']
        rpg_calculated = round(rebounds_total / games, 1)
        assert abs(stats['rpg'] - rpg_calculated) < 0.2, \
            f"{name}: RPG mismatch: {stats['rpg']} vs calculated {rpg_calculated}"

        apg_calculated = round(stats['assists'] / games, 1)
        assert abs(stats['apg'] - apg_calculated) < 0.2, \
            f"{name}: APG mismatch: {stats['apg']} vs calculated {apg_calculated}"

    # Percentages should be valid
    fg_pct = stats['fieldGoals']['percentage']
    assert 0 <= fg_pct <= 100, f"{name}: Invalid FG%: {fg_pct}"

    # Made shots can't exceed attempts
    assert stats['fieldGoals']['made'] <= stats['fieldGoals']['attempted'], \
        f"{name}: FGM > FGA: {stats['fieldGoals']['made']} > {stats['fieldGoals']['attempted']}"

    assert stats['threePointFieldGoals']['made'] <= stats['threePointFieldGoals']['attempted'], \
        f"{name}: 3PM > 3PA"

    assert stats['freeThrows']['made'] <= stats['freeThrows']['attempted'], \
        f"{name}: FTM > FTA"

    # Game-by-game should match season totals
    if player.get('gameByGame'):
        gbg_points = sum(game.get('points', 0) for game in player['gameByGame'])
        assert gbg_points == stats['points'], \
            f"{name}: Game-by-game points ({gbg_points}) ≠ season total ({stats['points']})"

def validate_subprocess_status(progress_callback: Dict, strict: bool = True) -> None:
    """
    Validate all subprocesses completed successfully

    Args:
        progress_callback: Progress callback dict with dataStatus
        strict: If True, ALL subprocesses must succeed (no skipped/failed)
    """
    if 'dataStatus' not in progress_callback:
        raise AssertionError("No dataStatus in progress_callback")

    statuses = {s['name']: s for s in progress_callback['dataStatus']}

    # Core processes that MUST succeed
    CORE_PROCESSES = [
        'Game Data',
        'Roster Data',
        'Team Game Stats',
        'Player Season Stats'
    ]

    # Optional processes (user wants strict mode, so these must also succeed)
    OPTIONAL_PROCESSES = [
        'Wikipedia Data',
        'Bart Torvik Data',
        'KenPom Data',
        'NET Rating',
        'Coach History',
        'Quadrant Records',
        'Conference Rankings'
    ]

    failures = []

    # Check core processes (always strict)
    for process in CORE_PROCESSES:
        if process not in statuses:
            failures.append(f"Missing: {process}")
        elif statuses[process]['status'] != 'success':
            msg = statuses[process].get('message', 'No message')
            failures.append(f"Failed: {process} - {msg}")

    # Check optional processes (strict mode per user requirement)
    if strict:
        for process in OPTIONAL_PROCESSES:
            if process in statuses:
                if statuses[process]['status'] not in ['success', 'skipped']:
                    msg = statuses[process].get('message', 'No message')
                    failures.append(f"Failed: {process} - {msg}")

    if failures:
        raise AssertionError(f"Subprocess failures:\n" + "\n".join(f"  - {f}" for f in failures))

def validate_data_structure(data: Dict) -> None:
    """Comprehensive data structure validation"""

    # Core required keys (present in all versions)
    REQUIRED_KEYS = [
        'team', 'season', 'seasonType', 'dataGenerated',
        'players', 'metadata'
    ]
    validate_required_keys(data, REQUIRED_KEYS)

    # Validate metadata
    assert 'totalPlayers' in data['metadata']
    assert 'apiCalls' in data['metadata']

    # Validate players array
    assert isinstance(data['players'], list)

    # Validate each player (if any - empty arrays are valid for test/incomplete files)
    for player in data['players']:
        required_player_keys = ['name', 'seasonTotals', 'gameByGame']
        validate_required_keys(player, required_player_keys)
        validate_player_stats(player)

    # Validate team records (if present - newer files have these)
    if 'totalRecord' in data and 'conferenceRecord' in data:
        validate_team_record_consistency(data)
