#!/usr/bin/env python3
"""
Generate Michigan State Scouting Data as JSON
Consolidates all player stats, roster info, and game data into a single JSON file
"""

from cbb_api_wrapper import CollegeBasketballAPI
import json
from datetime import datetime


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
                            end_date = datetime(2025, 3, 9)
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
        'game_by_game': game_by_game
    }


def generate_msu_data_json():
    """Generate consolidated JSON file with all Michigan State data."""
    print("Fetching Michigan State data...")
    api = CollegeBasketballAPI()
    
    # Player roster
    players = [
        {"name": "Jaxon Kohler", "number": "0"},
        {"name": "Jeremy Fears Jr.", "number": "1"},
        {"name": "Kur Teng", "number": "2"},
        {"name": "Jaden Akins", "number": "3"},
        {"name": "Tre Holloman", "number": "5"},
        {"name": "Gehrig Normand", "number": "7"},
        {"name": "Frankie Fidler", "number": "8"},
        {"name": "Szymon Zapala", "number": "10"},
        {"name": "Jase Richardson", "number": "11"},
        {"name": "Carson Cooper", "number": "15"},
        {"name": "Nick Sanders", "number": "20"},
        {"name": "Xavier Booker", "number": "34"},
        {"name": "Coen Carr", "number": "55"}
    ]
    
    # Fetch data
    print("Fetching game data...")
    game_data = api.get_player_game_stats_by_date('2024-11-04', '2025-03-10', "michigan state")
    
    print("Fetching roster data...")
    roster_data = api.get_team_roster(2025, "michigan state")
    
    print("Fetching recruiting data...")
    recruiting_data = api.get_recruiting_players("Michigan State")
    
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
    
    # Build consolidated data structure
    team_data = {
        'team': 'Michigan State',
        'season': '2024-25',
        'seasonType': 'Regular',
        'dataGenerated': datetime.now().isoformat(),
        'players': []
    }
    
    # Process each player
    for player_info in players:
        player_name = player_info["name"]
        jersey_number = player_info["number"]
        
        print(f"Processing {player_name}...")
        
        # Calculate stats
        stats = calculate_regular_season_stats(player_name, game_data)
        if not stats:
            continue
        
        # Get roster data
        player_roster_data = roster_lookup.get(player_name.lower(), {})
        
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
        
        team_data['players'].append(player_record)
    
    # Sort players by MPG (descending)
    team_data['players'].sort(key=lambda x: x['seasonTotals']['mpg'], reverse=True)
    
    # Add metadata
    team_data['metadata'] = {
        'totalPlayers': len(team_data['players']),
        'apiCalls': api.api_call_count if hasattr(api, 'api_call_count') else 0
    }
    
    # Save to JSON file
    output_file = 'msu_scouting_data.json'
    with open(output_file, 'w') as f:
        json.dump(team_data, f, indent=2)
    
    print(f"\n✅ JSON data generated successfully!")
    print(f"📁 File saved as: {output_file}")
    print(f"📊 Total players: {len(team_data['players'])}")
    print(f"📏 File size: {len(json.dumps(team_data))} bytes")
    
    # Print API call summary
    if hasattr(api, 'get_api_call_summary'):
        api.print_api_call_summary()
    
    return team_data


if __name__ == '__main__':
    generate_msu_data_json()

