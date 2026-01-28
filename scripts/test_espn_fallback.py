#!/usr/bin/env python3
"""
Test script for ESPN fallback functionality.

Tests the patching of San Diego State vs Grand Canyon game (2026-01-22)
which is known to have empty player stats in CBBD.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from espn_fallback import ESPNFallback, patch_game_data_with_espn


def test_espn_team_lookup():
    """Test ESPN team ID lookups."""
    print("=" * 60)
    print("Test 1: ESPN Team ID Lookups")
    print("=" * 60)
    
    fallback = ESPNFallback(verbose=True)
    
    test_teams = [
        "San Diego State",
        "Grand Canyon",
        "UCLA",
        "Michigan State",
        "Eastern Washington",
        "Unknown Team XYZ",  # Should return None
    ]
    
    for team in test_teams:
        team_id = fallback.get_espn_team_id(team)
        status = "✓" if team_id else "✗"
        print(f"  {status} {team}: {team_id}")
    
    print()


def test_schedule_fetch():
    """Test fetching team schedule from ESPN."""
    print("=" * 60)
    print("Test 2: Fetch ESPN Schedule")
    print("=" * 60)
    
    fallback = ESPNFallback(verbose=True)
    
    # San Diego State = ESPN ID 21
    schedule = fallback.get_team_schedule("21")
    
    if schedule:
        print(f"  ✓ Retrieved {len(schedule)} games for San Diego State")
        # Show a few games
        for game in schedule[:3]:
            print(f"    - {game.get('date', '')[:10]}: {game.get('name', '')}")
    else:
        print("  ✗ Failed to fetch schedule")
    
    print()


def test_find_event():
    """Test finding specific ESPN event ID."""
    print("=" * 60)
    print("Test 3: Find ESPN Event ID")
    print("=" * 60)
    
    fallback = ESPNFallback(verbose=True)
    
    # Look for San Diego State vs Grand Canyon on 2026-01-22
    event_id = fallback.find_espn_event_id(
        espn_team_id="21",
        game_date="2026-01-22T04:00:00.000Z",
        opponent="Grand Canyon"
    )
    
    if event_id:
        print(f"  ✓ Found event ID: {event_id}")
    else:
        print("  ✗ Could not find event")
    
    print()
    return event_id


def test_box_score_fetch(event_id: str):
    """Test fetching box score from ESPN."""
    print("=" * 60)
    print("Test 4: Fetch Box Score")
    print("=" * 60)
    
    if not event_id:
        print("  ✗ Skipping - no event ID")
        return None
    
    fallback = ESPNFallback(verbose=True)
    box_score = fallback.get_game_box_score(event_id)
    
    if box_score:
        print(f"  ✓ Retrieved box score for event {event_id}")
        # Check structure
        if 'boxscore' in box_score:
            teams = box_score['boxscore'].get('players', [])
            print(f"    Teams in box score: {len(teams)}")
            for team in teams:
                team_name = team.get('team', {}).get('displayName', 'Unknown')
                athletes = team.get('statistics', [{}])[0].get('athletes', [])
                print(f"    - {team_name}: {len(athletes)} players")
    else:
        print("  ✗ Failed to fetch box score")
    
    print()
    return box_score


def test_transform(box_score: dict):
    """Test transforming ESPN data to CBBD format."""
    print("=" * 60)
    print("Test 5: Transform to CBBD Format")
    print("=" * 60)
    
    if not box_score:
        print("  ✗ Skipping - no box score data")
        return
    
    fallback = ESPNFallback(verbose=True)
    
    # Mock CBBD game object
    mock_game = {
        'gameId': 214567,
        'startDate': '2026-01-22T04:00:00.000Z',
        'opponent': 'Grand Canyon'
    }
    
    players = fallback.transform_espn_to_cbbd_format(box_score, "San Diego State", mock_game)
    
    if players:
        print(f"  ✓ Transformed {len(players)} players")
        print()
        print("  Sample player stats (CBBD format):")
        for player in players[:3]:
            name = player.get('name', 'Unknown')
            pts = player.get('points', 0)
            fg = player.get('fieldGoals', {})
            fg_str = f"{fg.get('made', 0)}-{fg.get('attempted', 0)}"
            reb = player.get('rebounds', {}).get('total', 0)
            ast = player.get('assists', 0)
            print(f"    - {name}: {pts} pts, {fg_str} FG, {reb} reb, {ast} ast")
    else:
        print("  ✗ Transform failed")
    
    print()


def test_full_patch():
    """Test the full patching workflow."""
    print("=" * 60)
    print("Test 6: Full Patch Workflow")
    print("=" * 60)
    
    # Simulate CBBD response with empty players for the Grand Canyon game
    mock_cbbd_data = [
        {
            'gameId': 214567,
            'season': 2026,
            'startDate': '2026-01-22T04:00:00.000Z',
            'team': 'San Diego State',
            'opponent': 'Grand Canyon',
            'isHome': False,
            'conferenceGame': True,
            'players': []  # Empty - this is the bug we're fixing!
        },
        {
            'gameId': 214620,
            'season': 2026,
            'startDate': '2026-01-24T21:00:00.000Z',
            'team': 'San Diego State',
            'opponent': 'UNLV',
            'isHome': False,
            'conferenceGame': True,
            'players': [
                {'name': 'Miles Byrd', 'points': 23}  # Has data
            ]
        }
    ]
    
    print(f"  Before patching:")
    for game in mock_cbbd_data:
        players = len(game.get('players', []))
        print(f"    - vs {game['opponent']}: {players} players")
    
    # Apply patch
    patched_data = patch_game_data_with_espn(mock_cbbd_data, "San Diego State", verbose=True)
    
    print(f"\n  After patching:")
    for game in patched_data:
        players = len(game.get('players', []))
        patched = "✓ PATCHED" if game.get('_espn_patched') else ""
        print(f"    - vs {game['opponent']}: {players} players {patched}")
    
    # Verify the Grand Canyon game was patched
    gcu_game = next((g for g in patched_data if g['opponent'] == 'Grand Canyon'), None)
    if gcu_game and len(gcu_game.get('players', [])) > 0:
        print(f"\n  ✓ SUCCESS: Grand Canyon game patched with {len(gcu_game['players'])} players!")
        
        # Show the patched stats
        print("\n  Patched player stats:")
        for player in gcu_game['players'][:5]:
            name = player.get('name', 'Unknown')
            pts = player.get('points', 0)
            fg = player.get('fieldGoals', {})
            fg_str = f"{fg.get('made', 0)}-{fg.get('attempted', 0)}"
            print(f"    - {name}: {pts} pts, {fg_str} FG")
    else:
        print(f"\n  ✗ FAILED: Grand Canyon game was not patched")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ESPN FALLBACK TEST SUITE")
    print("=" * 60 + "\n")
    
    test_espn_team_lookup()
    test_schedule_fetch()
    event_id = test_find_event()
    box_score = test_box_score_fetch(event_id)
    test_transform(box_score)
    test_full_patch()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
