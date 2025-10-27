#!/usr/bin/env python3
"""
Generate comprehensive HTML page with all Jaxon Kohler data points
"""

from cbb_api_wrapper import CollegeBasketballAPI
import json
from datetime import datetime


def generate_comprehensive_html():
    """Generate comprehensive HTML page with all data points."""
    
    # Load data
    print("Loading Jaxon Kohler's data...")
    api = CollegeBasketballAPI()
    
    # Get season stats
    msu_players = api.get_player_season_stats(2024, "michigan state")
    season_stats = None
    for player in msu_players:
        if 'jaxon' in player.get('name', '').lower() and 'kohler' in player.get('name', '').lower():
            season_stats = player
            break
    
    # Get per-game stats
    game_data = api.get_player_game_stats_by_date('2024-11-04', '2025-03-10', "michigan state")
    game_stats = []
    for game_record in game_data:
        if 'players' in game_record:
            for player in game_record['players']:
                if 'jaxon' in player.get('name', '').lower() and 'kohler' in player.get('name', '').lower():
                    player_data = player.copy()
                    player_data['gameId'] = game_record.get('gameId')
                    player_data['startDate'] = game_record.get('startDate')
                    player_data['opponent'] = game_record.get('opponent')
                    player_data['isHome'] = game_record.get('isHome')
                    game_stats.append(player_data)
    
    # Sort games by date
    game_stats.sort(key=lambda x: x.get('startDate', ''))
    
    print(f"✅ Loaded {len(game_stats)} games of data")
    
    # Calculate totals and averages
    total_games = len(game_stats)
    total_starts = sum(1 for g in game_stats if g.get('starter'))
    
    # Field Goals
    total_fgm = sum(g.get('fieldGoals', {}).get('made', 0) for g in game_stats)
    total_fga = sum(g.get('fieldGoals', {}).get('attempted', 0) for g in game_stats)
    fg_pct = round(total_fgm / total_fga * 100, 1) if total_fga > 0 else 0
    
    # 3-Pointers
    total_3pm = sum(g.get('threePointFieldGoals', {}).get('made', 0) for g in game_stats)
    total_3pa = sum(g.get('threePointFieldGoals', {}).get('attempted', 0) for g in game_stats)
    three_pct = round(total_3pm / total_3pa * 100, 1) if total_3pa > 0 else 0
    
    # Free Throws
    total_ftm = sum(g.get('freeThrows', {}).get('made', 0) for g in game_stats)
    total_fta = sum(g.get('freeThrows', {}).get('attempted', 0) for g in game_stats)
    ft_pct = round(total_ftm / total_fta * 100, 1) if total_fta > 0 else 0
    
    # Rebounds
    total_or = sum(g.get('rebounds', {}).get('offensive', 0) for g in game_stats)
    total_dr = sum(g.get('rebounds', {}).get('defensive', 0) for g in game_stats)
    total_reb = total_or + total_dr
    rpg = round(total_reb / total_games, 1) if total_games > 0 else 0
    
    # Other stats
    total_fouls = sum(g.get('fouls', 0) for g in game_stats)
    total_assists = sum(g.get('assists', 0) for g in game_stats)
    apg = round(total_assists / total_games, 1) if total_games > 0 else 0
    
    # Assist/Turnover ratio
    total_turnovers = sum(g.get('turnovers', 0) for g in game_stats)
    ast_to_ratio = round(total_assists / total_turnovers, 2) if total_turnovers > 0 else 0
    
    # Steals
    total_steals = sum(g.get('steals', 0) for g in game_stats)
    spg = round(total_steals / total_games, 1) if total_games > 0 else 0
    
    # Blocks
    total_blocks = sum(g.get('blocks', 0) for g in game_stats)
    bpg = round(total_blocks / total_games, 1) if total_games > 0 else 0
    
    # Minutes and Points
    total_minutes = sum(g.get('minutes', 0) for g in game_stats)
    mpg = round(total_minutes / total_games, 1) if total_games > 0 else 0
    
    total_points = sum(g.get('points', 0) for g in game_stats)
    ppg = round(total_points / total_games, 1) if total_games > 0 else 0
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jaxon Kohler - Complete Statistics</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #18453b 0%, #2d5a4f 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .season-summary {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            border-left: 5px solid #18453b;
        }}
        
        .season-summary h2 {{
            color: #18453b;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-item {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid #e9ecef;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 5px;
            font-weight: bold;
        }}
        
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #18453b;
        }}
        
        .games-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }}
        
        .games-table th,
        .games-table td {{
            padding: 8px 6px;
            text-align: center;
            border: 1px solid #dee2e6;
        }}
        
        .games-table th {{
            background: #18453b;
            color: white;
            font-weight: bold;
            font-size: 12px;
        }}
        
        .games-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        .games-table tr:hover {{
            background: #e3f2fd;
        }}
        
        .game-number {{
            font-weight: bold;
            color: #18453b;
        }}
        
        .date-cell {{
            font-size: 11px;
            white-space: nowrap;
        }}
        
        .opponent-cell {{
            text-align: left;
            font-weight: 500;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .percentage {{
            font-weight: bold;
        }}
        
        .high-value {{
            background: #d4edda;
            font-weight: bold;
        }}
        
        .low-value {{
            background: #f8d7da;
            font-weight: bold;
        }}
        
        .summary-section {{
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        
        .summary-section h3 {{
            margin-bottom: 15px;
            font-size: 1.4em;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        
        .summary-item {{
            text-align: center;
        }}
        
        .summary-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        
        .summary-value {{
            font-size: 1.3em;
            font-weight: bold;
        }}
        
        @media (max-width: 768px) {{
            .games-table {{
                font-size: 11px;
            }}
            
            .games-table th,
            .games-table td {{
                padding: 4px 2px;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏀 Jaxon Kohler</h1>
            <p>Michigan State Spartans • 2024 Season • Complete Statistics</p>
        </div>
        
        <div class="content">
            <div class="season-summary">
                <h2>📊 Season Summary</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-label">Games Played</div>
                        <div class="stat-value">{total_games}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Games Started</div>
                        <div class="stat-value">{total_starts}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Field Goals</div>
                        <div class="stat-value">{total_fgm}-{total_fga}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Field Goal %</div>
                        <div class="stat-value">{fg_pct}%</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">3-Pointers</div>
                        <div class="stat-value">{total_3pm}-{total_3pa}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">3-Point %</div>
                        <div class="stat-value">{three_pct}%</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Free Throws</div>
                        <div class="stat-value">{total_ftm}-{total_fta}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Free Throw %</div>
                        <div class="stat-value">{ft_pct}%</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Offensive Rebounds</div>
                        <div class="stat-value">{total_or}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Defensive Rebounds</div>
                        <div class="stat-value">{total_dr}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Total Rebounds</div>
                        <div class="stat-value">{total_reb}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Rebounds Per Game</div>
                        <div class="stat-value">{rpg}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Fouls</div>
                        <div class="stat-value">{total_fouls}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Assists</div>
                        <div class="stat-value">{total_assists}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Assists Per Game</div>
                        <div class="stat-value">{apg}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">A/T Ratio</div>
                        <div class="stat-value">{ast_to_ratio}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Steals</div>
                        <div class="stat-value">{total_steals}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Steals Per Game</div>
                        <div class="stat-value">{spg}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Blocks</div>
                        <div class="stat-value">{total_blocks}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Blocks Per Game</div>
                        <div class="stat-value">{bpg}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Minutes</div>
                        <div class="stat-value">{total_minutes}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Minutes Per Game</div>
                        <div class="stat-value">{mpg}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Points</div>
                        <div class="stat-value">{total_points}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Points Per Game</div>
                        <div class="stat-value">{ppg}</div>
                    </div>
                </div>
            </div>
            
            <div class="summary-section">
                <h3>🎯 Key Performance Metrics</h3>
                <div class="summary-grid">
                    <div class="summary-item">
                        <div class="summary-label">Games Started</div>
                        <div class="summary-value">{total_starts}/{total_games}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Start %</div>
                        <div class="summary-value">{round(total_starts/total_games*100, 1)}%</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">FG%</div>
                        <div class="summary-value">{fg_pct}%</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">3P%</div>
                        <div class="summary-value">{three_pct}%</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">FT%</div>
                        <div class="summary-value">{ft_pct}%</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">A/T Ratio</div>
                        <div class="summary-value">{ast_to_ratio}</div>
                    </div>
                </div>
            </div>
            
            <h2>🎮 Game-by-Game Statistics</h2>
            <table class="games-table">
                <thead>
                    <tr>
                        <th>G</th>
                        <th>GS</th>
                        <th>Date</th>
                        <th>Opponent</th>
                        <th>FG-FGA</th>
                        <th>FG%</th>
                        <th>3P-3PA</th>
                        <th>FT-FTA</th>
                        <th>OR</th>
                        <th>DR</th>
                        <th>Reb</th>
                        <th>DQ</th>
                        <th>AST</th>
                        <th>APG</th>
                        <th>Ratio</th>
                        <th>SPG</th>
                        <th>BLK</th>
                        <th>BPG</th>
                        <th>MPG</th>
                        <th>PPG</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_game_rows(game_stats)}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content


def generate_game_rows(game_stats):
    """Generate table rows for each game."""
    rows = []
    
    for i, game in enumerate(game_stats, 1):
        # Basic info
        g = i
        gs = 1 if game.get('starter') else 0
        date = game.get('startDate', '')[:10] if game.get('startDate') else 'N/A'
        opponent = game.get('opponent', 'N/A')
        
        # Field Goals
        fg_data = game.get('fieldGoals', {})
        fgm = fg_data.get('made', 0)
        fga = fg_data.get('attempted', 0)
        fg_pct = fg_data.get('pct', 0)
        
        # 3-Pointers
        three_data = game.get('threePointFieldGoals', {})
        three_pm = three_data.get('made', 0)
        three_pa = three_data.get('attempted', 0)
        
        # Free Throws
        ft_data = game.get('freeThrows', {})
        ftm = ft_data.get('made', 0)
        fta = ft_data.get('attempted', 0)
        
        # Rebounds
        reb_data = game.get('rebounds', {})
        or_reb = reb_data.get('offensive', 0)
        dr_reb = reb_data.get('defensive', 0)
        total_reb = or_reb + dr_reb
        
        # Other stats
        fouls = game.get('fouls', 0)
        assists = game.get('assists', 0)
        turnovers = game.get('turnovers', 0)
        steals = game.get('steals', 0)
        blocks = game.get('blocks', 0)
        minutes = game.get('minutes', 0)
        points = game.get('points', 0)
        
        # Calculate per-game averages (same as game values for individual games)
        apg = assists
        spg = steals
        bpg = blocks
        mpg = minutes
        ppg = points
        
        # Assist/Turnover ratio
        ast_to_ratio = round(assists / turnovers, 2) if turnovers > 0 else 0
        
        # Add CSS classes for highlighting
        fg_class = "high-value" if fg_pct >= 60 else "low-value" if fg_pct <= 30 and fga > 0 else ""
        points_class = "high-value" if points >= 10 else ""
        
        row = f'''
        <tr>
            <td class="game-number">{g}</td>
            <td>{gs}</td>
            <td class="date-cell">{date}</td>
            <td class="opponent-cell">{opponent}</td>
            <td>{fgm}-{fga}</td>
            <td class="percentage {fg_class}">{fg_pct:.1f}%</td>
            <td>{three_pm}-{three_pa}</td>
            <td>{ftm}-{fta}</td>
            <td>{or_reb}</td>
            <td>{dr_reb}</td>
            <td>{total_reb}</td>
            <td>{fouls}</td>
            <td>{assists}</td>
            <td>{apg}</td>
            <td>{ast_to_ratio}</td>
            <td>{spg}</td>
            <td>{blocks}</td>
            <td>{bpg}</td>
            <td>{mpg}</td>
            <td class="{points_class}">{ppg}</td>
        </tr>
        '''
        rows.append(row)
    
    return ''.join(rows)


if __name__ == "__main__":
    try:
        html_content = generate_comprehensive_html()
        
        # Save to file
        with open('jaxon_kohler_complete_stats.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✅ Complete statistics HTML generated successfully!")
        print("📁 File saved as: jaxon_kohler_complete_stats.html")
        print("🌐 Open the file in your web browser to view all statistics!")
        
    except Exception as e:
        print(f"❌ Error generating HTML: {e}")
        print("Make sure your API key is set up correctly.")
