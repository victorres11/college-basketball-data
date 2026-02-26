"""
Shared ranking utility functions for conference stat rankings.

Extracted from team-specific generators to avoid duplication.
Used by all generator scripts and the web-ui generator.
"""


# ESPN qualification threshold: players must have played this percentage
# of the max games in their conference to qualify for per-game stat rankings.
MIN_GAMES_PCT = 0.75

# Per-game stats that require minimum games qualification
PER_GAME_STATS = {'pointsPerGame', 'assistsPerGame', 'reboundsPerGame',
                  'stealsPerGame', 'blocksPerGame', 'minutesPerGame'}

# Percentage stats that require BOTH minimum games (75%) AND a minimum volume per game
# NCAA official thresholds: 2.5 made per game for 3P% and FT%, 5.0 made per game for FG%
PCT_VOLUME_REQS = {
    'threePointPct': ('threePointFieldGoals', 'made', 2.5),
    'freeThrowPct':  ('freeThrows', 'made', 2.5),
    'fieldGoalPct':  ('fieldGoals', 'made', 5.0),
}


def calculate_player_conference_rankings_from_list(all_players_raw, conference_name, target_player_name):
    """Calculate player's conference rankings for key statistical categories.

    Players must have played in 75% of the max games in their conference
    to qualify for per-game stat rankings. Percentage stats (3P%, FT%, FG%)
    additionally require a minimum volume of makes per game (NCAA thresholds).
    """

    # Filter for conference players
    conference_players = [p for p in all_players_raw if p.get('conference') == conference_name]

    # Find our player
    target_player = None
    for player in conference_players:
        if target_player_name.lower() in player.get('name', '').lower():
            target_player = player
            break

    if not target_player:
        return {}

    rankings = {}

    # Calculate rankings for key stats
    stats_to_rank = [
        ('pointsPerGame', lambda p: (p['points'] / p['games']) if p['games'] > 0 else None),
        ('assistsPerGame', lambda p: (p['assists'] / p['games']) if p['games'] > 0 else None),
        ('reboundsPerGame', lambda p: (p['rebounds']['total'] / p['games']) if p['games'] > 0 else None),
        ('stealsPerGame', lambda p: (p['steals'] / p['games']) if p['games'] > 0 else None),
        ('blocksPerGame', lambda p: (p['blocks'] / p['games']) if p['games'] > 0 else None),
        ('fieldGoalPct', lambda p: p['fieldGoals']['pct']),
        ('threePointPct', lambda p: p['threePointFieldGoals']['pct']),
        ('freeThrowPct', lambda p: p['freeThrows']['pct']),
        ('effectiveFieldGoalPct', lambda p: p.get('effectiveFieldGoalPct')),
        ('assistToTurnoverRatio', lambda p: p['assistsTurnoverRatio']),
        ('offensiveRating', lambda p: p.get('offensiveRating')),
        ('defensiveRating', lambda p: p.get('defensiveRating')),
        ('netRating', lambda p: p.get('netRating')),
        # New counting stats rankings
        ('fieldGoalsMade', lambda p: p['fieldGoals']['made']),
        ('fieldGoalsAttempted', lambda p: p['fieldGoals']['attempted']),
        ('threePointFieldGoalsMade', lambda p: p['threePointFieldGoals']['made']),
        ('threePointFieldGoalsAttempted', lambda p: p['threePointFieldGoals']['attempted']),
        ('freeThrowsMade', lambda p: p['freeThrows']['made']),
        ('freeThrowsAttempted', lambda p: p['freeThrows']['attempted']),
        ('offensiveRebounds', lambda p: p['rebounds']['offensive']),
        ('defensiveRebounds', lambda p: p['rebounds']['defensive']),
        ('totalRebounds', lambda p: p['rebounds']['total']),
        ('totalAssists', lambda p: p['assists']),
        ('totalBlocks', lambda p: p['blocks']),
        ('minutesPerGame', lambda p: (p['minutes'] / p['games']) if p['games'] > 0 else None),
    ]

    # Qualification threshold: player must have played 75% of max games in conference
    max_games = max((p.get('games', 0) for p in conference_players), default=0)
    min_games_threshold = int(max_games * MIN_GAMES_PCT)

    for stat_name, calc_func in stats_to_rank:
        values = []
        for player in conference_players:
            try:
                games = player.get('games', 0)
                # For per-game stats, require minimum games played (75%)
                if stat_name in PER_GAME_STATS and games < min_games_threshold:
                    continue
                # For percentage stats, require both games threshold and volume per game
                if stat_name in PCT_VOLUME_REQS:
                    if games < min_games_threshold:
                        continue
                    stat_key, sub_key, min_per_game = PCT_VOLUME_REQS[stat_name]
                    total_made = player.get(stat_key, {}).get(sub_key, 0)
                    if games == 0 or (total_made / games) < min_per_game:
                        continue
                value = calc_func(player)
                if value is not None:
                    values.append((value, player['name']))
            except:
                pass

        # Sort to determine rank (determine if higher is better)
        is_higher_better = not ('Turnover' in stat_name or 'defensiveRating' in stat_name)
        values.sort(reverse=is_higher_better)

        # Find our player's rank
        for rank, (value, player_name) in enumerate(values, 1):
            if target_player_name.lower() in player_name.lower():
                rankings[stat_name] = {
                    'rank': rank,
                    'totalPlayers': len(values),
                    'value': value
                }
                break

    return rankings
