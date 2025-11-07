#!/usr/bin/env python3
"""
Generate Michigan State Roster Scouting Report
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
Creates newspaper-style HTML page with player cards for all MSU players
"""

from cbb_api_wrapper import CollegeBasketballAPI
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor


def calculate_team_game_stats(msu_game_data, opponent_game_data_list, api, date_range):
    """Calculate team stats by aggregating all players for each game."""
    team_game_stats = []
    
    # Get game scores from games endpoint - optimized to only get MSU regular season games
    print("Fetching game scores for Michigan State regular season...")
    
    # Fetch only MSU regular season games in one call
    all_games = []
    try:
        # Use team, season, and seasonType to get only relevant games
        games = api._make_request('games', {
            'team': 'Michigan State',
            'season': 2024,
            'seasonType': 'regular',
            'status': 'final'  # Only completed games
        })
        all_games = games if isinstance(games, list) else [games]
        print(f"Fetched {len(all_games)} Michigan State regular season games")
    except Exception as e:
        print(f"Warning: Could not fetch MSU regular season games: {e}")
        pass
    
    # Create lookup for game scores
    game_scores = {}
    for game in all_games:
        game_id = game.get('id')
        home_team = str(game.get('homeTeam', '')).lower()
        away_team = str(game.get('awayTeam', '')).lower()
        
        if 'michigan state' in home_team or 'michigan state' in away_team:
            msu_is_home = 'michigan state' in home_team
            msu_score = game.get('homePoints', 0) if msu_is_home else game.get('awayPoints', 0)
            opp_score = game.get('awayPoints', 0) if msu_is_home else game.get('homePoints', 0)
            game_scores[game_id] = {'msu_score': msu_score, 'opp_score': opp_score}
    
    # Create lookup for opponent data by gameId
    opponent_lookup = {}
    for opp_game_data in opponent_game_data_list:
        for game in opp_game_data:
            if 'gameId' in game:
                opponent_lookup[game['gameId']] = game
    
    for game in msu_game_data:
        if 'players' not in game:
            continue
        
        # Aggregate MSU team stats
        msu_stats = aggregate_team_stats(game['players'])
        
        # Get opponent game data
        game_id = game.get('gameId')
        opponent_name = game.get('opponent', 'Unknown')
        opponent_stats = None
        
        if game_id in opponent_lookup:
            opp_game = opponent_lookup[game_id]
            if 'players' in opp_game:
                opponent_stats = aggregate_team_stats(opp_game['players'])
        else:
            # Try to find opponent by searching through all opponent data
            for opp_game_data in opponent_game_data_list:
                for opp_game in opp_game_data:
                    if opp_game.get('gameId') == game_id and 'players' in opp_game:
                        opponent_stats = aggregate_team_stats(opp_game['players'])
                        break
                if opponent_stats:
                    break
        
        # Parse date
        date_obj = None
        date_str = game.get('startDate', '')
        if date_str:
            try:
                date_part = date_str.split('T')[0]
                year, month, day = date_part.split('-')
                date_obj = datetime(int(year), int(month), int(day))
            except:
                pass
        
        # Get scores from games endpoint
        game_id = game.get('gameId')
        if game_id in game_scores:
            msu_score = game_scores[game_id]['msu_score']
            opp_score = game_scores[game_id]['opp_score']
        else:
            # Fallback to aggregated player points
            msu_score = msu_stats['points']
            opp_score = opponent_stats['points'] if opponent_stats else 0
        
        result = 'W' if msu_score > opp_score else 'L' if msu_score < opp_score else 'T'
        result_text = f"{result} {msu_score}-{opp_score}"
        
        # Calculate FG%
        msu_fg_pct = (msu_stats['fgm'] / msu_stats['fga'] * 100) if msu_stats['fga'] > 0 else 0
        opp_fg_pct = (opponent_stats['fgm'] / opponent_stats['fga'] * 100) if opponent_stats and opponent_stats['fga'] > 0 else 0
        fg_margin = msu_stats['fgm'] - (opponent_stats['fgm'] if opponent_stats else 0)  # Absolute difference in made FGs
        
        # Calculate margins
        reb_margin = msu_stats['total_reb'] - (opponent_stats['total_reb'] if opponent_stats else 0)
        to_margin = opponent_stats['turnovers'] - msu_stats['turnovers'] if opponent_stats else 0  # Positive is good
        fd_margin = (opponent_stats['fouls'] if opponent_stats else 0) - msu_stats['fouls']  # Positive = opponent committed more fouls (good for MSU)
        fta_margin = msu_stats['fta'] - (opponent_stats['fta'] if opponent_stats else 0)
        
        team_game_stats.append({
            'date': date_str,
            'date_obj': date_obj,
            'opponent': opponent_name,
            'result': result_text,
            'result_wl': result,
            'msu_score': msu_score,
            'opp_score': opp_score,
            'fg_pct_msu': msu_fg_pct,
            'fg_pct_opp': opp_fg_pct,
            'fg_margin': fg_margin,
            'reb_margin': reb_margin,
            'to_margin': to_margin,
            'fd_margin': fd_margin,
            'fta_margin': fta_margin,
            # Offense stats
            '3pm': msu_stats['three_pm'],
            '3pa': msu_stats['three_pa'],
            'ft': msu_stats['ftm'],
            'fta': msu_stats['fta'],
            'ast': msu_stats['assists'],
            'to': msu_stats['turnovers'],
            'stl': msu_stats['steals'],
            'blk': msu_stats['blocks'],
            # Defense stats
            'opp_3pm': opponent_stats['three_pm'] if opponent_stats else 0,
            'opp_3pa': opponent_stats['three_pa'] if opponent_stats else 0,
            'opp_ft': opponent_stats['ftm'] if opponent_stats else 0,
            'opp_fta': opponent_stats['fta'] if opponent_stats else 0,
            'opp_ast': opponent_stats['assists'] if opponent_stats else 0,
            'opp_to': opponent_stats['turnovers'] if opponent_stats else 0,
            'opp_stl': opponent_stats['steals'] if opponent_stats else 0,
            'opp_blk': opponent_stats['blocks'] if opponent_stats else 0,
        })
    
    # Sort by date
    team_game_stats.sort(key=lambda x: x.get('date_obj') or datetime(1900, 1, 1))
    
    return team_game_stats


def aggregate_team_stats(players):
    """Aggregate player stats to get team totals."""
    team_stats = {
        'fgm': 0, 'fga': 0,
        'three_pm': 0, 'three_pa': 0,
        'ftm': 0, 'fta': 0,
        'off_reb': 0, 'def_reb': 0, 'total_reb': 0,
        'assists': 0,
        'turnovers': 0,
        'steals': 0,
        'blocks': 0,
        'fouls': 0,
        'points': 0,
    }
    
    for player in players:
        # Field goals
        fg_data = player.get('fieldGoals', {})
        team_stats['fgm'] += fg_data.get('made', 0)
        team_stats['fga'] += fg_data.get('attempted', 0)
        
        # 3-pointers
        three_data = player.get('threePointFieldGoals', {})
        team_stats['three_pm'] += three_data.get('made', 0)
        team_stats['three_pa'] += three_data.get('attempted', 0)
        
        # Free throws
        ft_data = player.get('freeThrows', {})
        team_stats['ftm'] += ft_data.get('made', 0)
        team_stats['fta'] += ft_data.get('attempted', 0)
        
        # Rebounds
        reb_data = player.get('rebounds', {})
        team_stats['off_reb'] += reb_data.get('offensive', 0)
        team_stats['def_reb'] += reb_data.get('defensive', 0)
        team_stats['total_reb'] += reb_data.get('total', 0)
        
        # Other stats
        team_stats['assists'] += player.get('assists', 0)
        team_stats['turnovers'] += player.get('turnovers', 0)
        team_stats['steals'] += player.get('steals', 0)
        team_stats['blocks'] += player.get('blocks', 0)
        team_stats['fouls'] += player.get('fouls', 0)
        team_stats['points'] += player.get('points', 0)
    
    return team_stats


def calculate_regular_season_stats(player_name, game_data):
    """Calculate regular season stats from per-game data for a specific player."""
    
    # Filter games for this player within regular season dates
    player_games = []
    for game in game_data:
        if 'players' in game:
            for player in game['players']:
                if player.get('name', '').lower() == player_name.lower():
                    # Check if game is within regular season (2024-11-04 to 2025-03-09)
                    game_date = game.get('startDate', '')
                    if game_date:
                        # Parse date and check if it's within regular season
                        try:
                            # Extract date part (before 'T')
                            date_part = game_date.split('T')[0]
                            year, month, day = date_part.split('-')
                            game_date_obj = datetime(int(year), int(month), int(day))
                            
                            # Regular season bounds (inclusive through March 9)
                            start_date = datetime(2024, 11, 4)
                            end_date = datetime(2025, 3, 9)  # Inclusive through March 9
                            
                            if start_date <= game_date_obj <= end_date:
                                player_games.append(player)
                        except:
                            # If date parsing fails, skip this game
                            continue
    
    if not player_games:
        return None
    
    # Sort games by date
    player_games.sort(key=lambda x: x.get('startDate', ''))
    
    # Calculate totals
    games = len(player_games)
    starts = sum(1 for game in player_games if game.get('starter', False))
    
    # Initialize totals
    fgm = fga = three_pm = three_pa = ftm = fta = 0
    or_reb = dr_reb = assists = turnovers = steals = blocks = fouls = minutes = points = 0
    
    for game in player_games:
        # Field goals
        fg_data = game.get('fieldGoals', {})
        fgm += fg_data.get('made', 0)
        fga += fg_data.get('attempted', 0)
        
        # 3-pointers
        three_data = game.get('threePointFieldGoals', {})
        three_pm += three_data.get('made', 0)
        three_pa += three_data.get('attempted', 0)
        
        # Free throws
        ft_data = game.get('freeThrows', {})
        ftm += ft_data.get('made', 0)
        fta += ft_data.get('attempted', 0)
        
        # Rebounds
        reb_data = game.get('rebounds', {})
        or_reb += reb_data.get('offensive', 0)
        dr_reb += reb_data.get('defensive', 0)
        
        # Other stats
        assists += game.get('assists', 0)
        turnovers += game.get('turnovers', 0)
        steals += game.get('steals', 0)
        blocks += game.get('blocks', 0)
        fouls += game.get('fouls', 0)
        minutes += game.get('minutes', 0)
        points += game.get('points', 0)
    
    # Calculate percentages
    fg_pct = (fgm / fga * 100) if fga > 0 else 0
    three_pct = (three_pm / three_pa * 100) if three_pa > 0 else 0
    ft_pct = (ftm / fta * 100) if fta > 0 else 0
    
    # Calculate per-game averages
    total_reb = or_reb + dr_reb
    rpg = round(total_reb / games, 1) if games > 0 else 0
    apg = round(assists / games, 1) if games > 0 else 0
    spg = round(steals / games, 1) if games > 0 else 0
    bpg = round(blocks / games, 1) if games > 0 else 0
    mpg = round(minutes / games, 1) if games > 0 else 0
    ppg = round(points / games, 1) if games > 0 else 0
    
    # Assist/Turnover ratio
    ast_to_ratio = round(assists / turnovers, 2) if turnovers > 0 else 0
    
    # Get position from first game (assuming it's consistent)
    position = player_games[0].get('position', 'N/A') if player_games else 'N/A'
    
    # Get last game
    last_game = player_games[-1] if player_games else None
    
    return {
        'games': games,
        'starts': starts,
        'fgm': fgm,
        'fga': fga,
        'fg_pct': fg_pct,
        'three_pm': three_pm,
        'three_pa': three_pa,
        'three_pct': three_pct,
        'ftm': ftm,
        'fta': fta,
        'ft_pct': ft_pct,
        'or_reb': or_reb,
        'dr_reb': dr_reb,
        'total_reb': total_reb,
        'assists': assists,
        'turnovers': turnovers,
        'steals': steals,
        'blocks': blocks,
        'fouls': fouls,
        'minutes': minutes,
        'points': points,
        'rpg': rpg,
        'apg': apg,
        'spg': spg,
        'bpg': bpg,
        'mpg': mpg,
        'ppg': ppg,
        'ast_to_ratio': ast_to_ratio,
        'position': position,
        'last_game': last_game
    }


def calculate_team_rankings(api):
    """Calculate MSU's D1 and Big Ten conference rankings for all statistical categories."""
    
    # Fetch all team season stats
    print("Fetching team season statistics for rankings...")
    all_teams_raw = api.get_team_season_stats(2025)
    
    # Filter out non-D1 teams (those with None conference or very few games)
    all_teams = [
        team for team in all_teams_raw 
        if team.get('conference') is not None and team.get('games', 0) >= 10
    ]
    
    # Filter for Big Ten teams
    big_ten_teams = [team for team in all_teams if team.get('conference') == 'Big Ten']
    print(f"Found {len(all_teams_raw)} total teams, {len(all_teams)} D1 teams, {len(big_ten_teams)} Big Ten teams")
    
    # Find Michigan State
    msu_team = None
    for team in big_ten_teams:
        if 'michigan state' in team.get('team', '').lower():
            msu_team = team
            break
    
    if not msu_team:
        print("Michigan State not found in Big Ten teams")
        return []
    
    rankings = []
    
    # Extract MSU stats
    msu_games = msu_team['games']
    msu_team_stats = msu_team['teamStats']
    msu_opp_stats = msu_team['opponentStats']
    
    # Helper function to rank teams
    def calculate_rankings(stat_calculator, reverse=True):
        """Calculate D1 and Big Ten rankings for a stat category."""
        # Calculate D1 rankings
        d1_values = []
        for team in all_teams:
            try:
                value = stat_calculator(team)
                if value is not None:
                    d1_values.append({'team': team, 'value': value, 'name': team['team']})
            except:
                pass
        
        # Calculate Big Ten rankings
        big_ten_values = []
        for team in big_ten_teams:
            try:
                value = stat_calculator(team)
                if value is not None:
                    big_ten_values.append({'team': team, 'value': value, 'name': team['team']})
            except:
                pass
        
        # Sort by value
        d1_values.sort(key=lambda x: x['value'], reverse=reverse)
        big_ten_values.sort(key=lambda x: x['value'], reverse=reverse)
        
        # Find MSU's ranks
        msu_value = stat_calculator(msu_team)
        
        # D1 rank
        d1_rank = 1
        for i, tv in enumerate(d1_values):
            if tv['value'] == msu_value:
                d1_rank = i + 1
                break
        
        # Big Ten rank
        big_ten_rank = 1
        for i, tv in enumerate(big_ten_values):
            if tv['value'] == msu_value:
                big_ten_rank = i + 1
                break
        
        return {
            'value': msu_value,
            'd1_rank': d1_rank,
            'big_ten_rank': big_ten_rank,
            'd1_total': len(d1_values),
            'big_ten_total': len(big_ten_values)
        }
    
    # 1. PPG
    rankings.append({
        'category': 'PPG',
        'rank': calculate_rankings(lambda t: t['teamStats']['points']['total'] / t['games'], reverse=True),
        'stat': msu_team_stats['points']['total'] / msu_games
    })
    
    # 2. FG%
    rankings.append({
        'category': 'FG%',
        'rank': calculate_rankings(lambda t: t['teamStats']['fieldGoals']['pct'], reverse=True),
        'stat': msu_team_stats['fieldGoals']['pct']
    })
    
    # 3. 3P%
    rankings.append({
        'category': '3P%',
        'rank': calculate_rankings(lambda t: t['teamStats']['threePointFieldGoals']['pct'], reverse=True),
        'stat': msu_team_stats['threePointFieldGoals']['pct']
    })
    
    # 4. 3P FGM/G
    rankings.append({
        'category': '3P FGM/G',
        'rank': calculate_rankings(lambda t: t['teamStats']['threePointFieldGoals']['made'] / t['games'], reverse=True),
        'stat': msu_team_stats['threePointFieldGoals']['made'] / msu_games
    })
    
    # 5. 3P FGA/G
    rankings.append({
        'category': '3P FGA/G',
        'rank': calculate_rankings(lambda t: t['teamStats']['threePointFieldGoals']['attempted'] / t['games'], reverse=True),
        'stat': msu_team_stats['threePointFieldGoals']['attempted'] / msu_games
    })
    
    # 6. Off Reb/G
    rankings.append({
        'category': 'Off Reb/G',
        'rank': calculate_rankings(lambda t: t['teamStats']['rebounds']['offensive'] / t['games'], reverse=True),
        'stat': msu_team_stats['rebounds']['offensive'] / msu_games
    })
    
    # 7. TO/G (lower is better)
    rankings.append({
        'category': 'TO/G',
        'rank': calculate_rankings(lambda t: t['teamStats']['turnovers']['total'] / t['games'], reverse=False),
        'stat': msu_team_stats['turnovers']['total'] / msu_games
    })
    
    # 8. APG
    rankings.append({
        'category': 'APG',
        'rank': calculate_rankings(lambda t: t['teamStats']['assists'] / t['games'], reverse=True),
        'stat': msu_team_stats['assists'] / msu_games
    })
    
    # 9. FT%
    rankings.append({
        'category': 'FT%',
        'rank': calculate_rankings(lambda t: t['teamStats']['freeThrows']['pct'], reverse=True),
        'stat': msu_team_stats['freeThrows']['pct']
    })
    
    # 10. FTM/G
    rankings.append({
        'category': 'FTM/G',
        'rank': calculate_rankings(lambda t: t['teamStats']['freeThrows']['made'] / t['games'], reverse=True),
        'stat': msu_team_stats['freeThrows']['made'] / msu_games
    })
    
    # 11. FTA/G
    rankings.append({
        'category': 'FTA/G',
        'rank': calculate_rankings(lambda t: t['teamStats']['freeThrows']['attempted'] / t['games'], reverse=True),
        'stat': msu_team_stats['freeThrows']['attempted'] / msu_games
    })
    
    # 12. Def. PPG (lower is better)
    rankings.append({
        'category': 'Def. PPG',
        'rank': calculate_rankings(lambda t: t['opponentStats']['points']['total'] / t['games'], reverse=False),
        'stat': msu_opp_stats['points']['total'] / msu_games
    })
    
    # 13. Def. FG% (lower is better)
    rankings.append({
        'category': 'Def. FG%',
        'rank': calculate_rankings(lambda t: t['opponentStats']['fieldGoals']['pct'], reverse=False),
        'stat': msu_opp_stats['fieldGoals']['pct']
    })
    
    # 14. Fouls/G
    rankings.append({
        'category': 'Fouls/G',
        'rank': calculate_rankings(lambda t: t['teamStats']['fouls']['total'] / t['games'], reverse=False),
        'stat': msu_team_stats['fouls']['total'] / msu_games
    })
    
    # 15. Def Rebs/G
    rankings.append({
        'category': 'Def Rebs/G',
        'rank': calculate_rankings(lambda t: t['teamStats']['rebounds']['defensive'] / t['games'], reverse=True),
        'stat': msu_team_stats['rebounds']['defensive'] / msu_games
    })
    
    # 16. TO Forced/G
    rankings.append({
        'category': 'TO Forced/G',
        'rank': calculate_rankings(lambda t: t['opponentStats']['turnovers']['total'] / t['games'], reverse=True),
        'stat': msu_opp_stats['turnovers']['total'] / msu_games
    })
    
    # 17. SPG
    rankings.append({
        'category': 'SPG',
        'rank': calculate_rankings(lambda t: t['teamStats']['steals'] / t['games'], reverse=True),
        'stat': msu_team_stats['steals'] / msu_games
    })
    
    # 18. BPG
    rankings.append({
        'category': 'BPG',
        'rank': calculate_rankings(lambda t: t['teamStats']['blocks'] / t['games'], reverse=True),
        'stat': msu_team_stats['blocks'] / msu_games
    })
    
    # 19. Pt. Margin
    pt_margin = (msu_team_stats['points']['total'] / msu_games) - (msu_opp_stats['points']['total'] / msu_games)
    rankings.append({
        'category': 'Pt. Margin',
        'rank': calculate_rankings(lambda t: (t['teamStats']['points']['total'] / t['games']) - (t['opponentStats']['points']['total'] / t['games']), reverse=True),
        'stat': pt_margin
    })
    
    # 20. Reb Margin
    reb_margin = (msu_team_stats['rebounds']['total'] / msu_games) - (msu_opp_stats['rebounds']['total'] / msu_games)
    rankings.append({
        'category': 'Reb Margin',
        'rank': calculate_rankings(lambda t: (t['teamStats']['rebounds']['total'] / t['games']) - (t['opponentStats']['rebounds']['total'] / t['games']), reverse=True),
        'stat': reb_margin
    })
    
    # 21. TO Margin
    to_margin = (msu_opp_stats['turnovers']['total'] / msu_games) - (msu_team_stats['turnovers']['total'] / msu_games)
    rankings.append({
        'category': 'TO Margin',
        'rank': calculate_rankings(lambda t: (t['opponentStats']['turnovers']['total'] / t['games']) - (t['teamStats']['turnovers']['total'] / t['games']), reverse=True),
        'stat': to_margin
    })
    
    # 22. A:TO Ratio
    if msu_team_stats['turnovers']['total'] > 0:
        ast_to_ratio = msu_team_stats['assists'] / msu_team_stats['turnovers']['total']
    else:
        ast_to_ratio = 0
    rankings.append({
        'category': 'A:TO Ratio',
        'rank': calculate_rankings(lambda t: t['teamStats']['assists'] / t['teamStats']['turnovers']['total'] if t['teamStats']['turnovers']['total'] > 0 else 0, reverse=True),
        'stat': ast_to_ratio
    })
    
    return rankings


def generate_rankings_table(rankings):
    """Generate HTML table for team statistical rankings."""
    
    if not rankings:
        return ""
    
    table_html = """
    <div class="rankings-section">
        <h2>Team Statistical Rankings</h2>
        <p>2024-25 Regular Season</p>
        <table class="rankings-table">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>D1 Rank</th>
                    <th>Big Ten Rank</th>
                    <th>Stat</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for ranking in rankings:
        category = ranking['category']
        d1_rank = ranking['rank']['d1_rank']
        big_ten_rank = ranking['rank']['big_ten_rank']
        stat_value = ranking['stat']
        
        # Format stat based on category type
        if '%' in category or 'FG%' in category or 'FT%' in category:
            stat_display = f"{stat_value:.1f}%"
        elif 'Ratio' in category:
            stat_display = f"{stat_value:.2f}"
        elif 'Margin' in category:
            stat_display = f"+{stat_value:.1f}" if stat_value >= 0 else f"{stat_value:.1f}"
        else:
            stat_display = f"{stat_value:.1f}"
        
        table_html += f"""
                <tr>
                    <td>{category}</td>
                    <td>{d1_rank}</td>
                    <td>{big_ten_rank}</td>
                    <td>{stat_display}</td>
                </tr>
        """
    
    table_html += """
            </tbody>
        </table>
    </div>
    """
    
    return table_html


def generate_team_stats_table(team_game_stats):
    """Generate HTML table for team game-by-game statistics."""
    
    # Start building the table
    table_html = """
    <div class="team-stats-section">
        <h2>Game-by-Game Team Statistics</h2>
        <p>Regular Season 2024-25 (31 Games)</p>
        <div class="table-container">
            <table class="team-stats-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Opponent</th>
                        <th>Result</th>
                        <th>FG% (MSU)</th>
                        <th>FG% (Opp)</th>
                        <th>FG Mar</th>
                        <th>Reb Mar</th>
                        <th>TO Mar</th>
                        <th>FD Mar</th>
                        <th>FTA Mar</th>
                        <th>3PM</th>
                        <th>3PA</th>
                        <th>FT</th>
                        <th>FTA</th>
                        <th>A</th>
                        <th>TO</th>
                        <th>Stl</th>
                        <th>Blk</th>
                        <th>Opp 3PM</th>
                        <th>Opp 3PA</th>
                        <th>Opp FT</th>
                        <th>Opp FTA</th>
                        <th>Opp A</th>
                        <th>Opp TO</th>
                        <th>Opp Stl</th>
                        <th>Opp Blk</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for game in team_game_stats:
        # Format date
        date_str = game['date']
        if date_str:
            try:
                date_part = date_str.split('T')[0]
                month, day, year = date_part.split('-')[1], date_part.split('-')[2], date_part.split('-')[0]
                display_date = f"{month}/{day}"
            except:
                display_date = date_str
        else:
            display_date = "N/A"
        
        # Result cell with color
        result_class = "result-win" if game['result_wl'] == 'W' else "result-loss"
        
        # Format margins with color
        def format_margin(value):
            if value > 0:
                return f'<span class="margin-positive">+{value:.1f}</span>' if abs(value) < 1 else f'<span class="margin-positive">+{value}</span>'
            elif value < 0:
                return f'<span class="margin-negative">{value:.1f}</span>' if abs(value) < 1 else f'<span class="margin-negative">{value}</span>'
            else:
                return '<span class="margin-zero">0</span>'
        
        table_html += f"""
                    <tr>
                        <td>{display_date}</td>
                        <td>{game['opponent']}</td>
                        <td class="{result_class}">{game['result']}</td>
                        <td>{game['fg_pct_msu']:.1f}%</td>
                        <td>{game['fg_pct_opp']:.1f}%</td>
                        <td>{format_margin(game['fg_margin'])}</td>
                        <td>{format_margin(game['reb_margin'])}</td>
                        <td>{format_margin(game['to_margin'])}</td>
                        <td>{format_margin(game['fd_margin'])}</td>
                        <td>{format_margin(game['fta_margin'])}</td>
                        <td>{game['3pm']}</td>
                        <td>{game['3pa']}</td>
                        <td>{game['ft']}</td>
                        <td>{game['fta']}</td>
                        <td>{game['ast']}</td>
                        <td>{game['to']}</td>
                        <td>{game['stl']}</td>
                        <td>{game['blk']}</td>
                        <td>{game['opp_3pm']}</td>
                        <td>{game['opp_3pa']}</td>
                        <td>{game['opp_ft']}</td>
                        <td>{game['opp_fta']}</td>
                        <td>{game['opp_ast']}</td>
                        <td>{game['opp_to']}</td>
                        <td>{game['opp_stl']}</td>
                        <td>{game['opp_blk']}</td>
                    </tr>
        """
    
    table_html += """
                </tbody>
            </table>
        </div>
    </div>
    """
    
    return table_html


def generate_player_card(player_name, jersey_number, regular_season_stats, roster_data=None):
    """Generate HTML for a single player card."""
    
    # Get roster data for this player
    height_str = "N/A"
    hometown_str = "N/A"
    high_school_str = "N/A"
    class_year_str = "N/A"
    
    if roster_data and isinstance(roster_data, dict):
        roster_player = roster_data  # Already the player data, not a lookup
        if roster_player:
            # Convert height from inches to feet'inches
            height_inches = roster_player.get('height')
            if height_inches:
                feet = height_inches // 12
                inches = height_inches % 12
                height_str = f"{feet}\' {inches}\""
            
            # Hometown
            hometown = roster_player.get('hometown', {})
            city = hometown.get('city', '')
            state = hometown.get('state', '')
            if city and state:
                hometown_str = f"{city}, {state}"
            
            # High school
            high_school_str = roster_player.get('highSchool', 'N/A')
            
            # Class year (calculate from start and end season)
            start_season = roster_player.get('startSeason')
            end_season = roster_player.get('endSeason')
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
    
    if not regular_season_stats:
        return f'''
        <div class="player-card">
            <div class="card-left">
                <div class="card-header">
                    <div class="jersey-number">#{jersey_number}</div>
                    <div class="player-name">{player_name.upper()}</div>
                </div>
                <div class="player-info">N/A • {height_str} • {class_year_str}</div>
                <div class="hometown-info">{hometown_str} ({high_school_str})</div>
                <div class="last-game">No regular season games</div>
            </div>
            <div class="card-right">
                <div class="no-data">No regular season data available</div>
            </div>
        </div>
        '''
    
    # Extract calculated regular season stats
    games = regular_season_stats['games']
    starts = regular_season_stats['starts']
    fgm = regular_season_stats['fgm']
    fga = regular_season_stats['fga']
    fg_pct = regular_season_stats['fg_pct']
    three_pm = regular_season_stats['three_pm']
    three_pa = regular_season_stats['three_pa']
    three_pct = regular_season_stats['three_pct']
    ftm = regular_season_stats['ftm']
    fta = regular_season_stats['fta']
    ft_pct = regular_season_stats['ft_pct']
    or_reb = regular_season_stats['or_reb']
    dr_reb = regular_season_stats['dr_reb']
    total_reb = regular_season_stats['total_reb']
    assists = regular_season_stats['assists']
    turnovers = regular_season_stats['turnovers']
    steals = regular_season_stats['steals']
    blocks = regular_season_stats['blocks']
    fouls = regular_season_stats['fouls']
    minutes = regular_season_stats['minutes']
    points = regular_season_stats['points']
    position = regular_season_stats['position']
    rpg = regular_season_stats['rpg']
    apg = regular_season_stats['apg']
    spg = regular_season_stats['spg']
    bpg = regular_season_stats['bpg']
    mpg = regular_season_stats['mpg']
    ppg = regular_season_stats['ppg']
    ast_to_ratio = regular_season_stats['ast_to_ratio']
    
    # Get last game stats
    last_game_text = "No regular season games"
    if regular_season_stats['last_game']:
        last_game = regular_season_stats['last_game']
        last_points = last_game.get('points', 0)
        last_reb = last_game.get('rebounds', {}).get('total', 0)
        last_ast = last_game.get('assists', 0)
        last_to = last_game.get('turnovers', 0)
        last_steals = last_game.get('steals', 0)
        last_blocks = last_game.get('blocks', 0)
        last_fgm = last_game.get('fieldGoals', {}).get('made', 0)
        last_fga = last_game.get('fieldGoals', {}).get('attempted', 0)
        last_ftm = last_game.get('freeThrows', {}).get('made', 0)
        last_fta = last_game.get('freeThrows', {}).get('attempted', 0)
        last_3pm = last_game.get('threePointFieldGoals', {}).get('made', 0)
        last_3pa = last_game.get('threePointFieldGoals', {}).get('attempted', 0)
        last_minutes = last_game.get('minutes', 0)
        
        last_game_text = f"Last: {last_points}p, {last_reb}r, {last_ast}a, {last_to}to, {last_steals}s, {last_blocks}b, {last_fgm}-{last_fga}fg, {last_ftm}-{last_fta}ft, ({last_3pm}-{last_3pa})3p, [{last_minutes}]"
    
    return f'''
    <div class="player-card">
        <div class="card-left">
            <div class="card-header">
                <div class="jersey-number">#{jersey_number}</div>
                <div class="player-name">{player_name.upper()}</div>
            </div>
            
            <div class="player-info">{position} • {height_str} • {class_year_str}</div>
            <div class="hometown-info">{hometown_str} ({high_school_str})</div>
            <div class="last-game">{last_game_text}</div>
        </div>
        
        <div class="card-right">
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>G</th>
                        <th>GS</th>
                        <th>FG-FGA</th>
                        <th>FG%</th>
                        <th>3P-3PA</th>
                        <th>3P%</th>
                        <th>FT-FTA</th>
                        <th>FT%</th>
                        <th>OR</th>
                        <th>DR</th>
                        <th>Reb</th>
                        <th>RPG</th>
                        <th>AST</th>
                        <th>APG</th>
                        <th>Ratio</th>
                        <th>SPG</th>
                        <th>BLK</th>
                        <th>BPG</th>
                        <th>MPG</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{games}</td>
                        <td>{starts}</td>
                        <td>{fgm}-{fga}</td>
                        <td>{fg_pct:.1f}%</td>
                        <td>{three_pm}-{three_pa}</td>
                        <td>{three_pct:.1f}%</td>
                        <td>{ftm}-{fta}</td>
                        <td>{ft_pct:.1f}%</td>
                        <td>{or_reb}</td>
                        <td>{dr_reb}</td>
                        <td>{total_reb}</td>
                        <td>{rpg}</td>
                        <td>{assists}</td>
                        <td>{apg}</td>
                        <td>{ast_to_ratio}</td>
                        <td>{spg}</td>
                        <td>{blocks}</td>
                        <td>{bpg}</td>
                        <td>{mpg}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    '''


def generate_msu_roster_report():
    """Generate comprehensive MSU roster scouting report."""
    
    # Load data
    print("Loading Michigan State roster data...")
    api = CollegeBasketballAPI()
    
    # Store API instance globally for summary
    global api_instance
    api_instance = api
    
    # Player roster with jersey numbers
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
    
    # Get per-game stats for regular season (2024-11-04 to 2025-03-09 inclusive)
    # API needs end date as 2025-03-10 to include March 9 games
    game_data = api.get_player_game_stats_by_date('2024-11-04', '2025-03-10', "michigan state")
    
    # Get roster data for player details (use 2025 for current roster)
    print("Fetching roster data for player details...")
    roster_data = api.get_team_roster(2025, "michigan state")
    
    # Get recruiting data for high school information
    print("Fetching recruiting data for high school information...")
    recruiting_data = api.get_recruiting_players("Michigan State")
    
    # Create roster lookup
    roster_lookup = {}
    if roster_data and 'players' in roster_data[0]:
        for player in roster_data[0]['players']:
            player_name = player.get('name', '')
            roster_lookup[player_name.lower()] = player
    
    # Create recruiting lookup for high school data
    recruiting_lookup = {}
    for recruit in recruiting_data:
        player_name = recruit.get('name', '')
        recruiting_lookup[player_name.lower()] = recruit
    
    # Merge recruiting data (high school) into roster data
    for player_name, player_data in roster_lookup.items():
        # Try exact match first
        if player_name in recruiting_lookup:
            recruit_data = recruiting_lookup[player_name]
            player_data['highSchool'] = recruit_data.get('school', 'N/A')
        else:
            # Try partial matching (e.g., "Jeremy Fears" vs "Jeremy Fears Jr.")
            for recruit_name, recruit_data in recruiting_lookup.items():
                if player_name in recruit_name or recruit_name in player_name:
                    player_data['highSchool'] = recruit_data.get('school', 'N/A')
                    break
    
    # Process each player
    player_cards = []
    
    for player_info in players:
        player_name = player_info["name"]
        jersey_number = player_info["number"]
        
        print(f"Processing {player_name}...")
        
        # Calculate regular season stats from per-game data
        regular_season_stats = calculate_regular_season_stats(player_name, game_data)
        
        # Generate player card with roster data
        player_roster_data = roster_lookup.get(player_name.lower(), {})
        
        # Debug if no roster data found
        if not player_roster_data:
            print(f"  Warning: No roster data found for {player_name}")
            # Try to find by partial name match
            for roster_name, roster_player in roster_lookup.items():
                if player_name.lower() in roster_name or roster_name in player_name.lower():
                    print(f"  Found partial match: {roster_name}")
                    player_roster_data = roster_player
                    break
        
        card_html = generate_player_card(player_name, jersey_number, regular_season_stats, player_roster_data)
        player_cards.append(card_html)
    
    # Calculate team game stats
    print("Calculating team game-by-game statistics...")
    
    # Get all unique opponents from the games
    opponents = set()
    for game in game_data:
        opponent = game.get('opponent')
        if opponent and opponent.lower() != 'michigan state':
            opponents.add(opponent.lower())
    
    print(f"Fetching opponent data for {len(opponents)} teams (parallel)...")
    
    def fetch_opponent_data(opponent):
        try:
            api_temp = CollegeBasketballAPI()
            opponent_data = api_temp.get_player_game_stats_by_date('2024-11-04', '2025-03-10', opponent)
            if opponent_data:
                return opponent_data
        except Exception as e:
            print(f"Warning: Could not fetch data for {opponent}: {e}")
        return None
    
    # Fetch all opponents in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_opponent_data, opponents)
        opponent_game_data_list = [data for data in results if data]
    
    # Calculate team stats for each game
    date_range = {'start': '2024-11-04', 'end': '2025-03-09'}
    team_game_stats = calculate_team_game_stats(game_data, opponent_game_data_list, api, date_range)
    
    # Generate team stats table
    print(f"Generated stats for {len(team_game_stats)} games")
    team_stats_table = generate_team_stats_table(team_game_stats)
    
    # Calculate team rankings
    rankings = calculate_team_rankings(api)
    rankings_table = generate_rankings_table(rankings)
    
    # Generate HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Michigan State 2024-25 Regular Season Roster Report</title>
    <style>
        body {{
            font-family: 'Arial Narrow', Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
            color: #000;
            line-height: 1.3;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border: 2px solid #000;
        }}
        
        .header h1 {{
            font-size: 24pt;
            font-weight: bold;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .header p {{
            font-size: 12pt;
            font-weight: bold;
        }}
        
        .roster-grid {{
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        .player-card {{
            border: 1px solid black;
            padding: 15px;
            background: white;
            width: 100%;
            display: flex;
            gap: 20px;
            min-height: 200px;
        }}
        
        .card-left {{
            flex: 0 0 200px;
        }}
        
        .card-right {{
            flex: 1;
        }}
        
        .card-header {{
            margin-bottom: 6px;
        }}
        
        .jersey-number {{
            font-size: 48px;
            font-weight: bold;
            line-height: 1;
            margin-bottom: 4px;
        }}
        
        .player-name {{
            font-size: 12pt;
            font-weight: bold;
            text-transform: uppercase;
            line-height: 1.1;
        }}
        
        .player-info {{
            font-size: 10pt;
            margin-bottom: 4px;
        }}
        
        .hometown-info {{
            font-size: 9pt;
            margin-bottom: 4px;
        }}
        
        .last-game {{
            font-size: 8pt;
            font-style: italic;
            color: #333;
        }}
        
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 8pt;
        }}
        
        .stats-table th {{
            background-color: #f0f0f0;
            font-weight: bold;
            text-align: right;
            padding: 4px 6px;
            border: 1px solid #ccc;
        }}
        
        .stats-table td {{
            text-align: right;
            padding: 3px 6px;
            border: 1px solid #ccc;
        }}
        
        .no-data {{
            text-align: center;
            font-style: italic;
            color: #666;
            padding: 20px;
        }}
        
        .team-stats-section {{
            max-width: 1200px;
            margin: 40px auto 20px;
            padding: 20px;
            background: white;
            border: 2px solid #000;
        }}
        
        .team-stats-section h2 {{
            font-size: 18pt;
            font-weight: bold;
            margin: 0 0 10px 0;
            text-align: center;
            text-transform: uppercase;
        }}
        
        .team-stats-section p {{
            font-size: 10pt;
            text-align: center;
            margin: 0 0 15px 0;
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
        
        .team-stats-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 8pt;
        }}
        
        .team-stats-table th {{
            background-color: #333;
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 6px 4px;
            border: 1px solid #000;
            position: sticky;
            top: 0;
        }}
        
        .team-stats-table td {{
            text-align: center;
            padding: 4px;
            border: 1px solid #ccc;
        }}
        
        .team-stats-table tbody tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        .result-win {{
            background-color: #d4edda !important;
            color: #155724;
            font-weight: bold;
        }}
        
        .result-loss {{
            background-color: #f8d7da !important;
            color: #721c24;
            font-weight: bold;
        }}
        
        .margin-positive {{
            color: #28a745;
            font-weight: bold;
        }}
        
        .margin-negative {{
            color: #dc3545;
            font-weight: bold;
        }}
        
        .margin-zero {{
            color: #000;
        }}
        
        .rankings-section {{
            max-width: 800px;
            margin: 40px auto 20px;
            padding: 20px;
            background: white;
            border: 2px solid #000;
        }}
        
        .rankings-section h2 {{
            font-size: 18pt;
            font-weight: bold;
            margin: 0 0 10px 0;
            text-align: center;
            text-transform: uppercase;
        }}
        
        .rankings-section p {{
            font-size: 10pt;
            text-align: center;
            margin: 0 0 15px 0;
        }}
        
        .rankings-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 10pt;
        }}
        
        .rankings-table th {{
            background-color: #333;
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 8px 12px;
            border: 1px solid #000;
        }}
        
        .rankings-table td {{
            padding: 6px 12px;
            border: 1px solid #ccc;
        }}
        
        .rankings-table td:first-child {{
            text-align: left;
            font-weight: 500;
        }}
        
        .rankings-table td:nth-child(2) {{
            text-align: center;
            font-weight: bold;
        }}
        
        .rankings-table td:last-child {{
            text-align: center;
        }}
        
        .rankings-table tbody tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        @media print {{
            body {{
                padding: 10px;
            }}
            
            .player-card {{
                break-inside: avoid;
                page-break-inside: avoid;
                margin-bottom: 15px;
            }}
        }}
        
        @media (max-width: 768px) {{
            .player-card {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .card-left {{
                flex: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>MICHIGAN STATE SPARTANS</h1>
        <p>2024-25 Regular Season Roster Report<br>
        Games: November 4, 2024 - March 9, 2025</p>
    </div>
    
    <div class="roster-grid">
        {"".join(player_cards)}
    </div>
    
    {team_stats_table}
    
    {rankings_table}
</body>
</html>
"""
    
    return html_content


if __name__ == "__main__":
    try:
        html_content = generate_msu_roster_report()
        
        # Save to file
        with open("msu_roster_scouting_report.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print("✅ MSU Roster Scouting Report generated successfully!")
        print("📁 File saved as: msu_roster_scouting_report.html")
        print("🌐 Open the file in your web browser to view the roster!")
        
        # Print API call summary
        if 'api_instance' in globals():
            api_instance.print_api_call_summary()
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()