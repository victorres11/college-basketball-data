#!/usr/bin/env python3
"""
Generate Eastern Washington Scouting Data as JSON
Consolidates all player stats, roster info, and game data into a single JSON file
"""

from cbb_api_wrapper import CollegeBasketballAPI
import json
from datetime import datetime


def get_player_career_season_stats(api, player_name, current_team):
    """
    Get player's season stats from previous seasons and schools.
    Searches across D1 players for the player name.
    """
    historical_seasons = []
    seasons_to_check = [2024, 2023, 2022]  # Check last 3 seasons
    
    print(f"  Searching historical data for {player_name}...")
    
    for season in seasons_to_check:
        # Skip current season (2025)
        if season == 2025:
            continue
            
        try:
            # Get all player stats for the season
            all_player_stats = api.get_player_season_stats(season, season_type='regular')
            
            # Look for player with similar name
            for player in all_player_stats:
                # Check if name matches (flexible matching)
                player_name_lower = player_name.lower()
                found_name_lower = player.get('name', '').lower()
                
                # Exact match or close match
                if player_name_lower == found_name_lower or \
                   (all(word in found_name_lower for word in player_name_lower.split()) and 
                    len(player_name_lower.split()) > 1):
                    
                    # Found the player
                    # Convert API season to academic year
                    academic_year = f"{season-1}-{str(season)[2:]}"
                    
                    season_data = {
                        'season': academic_year,
                        'team': player.get('team'),
                        'conference': player.get('conference'),
                        'games': player.get('games'),
                        'gamesStarted': player.get('starts'),
                        'seasonStats': {
                            'games': player.get('games'),
                            'minutes': player.get('minutes'),
                            'minutesPerGame': round(player.get('minutes', 0) / max(player.get('games', 1), 1), 1),
                            'points': player.get('points'),
                            'pointsPerGame': round(player.get('points', 0) / max(player.get('games', 1), 1), 1),
                            'assists': player.get('assists'),
                            'assistsPerGame': round(player.get('assists', 0) / max(player.get('games', 1), 1), 1),
                            'rebounds': player.get('rebounds'),
                            'reboundsPerGame': round(player.get('rebounds', {}).get('total', 0) / max(player.get('games', 1), 1), 1),
                            'steals': player.get('steals'),
                            'stealsPerGame': round(player.get('steals', 0) / max(player.get('games', 1), 1), 1),
                            'blocks': player.get('blocks'),
                            'blocksPerGame': round(player.get('blocks', 0) / max(player.get('games', 1), 1), 1),
                            'turnovers': player.get('turnovers'),
                            'turnoversPerGame': round(player.get('turnovers', 0) / max(player.get('games', 1), 1), 1),
                            'fouls': player.get('fouls'),
                            'foulsPerGame': round(player.get('fouls', 0) / max(player.get('games', 1), 1), 1),
                            'fieldGoals': player.get('fieldGoals'),
                            'twoPointFieldGoals': player.get('twoPointFieldGoals'),
                            'threePointFieldGoals': player.get('threePointFieldGoals'),
                            'freeThrows': player.get('freeThrows'),
                            'offensiveRating': player.get('offensiveRating'),
                            'defensiveRating': player.get('defensiveRating'),
                            'netRating': player.get('netRating'),
                            'usage': player.get('usage'),
                            'assistsTurnoverRatio': player.get('assistsTurnoverRatio'),
                            'effectiveFieldGoalPct': player.get('effectiveFieldGoalPct'),
                            'trueShootingPct': player.get('trueShootingPct'),
                            'winShares': player.get('winShares')
                        }
                    }
                    historical_seasons.append(season_data)
                    print(f"    Found {season}: {player.get('team')} ({player.get('conference', 'N/A')})")
                    break
        except Exception as e:
            print(f"    Error fetching {season}: {e}")
            continue
    
    return historical_seasons


def calculate_player_conference_rankings_from_list(all_players_raw, conference_name, target_player_name):
    """Calculate player's conference rankings for key statistical categories."""
    
    
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
    
    for stat_name, calc_func in stats_to_rank:
        values = []
        for player in conference_players:
            try:
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


def calculate_conference_rankings(api, team_name, conference_name):
    """Calculate team's conference rankings for key statistical categories."""
    
    # Fetch all team season stats
    print(f"Fetching all team season statistics for {conference_name} and D1 rankings...")
    all_teams_raw = api.get_team_season_stats(2025, season_type='regular')
    
    # Filter for D1 teams (those with conferences and enough games)
    d1_teams = [team for team in all_teams_raw if team.get('conference') is not None and team.get('games', 0) >= 10]
    
    # Filter for conference teams
    conference_teams = [team for team in all_teams_raw if team.get('conference') == conference_name]
    
    # Find our team
    target_team = None
    for team in conference_teams:
        if team_name.lower() in team.get('team', '').lower():
            target_team = team
            break
    
    if not target_team:
        print(f"Team {team_name} not found in {conference_name} conference")
        return {'conference': {}, 'd1': {}}
    
    # Helper function to calculate rankings for a set of teams
    def calculate_rankings_for_teams(teams, target_team_name):
        rankings = {}
        target_stats = target_team['teamStats']
        
        # Calculate rankings for key stats
        stats_to_rank = [
            ('pointsPerGame', lambda t: (t['teamStats']['points']['total'] / t['games']) if t['games'] > 0 else None),
            ('assistsPerGame', lambda t: (t['teamStats']['assists'] / t['games']) if t['games'] > 0 else None),
            ('reboundsPerGame', lambda t: (t['teamStats']['rebounds']['total'] / t['games']) if t['games'] > 0 else None),
            ('stealsPerGame', lambda t: (t['teamStats']['steals'] / t['games']) if t['games'] > 0 else None),
            ('blocksPerGame', lambda t: (t['teamStats']['blocks'] / t['games']) if t['games'] > 0 else None),
            ('fieldGoalPct', lambda t: t['teamStats']['fieldGoals']['pct']),
            ('threePointPct', lambda t: t['teamStats']['threePointFieldGoals']['pct']),
            ('freeThrowPct', lambda t: t['teamStats']['freeThrows']['pct']),
            ('effectiveFieldGoalPct', lambda t: t['teamStats']['fourFactors']['effectiveFieldGoalPct']),
            ('offensiveReboundPct', lambda t: t['teamStats']['fourFactors']['offensiveReboundPct']),
            ('opponentPointsPerGame', lambda t: (t['opponentStats']['points']['total'] / t['games']) if t['games'] > 0 else None),
        ]
        
        for stat_name, calc_func in stats_to_rank:
            values = []
            for team in teams:
                try:
                    value = calc_func(team)
                    if value is not None:
                        values.append((value, team['team']))
                except:
                    pass
            
            # Sort to determine rank (determine if higher is better)
            is_higher_better = not ('opponent' in stat_name or 'Points' in stat_name and 'opponent' in stat_name)
            values.sort(reverse=is_higher_better)
            
            # Find our team's rank
            for rank, (value, team) in enumerate(values, 1):
                if team_name.lower() in team.lower():
                    rankings[stat_name] = {
                        'rank': rank,
                        'totalTeams': len(values),
                        'value': value
                    }
                    break
        
        return rankings
    
    # Calculate conference and D1 rankings
    conference_rankings = calculate_rankings_for_teams(conference_teams, team_name)
    d1_rankings = calculate_rankings_for_teams(d1_teams, team_name)
    
    return {
        'conference': {
            'conference': conference_name,
            'team': team_name,
            'rankings': conference_rankings
        },
        'd1': {
            'level': 'Division 1',
            'team': team_name,
            'rankings': d1_rankings
        }
    }


def calculate_regular_season_stats(player_name, game_data):
    """Calculate regular season stats from per-game data for a specific player."""
    player_games = []
    for game in game_data:
        if 'players' in game:
            for player in game['players']:
                if player.get('name', '').lower() == player_name.lower():
                    game_date = game.get('startDate', '')
                    if game_date:
                        try:
                            date_part = game_date.split('T')[0]
                            year, month, day = date_part.split('-')
                            game_date_obj = datetime(int(year), int(month), int(day))
                            start_date = datetime(2024, 11, 4)
                            end_date = datetime(2025, 3, 16)
                            if start_date <= game_date_obj <= end_date:
                                player_games.append({
                                    'game': player,
                                    'game_context': {
                                        'gameId': game.get('gameId'),
                                        'startDate': game.get('startDate'),
                                        'opponent': game.get('opponent'),
                                        'isHome': game.get('isHome'),
                                        'seasonType': game.get('seasonType'),
                                        'conferenceGame': game.get('conferenceGame')
                                    }
                                })
                        except:
                            continue
    
    if not player_games:
        return None
    
    # Sort games by date
    player_games.sort(key=lambda x: x.get('game', {}).get('startDate', ''))
    games = len(player_games)
    starts = sum(1 for pg in player_games if pg.get('game', {}).get('starter', False))
    
    # Initialize totals
    fgm = fga = three_pm = three_pa = ftm = fta = 0
    or_reb = dr_reb = assists = turnovers = steals = blocks = fouls = minutes = points = 0
    
    for pg in player_games:
        game = pg['game']
        fg_data = game.get('fieldGoals', {})
        fgm += fg_data.get('made', 0)
        fga += fg_data.get('attempted', 0)
        
        three_data = game.get('threePointFieldGoals', {})
        three_pm += three_data.get('made', 0)
        three_pa += three_data.get('attempted', 0)
        
        ft_data = game.get('freeThrows', {})
        ftm += ft_data.get('made', 0)
        fta += ft_data.get('attempted', 0)
        
        reb_data = game.get('rebounds', {})
        or_reb += reb_data.get('offensive', 0)
        dr_reb += reb_data.get('defensive', 0)
        
        assists += game.get('assists', 0)
        turnovers += game.get('turnovers', 0)
        steals += game.get('steals', 0)
        blocks += game.get('blocks', 0)
        fouls += game.get('fouls', 0)
        minutes += game.get('minutes', 0)
        points += game.get('points', 0)
    
    # Calculate averages
    fg_pct = (fgm / fga * 100) if fga > 0 else 0
    three_pct = (three_pm / three_pa * 100) if three_pa > 0 else 0
    ft_pct = (ftm / fta * 100) if fta > 0 else 0
    total_reb = or_reb + dr_reb
    rpg = total_reb / games if games > 0 else 0
    apg = assists / games if games > 0 else 0
    spg = steals / games if games > 0 else 0
    bpg = blocks / games if games > 0 else 0
    ppg = points / games if games > 0 else 0
    mpg = minutes / games if games > 0 else 0
    ratio = apg / (turnovers / games) if games > 0 and turnovers > 0 else 0
    
    # Get all game-by-game data
    game_by_game = []
    for pg in player_games:
        game = pg['game']
        game_by_game.append({
            'date': pg['game_context']['startDate'],
            'opponent': pg['game_context']['opponent'],
            'isHome': pg['game_context']['isHome'],
            'conferenceGame': pg['game_context']['conferenceGame'],
            'starter': game.get('starter', False),
            'minutes': game.get('minutes', 0),
            'points': game.get('points', 0),
            'rebounds': game.get('rebounds', {}).get('total', 0),
            'assists': game.get('assists', 0),
            'turnovers': game.get('turnovers', 0),
            'steals': game.get('steals', 0),
            'blocks': game.get('blocks', 0),
            'fouls': game.get('fouls', 0),
            'fieldGoals': {
                'made': game.get('fieldGoals', {}).get('made', 0),
                'attempted': game.get('fieldGoals', {}).get('attempted', 0)
            },
            'threePointFieldGoals': {
                'made': game.get('threePointFieldGoals', {}).get('made', 0),
                'attempted': game.get('threePointFieldGoals', {}).get('attempted', 0)
            },
            'freeThrows': {
                'made': game.get('freeThrows', {}).get('made', 0),
                'attempted': game.get('freeThrows', {}).get('attempted', 0)
            },
            'rebounds': {
                'offensive': game.get('rebounds', {}).get('offensive', 0),
                'defensive': game.get('rebounds', {}).get('defensive', 0)
            }
        })
    
    # Count foul-outs (games with 5+ fouls)
    foul_outs = sum(1 for pg in player_games if pg['game'].get('fouls', 0) >= 5)
    
    return {
        'games': games,
        'starts': starts,
        'fgm': fgm, 'fga': fga, 'fg_pct': round(fg_pct, 1),
        'three_pm': three_pm, 'three_pa': three_pa, 'three_pct': round(three_pct, 1),
        'ftm': ftm, 'fta': fta, 'ft_pct': round(ft_pct, 1),
        'or_reb': or_reb, 'dr_reb': dr_reb, 'total_reb': total_reb, 'rpg': round(rpg, 1),
        'assists': assists, 'apg': round(apg, 1),
        'turnovers': turnovers, 'steals': steals, 'spg': round(spg, 1),
        'blocks': blocks, 'bpg': round(bpg, 1),
        'points': points, 'ppg': round(ppg, 1),
        'minutes': minutes, 'mpg': round(mpg, 1),
        'ratio': round(ratio, 1),
        'fouls': fouls, 'foulOuts': foul_outs,
        'game_by_game': game_by_game
    }


def generate_eastern_washington_data_json():
    """Generate consolidated JSON file with all Eastern Washington data."""
    print("Fetching Eastern Washington data...")
    api = CollegeBasketballAPI()
    
    # Fetch data
    print("Fetching game data for Eastern Washington players...")
    game_data = api.get_player_game_stats_by_date('2024-11-04', '2025-03-17', "eastern washington")
    
    print("Fetching roster data...")
    roster_data = api.get_team_roster(2025, "eastern washington")
    
    print("Fetching recruiting data...")
    recruiting_data = api.get_recruiting_players("Eastern Washington")
    
    print("Fetching team game stats...")
    team_game_stats = api.get_team_game_stats(2025, '2024-11-04', '2025-03-17', "eastern washington", "regular")
    
    print("Fetching player season stats with rankings...")
    player_season_stats = api.get_player_season_stats(2025, "eastern washington", "regular")
    
    print("Fetching team season stats with rankings...")
    team_season_stats = api.get_team_season_stats(2025, "eastern washington", "regular")
    
    print("Calculating conference rankings...")
    conference_rankings = calculate_conference_rankings(api, "Eastern Washington", "Big Sky")
    
    # Fetch all conference players for individual player rankings (one-time fetch)
    print("Fetching all conference player stats for rankings...")
    all_conference_players = api.get_player_season_stats(2025, season_type='regular')
    
    # Create lookups
    roster_lookup = {}
    if roster_data and len(roster_data) > 0 and 'players' in roster_data[0]:
        for player in roster_data[0]['players']:
            player_name = player.get('name', '')
            roster_lookup[player_name.lower()] = player
    
    recruiting_lookup = {}
    for recruit in recruiting_data:
        player_name = recruit.get('name', '')
        recruiting_lookup[player_name.lower()] = recruit
    
    # Merge recruiting data (high school) into roster data
    for player_name, player_data in roster_lookup.items():
        if player_name in recruiting_lookup:
            recruit_data = recruiting_lookup[player_name]
            player_data['highSchool'] = recruit_data.get('school', 'N/A')
        else:
            # Try partial matching
            for recruit_name, recruit_data in recruiting_lookup.items():
                if player_name in recruit_name or recruit_name in player_name:
                    player_data['highSchool'] = recruit_data.get('school', 'N/A')
                    break
    
    # Get all unique players from game data
    unique_players = set()
    for game in game_data:
        if 'players' in game:
            for player in game['players']:
                player_name = player.get('name', '')
                if player_name:
                    unique_players.add(player_name)
    
    # Build consolidated data structure
    team_data = {
        'team': 'Eastern Washington',
        'season': '2024-25',
        'seasonType': 'Regular',
        'dataGenerated': datetime.now().isoformat(),
        'players': []
    }
    
    # Add team game stats if available
    if team_game_stats:
        team_data['teamGameStats'] = team_game_stats
    
    # Add team season stats with rankings if available
    if team_season_stats and len(team_season_stats) > 0:
        team_data['teamSeasonStats'] = team_season_stats[0]  # Usually just one team
    
    # Add conference and D1 rankings if available
    if conference_rankings:
        team_data['conferenceRankings'] = conference_rankings['conference']
        team_data['d1Rankings'] = conference_rankings['d1']
    
    # Create lookup for player season stats (for rankings)
    player_stats_lookup = {}
    if player_season_stats:
        for player in player_season_stats:
            player_name = player.get('name', '')
            if player_name:
                player_stats_lookup[player_name.lower()] = player
    
    # Process each player
    for player_name in sorted(unique_players):
        print(f"Processing {player_name}...")
        
        # Calculate stats
        stats = calculate_regular_season_stats(player_name, game_data)
        if not stats:
            continue
        
        # Get roster data
        player_roster_data = roster_lookup.get(player_name.lower(), {})
        
        # Get jersey number from roster or use "N/A"
        jersey_number = "N/A"
        if player_roster_data:
            jersey_number = str(player_roster_data.get('jersey', 'N/A'))
        
        # Determine if freshman
        is_freshman = False
        start_season = player_roster_data.get('startSeason')
        end_season = player_roster_data.get('endSeason')
        if start_season and end_season:
            years_at_school = end_season - start_season + 1
            is_freshman = (years_at_school == 1)
        
        # Extract height
        height_str = "N/A"
        height_inches = player_roster_data.get('height')
        if height_inches:
            feet = height_inches // 12
            inches = height_inches % 12
            height_str = f"{feet}-{inches}"
        
        # Extract hometown
        hometown_str = "N/A"
        hometown = player_roster_data.get('hometown', {})
        city = hometown.get('city', '')
        state = hometown.get('state', '')
        if city and state:
            hometown_str = f"{city}, {state}"
        
        # Class year
        class_year_str = "N/A"
        if start_season and end_season:
            years_at_school = end_season - start_season + 1
            if years_at_school == 1:
                class_year_str = "FR"
            elif years_at_school == 2:
                class_year_str = "SO"
            elif years_at_school == 3:
                class_year_str = "JR"
            else:
                class_year_str = "SR"
        
        player_record = {
            'name': player_name,
            'jerseyNumber': jersey_number,
            'position': player_roster_data.get('position', 'N/A'),
            'height': height_str,
            'class': class_year_str,
            'isFreshman': is_freshman,
            'hometown': hometown_str,
            'highSchool': player_roster_data.get('highSchool', 'N/A'),
            'seasonTotals': {
                'games': stats['games'],
                'gamesStarted': stats['starts'],
                'minutes': stats['minutes'],
                'mpg': stats['mpg'],
                'points': stats['points'],
                'ppg': stats['ppg'],
                'rebounds': stats['total_reb'],
                'rpg': stats['rpg'],
                'assists': stats['assists'],
                'apg': stats['apg'],
                'turnovers': stats['turnovers'],
                'steals': stats['steals'],
                'spg': stats['spg'],
                'blocks': stats['blocks'],
                'bpg': stats['bpg'],
                'fouls': stats['fouls'],
                'foulOuts': stats['foulOuts'],
                'fieldGoals': {
                    'made': stats['fgm'],
                    'attempted': stats['fga'],
                    'percentage': stats['fg_pct']
                },
                'threePointFieldGoals': {
                    'made': stats['three_pm'],
                    'attempted': stats['three_pa'],
                    'percentage': stats['three_pct']
                },
                'freeThrows': {
                    'made': stats['ftm'],
                    'attempted': stats['fta'],
                    'percentage': stats['ft_pct']
                },
                'rebounds': {
                    'offensive': stats['or_reb'],
                    'defensive': stats['dr_reb'],
                    'total': stats['total_reb']
                },
                'assistToTurnoverRatio': stats['ratio']
            },
            'gameByGame': stats.get('game_by_game', [])
        }
        
        # Add player season stats with rankings if available
        player_season_data = player_stats_lookup.get(player_name.lower())
        if player_season_data:
            player_record['seasonStatsWithRankings'] = player_season_data
        
        # Calculate player's conference rankings (using cached conference players)
        player_conference_rankings = calculate_player_conference_rankings_from_list(all_conference_players, "Big Sky", player_name)
        if player_conference_rankings:
            player_record['conferenceRankings'] = player_conference_rankings
        
        # Get player's historical season stats from previous schools
        historical_seasons = get_player_career_season_stats(api, player_name, "eastern washington")
        if historical_seasons:
            player_record['previousSeasons'] = historical_seasons
        
        team_data['players'].append(player_record)
    
    # Sort players by MPG (descending)
    team_data['players'].sort(key=lambda x: x['seasonTotals']['mpg'], reverse=True)
    
    # Add metadata
    team_data['metadata'] = {
        'totalPlayers': len(team_data['players']),
        'apiCalls': api.api_call_count if hasattr(api, 'api_call_count') else 0
    }
    
    # Save to JSON file
    output_file = 'eastern_washington_scouting_data.json'
    with open(output_file, 'w') as f:
        json.dump(team_data, f, indent=2)
    
    print(f"\n✅ JSON data generated successfully!")
    print(f"📁 File saved as: {output_file}")
    print(f"📊 Total players: {len(team_data['players'])}")
    
    # Print API call summary
    if hasattr(api, 'get_api_call_summary'):
        api.print_api_call_summary()
    
    return team_data


if __name__ == '__main__':
    generate_eastern_washington_data_json()

