#!/usr/bin/env python3
"""
Generate Compact Scouting Sheet
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
Creates print-ready HTML page with Excel/newspaper aesthetic
"""

from cbb_api_wrapper import CollegeBasketballAPI
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


# Reuse the calculation functions from existing report
# Import them here or copy the essential parts

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
                                player_games.append(player)
                        except:
                            continue
    
    if not player_games:
        return None
    
    player_games.sort(key=lambda x: x.get('startDate', ''))
    games = len(player_games)
    starts = sum(1 for game in player_games if game.get('starter', False))
    
    # Initialize totals
    fgm = fga = three_pm = three_pa = ftm = fta = 0
    or_reb = dr_reb = assists = turnovers = steals = blocks = fouls = minutes = points = 0
    
    for game in player_games:
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
    ratio = apg if turnovers > 0 else 0  # AST/TO ratio
    
    # Get last game stats
    last_game = player_games[-1] if player_games else None
    last_game_stats = ""
    if last_game:
        last_fg_data = last_game.get('fieldGoals', {})
        last_three = last_game.get('threePointFieldGoals', {})
        last_ft = last_game.get('freeThrows', {})
        last_reb = last_game.get('rebounds', {})
        
        last_game_stats = f"{last_game.get('points', 0)}p, {last_reb.get('total', 0)}r, {last_game.get('assists', 0)}a, {last_game.get('turnovers', 0)}to, {last_game.get('steals', 0)}s, {last_game.get('blocks', 0)}b, {last_fg_data.get('made', 0)}-{last_fg_data.get('attempted', 0)}fg, {last_ft.get('made', 0)}-{last_ft.get('attempted', 0)}ft, ({last_three.get('made', 0)}-{last_three.get('attempted', 0)})3p, [{last_game.get('minutes', 0)}]"
    
    return {
        'games': games, 'starts': starts,
        'fgm': fgm, 'fga': fga, 'fg_pct': fg_pct,
        'three_pm': three_pm, 'three_pa': three_pa, 'three_pct': three_pct,
        'ftm': ftm, 'fta': fta, 'ft_pct': ft_pct,
        'or_reb': or_reb, 'dr_reb': dr_reb, 'total_reb': total_reb, 'rpg': rpg,
        'assists': assists, 'apg': apg,
        'turnovers': turnovers, 'steals': steals, 'spg': spg,
        'blocks': blocks, 'bpg': bpg,
        'points': points, 'ppg': ppg,
        'minutes': minutes, 'mpg': mpg,
        'ratio': ratio,
        'last_game': last_game_stats
    }


def generate_compact_player_card(player_name, jersey_number, stats, roster_data=None, is_freshman=False, player_mpg=0):
    """Generate compact player card as single-row layout."""
    
    if not stats:
        return ""
    
    # Extract player details
    height_str = "N/A"
    hometown_str = "N/A"
    high_school_str = "N/A"
    class_year_str = "N/A"
    position = "N/A"
    
    if roster_data and isinstance(roster_data, dict):
        height_inches = roster_data.get('height')
        if height_inches:
            feet = height_inches // 12
            inches = height_inches % 12
            height_str = f"{feet}-{inches}"
        
        hometown = roster_data.get('hometown', {})
        city = hometown.get('city', '')
        state = hometown.get('state', '')
        if city and state:
            hometown_str = f"{city}, {state}"
        
        high_school_str = roster_data.get('highSchool', 'N/A')
        
        start_season = roster_data.get('startSeason')
        end_season = roster_data.get('endSeason')
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
        
        position = roster_data.get('position', 'N/A')
    
    # Format stats for display
    games = stats['games']
    starts = stats['starts']
    fgm = stats['fgm']
    fga = stats['fga']
    fg_pct = f"{stats['fg_pct']:.1f}"
    three_pm = stats['three_pm']
    three_pa = stats['three_pa']
    three_pct = f"{stats['three_pct']:.1f}"
    ftm = stats['ftm']
    fta = stats['fta']
    ft_pct = f"{stats['ft_pct']:.1f}"
    or_reb = stats['or_reb']
    dr_reb = stats['dr_reb']
    total_reb = stats['total_reb']
    dq = 0  # Placeholder
    assists = stats['assists']
    apg = f"{stats['apg']:.1f}"
    ratio = f"{stats['ratio']:.1f}"
    spg = f"{stats['spg']:.1f}"
    blocks = stats['blocks']
    bpg = f"{stats['bpg']:.1f}"
    mpg = f"{stats['mpg']:.0f}"
    rpg = f"{stats['rpg']:.1f}"
    ppg = f"{stats['ppg']:.1f}"
    last_game_stats = stats.get('last_game', 'No data')
    
    # Determine if freshman for styling
    freshman_class = "freshman-card" if is_freshman else ""
    
    card_html = f'''
    <div class="compact-player-card {freshman_class}">
        <div class="card-header-compact">
            <span class="jersey-large">{jersey_number}</span>
            <div class="name-section">
                <div class="player-name-compact {"freshman-name" if is_freshman else ""}">{player_name.upper()}</div>
                <div class="player-bio-compact">{class_year_str} {height_str} {position}</div>
            </div>
        </div>
        
        <div class="bio-line-compact">{hometown_str} ({high_school_str})</div>
        <div class="last-game-compact">{last_game_stats}</div>
        
        <table class="stats-table-compact">
            <tr class="header-row">
                <td>G</td><td>GS</td><td>FG-FGA</td><td>FG%</td><td>3P-3PA</td><td>FT-FTA</td><td>OR</td><td>DR</td><td>Reb</td><td>DQ</td><td>AST</td><td>APG</td><td>ratio</td><td>SPG</td><td>BLK</td><td>BPG</td><td>MPG</td>
            </tr>
            <tr class="value-row">
                <td>{games}</td><td>{starts}</td><td>{fgm}-{fga}</td><td>{fg_pct}%</td><td>{three_pm}-{three_pa}</td><td>{ftm}-{fta}</td><td>{or_reb}</td><td>{dr_reb}</td><td>{total_reb}</td><td>{dq}</td><td>{assists}</td><td>{apg}</td><td>{ratio}</td><td>{spg}</td><td>{blocks}</td><td>{bpg}</td><td>{mpg}</td>
            </tr>
        </table>
        
        <div class="summary-line">3P% {three_pct}% FT% {ft_pct}% RPG {rpg} PPG {ppg}</div>
        
        <div class="foul-circles">
            <span class="foul-circle"></span>
            <span class="foul-circle"></span>
            <span class="foul-circle"></span>
            <span class="foul-circle"></span>
            <span class="foul-circle"></span>
        </div>
    </div>
    '''
    
    return card_html


def generate_header_section():
    """Generate top header with team info and placeholders."""
    return '''
    <div class="page-header">
        <div class="team-header">
            <h1 class="team-name">Michigan State</h1>
            <div class="records-grid">
                <div class="record-line">
                    <span class="record-label">Overall:</span>
                    <span class="record-value">[OVERALL: TBD]</span>
                    <span class="record-label">Conference:</span>
                    <span class="record-value">[CONF: TBD]</span>
                </div>
                <div class="record-line">
                    <span class="record-item">KP:</span><span>[KP: TBD]</span>
                    <span class="record-item">NET:</span><span>[NET: TBD]</span>
                    <span class="record-item">Hm:</span><span>[HOME: TBD]</span>
                    <span class="record-item">Rd:</span><span>[ROAD: TBD]</span>
                    <span class="record-item">Neu:</span><span>[NEUTRAL: TBD]</span>
                </div>
                <div class="record-line">
                    <span class="record-item">Q1:</span><span>[Q1: TBD]</span>
                    <span class="record-item">Q2:</span><span>[Q2: TBD]</span>
                    <span class="record-item">Q3:</span><span>[Q3: TBD]</span>
                    <span class="record-item">Q4:</span><span>[Q4: TBD]</span>
                    <span class="record-item">1P:</span><span>[1P: TBD]</span>
                    <span class="record-item">2P:</span><span>[2P: TBD]</span>
                </div>
            </div>
        </div>
        
        <div class="coach-section">
            <div class="coach-line">[COACH: TBD] - [YEARS] ([TOTAL])</div>
            <div class="coach-notes">[Coach achievements and notes to be added]</div>
        </div>
    </div>
    '''


def generate_scouting_sheet():
    """Generate the compact scouting sheet HTML."""
    print("Loading Michigan State data...")
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
    game_data = api.get_player_game_stats_by_date('2024-11-04', '2025-03-10', "michigan state")
    roster_data = api.get_team_roster(2025, "michigan state")
    recruiting_data = api.get_recruiting_players("Michigan State")
    
    # Create lookups
    roster_lookup = {}
    if roster_data and 'players' in roster_data[0]:
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
            for recruit_name, recruit_data in recruiting_lookup.items():
                if player_name in recruit_name or recruit_name in player_name:
                    player_data['highSchool'] = recruit_data.get('school', 'N/A')
                    break
    
    # Separate players by MPG
    main_players = []
    bench_players = []
    
    for player_info in players:
        player_name = player_info["name"]
        jersey_number = player_info["number"]
        
        stats = calculate_regular_season_stats(player_name, game_data)
        if not stats:
            continue
        
        player_roster_data = roster_lookup.get(player_name.lower(), {})
        
        # Determine if freshman
        is_freshman = False
        start_season = player_roster_data.get('startSeason')
        end_season = player_roster_data.get('endSeason')
        if start_season and end_season:
            years_at_school = end_season - start_season + 1
            is_freshman = (years_at_school == 1)
        
        player_mpg = stats.get('mpg', 0)
        player_data = {
            'name': player_name,
            'number': jersey_number,
            'stats': stats,
            'roster': player_roster_data,
            'freshman': is_freshman,
            'mpg': player_mpg
        }
        
        if player_mpg >= 10:
            main_players.append(player_data)
        else:
            bench_players.append(player_data)
    
    # Sort main players by MPG (descending)
    main_players.sort(key=lambda x: x['mpg'], reverse=True)
    
    # Sort bench players by MPG (descending)
    bench_players.sort(key=lambda x: x['mpg'], reverse=True)
    
    # Generate HTML for main players (full cards)
    main_cards_html = []
    for player_data in main_players:
        card_html = generate_compact_player_card(
            player_data['name'],
            player_data['number'],
            player_data['stats'],
            player_data['roster'],
            player_data['freshman'],
            player_data['mpg']
        )
        if card_html:
            main_cards_html.append(card_html)
    
    # Generate HTML for bench players (condensed cards)
    bench_cards_html = []
    for player_data in bench_players:
        # Generate condensed version
        card_html = generate_compact_player_card(
            player_data['name'],
            player_data['number'],
            player_data['stats'],
            player_data['roster'],
            player_data['freshman'],
            player_data['mpg']
        )
        if card_html:
            bench_cards_html.append(card_html)
    
    # Generate HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Michigan State Scouting Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Arial Narrow', Arial, sans-serif;
            width: 8.5in;
            margin: 0;
            padding: 0;
            background: white;
            color: black;
            line-height: 1.2;
        }}
        
        .content-container {{
            padding: 0.15in;
        }}
        
        .page-header {{
            margin-bottom: 0.15in;
            border-bottom: 2px solid black;
            padding-bottom: 0.1in;
        }}
        
        .team-name {{
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 0.05in;
        }}
        
        .records-grid {{
            font-size: 9pt;
        }}
        
        .record-line {{
            display: flex;
            gap: 0.2in;
            margin-bottom: 0.03in;
        }}
        
        .record-label {{
            font-weight: bold;
        }}
        
        .record-item {{
            margin-right: 0.05in;
        }}
        
        .coach-section {{
            margin-top: 0.08in;
            font-size: 9pt;
        }}
        
        .coach-line {{
            font-weight: bold;
            margin-bottom: 0.02in;
        }}
        
        .coach-notes {{
            font-size: 8pt;
        }}
        
        .player-cards-grid {{
            margin-bottom: 0.3in;
            padding-left: 0.1in;
            padding-right: 0.1in;
        }}
        
        .compact-player-card {{
            border: 1px solid black;
            padding: 4px;
            width: 100%;
            background: white;
            margin-bottom: 0.1in;
            margin-left: 0;
            margin-right: auto;
        }}
        
        .freshman-card {{
            background-color: #e8f5e9 !important;
        }}
        
        .freshman-name {{
            color: #2e7d32 !important;
            font-weight: bold;
        }}
        
        .bench-section {{
            margin-top: 0.3in;
            margin-bottom: 0.3in;
        }}
        
        .bench-header {{
            font-size: 11pt;
            font-weight: bold;
            margin-bottom: 0.1in;
            padding-bottom: 0.05in;
            border-bottom: 1px solid black;
        }}
        
        .card-header-compact {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 3px;
        }}
        
        .jersey-large {{
            font-size: 42pt;
            font-weight: bold;
            line-height: 1;
            margin-right: 5px;
        }}
        
        .name-section {{
            flex: 1;
        }}
        
        .player-name-compact {{
            font-size: 12pt;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 2px;
        }}
        
        .player-bio-compact {{
            font-size: 9pt;
        }}
        
        .bio-line-compact {{
            font-size: 8pt;
            margin-bottom: 3px;
        }}
        
        .last-game-compact {{
            font-size: 7.5pt;
            margin-bottom: 5px;
        }}
        
        .stats-table-compact {{
            width: 100%;
            border-collapse: collapse;
            font-size: 6.5pt;
            margin-bottom: 4px;
        }}
        
        .stats-table-compact td {{
            border: 0.5px solid #333;
            padding: 1px;
            text-align: right;
        }}
        
        .stats-table-compact .header-row td {{
            font-weight: bold;
            text-align: center;
            background-color: #f5f5f5;
        }}
        
        .summary-line {{
            font-size: 8pt;
            text-align: right;
            margin-bottom: 3px;
        }}
        
        .foul-circles {{
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-top: 5px;
        }}
        
        .foul-circle {{
            width: 10px;
            height: 10px;
            border: 1px solid black;
            border-radius: 50%;
            display: inline-block;
        }}
        
        /* Keep existing table styles from original report */
        .team-stats-section {{
            margin-top: 0.4in;
        }}
        
        .team-stats-section h2 {{
            font-size: 12pt;
            margin-bottom: 0.1in;
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
        
        .team-stats-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 8pt;
        }}
        
        .team-stats-table th,
        .team-stats-table td {{
            border: 0.5px solid #333;
            padding: 2px 4px;
            text-align: center;
        }}
        
        .team-stats-table th {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    {generate_header_section()}
    
    <div class="player-cards-grid">
        {''.join(main_cards_html)}
    </div>
    
    {'<div class="bench-section"><h2 class="bench-header">Bench Players (&lt;10 MPG)</h2><div class="player-cards-grid">' + ''.join(bench_cards_html) + '</div></div>' if bench_cards_html else ''}
    
    <!-- Placeholder for existing tables -->
    <div class="team-stats-section">
        <p style="font-size: 10pt; text-align: center; font-style: italic;">
            [Game-by-game team statistics and rankings tables will be added below]
        </p>
    </div>
</body>
</html>
    '''
    
    with open('msu_scouting_sheet.html', 'w') as f:
        f.write(html_content)
    
    print("✅ Compact scouting sheet generated successfully!")
    print("📁 File saved as: msu_scouting_sheet.html")
    
    # Print API call summary
    if hasattr(api, 'get_api_call_summary'):
        api.print_api_call_summary()


if __name__ == '__main__':
    generate_scouting_sheet()

