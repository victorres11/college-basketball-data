#!/usr/bin/env python3
"""
Generate HTML data explorer for Jaxon Kohler
Creates a web page with all the player data embedded
"""

from cbb_api_wrapper import CollegeBasketballAPI
import json
from datetime import datetime


def generate_html_explorer():
    """Generate HTML page with embedded data."""
    
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
    
    print(f"✅ Loaded {len(game_stats)} games of data")
    
    # Sort games by date
    game_stats.sort(key=lambda x: x.get('startDate', ''))
    
    # Calculate some stats
    total_games = len(game_stats)
    total_points = sum(g.get('points', 0) for g in game_stats)
    total_rebounds = sum(g.get('rebounds', {}).get('total', 0) for g in game_stats)
    total_assists = sum(g.get('assists', 0) for g in game_stats)
    
    avg_points = round(total_points / total_games, 1) if total_games > 0 else 0
    avg_rebounds = round(total_rebounds / total_games, 1) if total_games > 0 else 0
    avg_assists = round(total_assists / total_games, 1) if total_games > 0 else 0
    
    # Find best performances
    best_points_game = max(game_stats, key=lambda x: x.get('points', 0))
    best_rebounds_game = max(game_stats, key=lambda x: x.get('rebounds', {}).get('total', 0))
    best_assists_game = max(game_stats, key=lambda x: x.get('assists', 0))
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jaxon Kohler - Michigan State 2024 Season</title>
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
            max-width: 1200px;
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
        
        .nav {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .nav-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }}
        
        .nav-btn {{
            background: #18453b;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }}
        
        .nav-btn:hover {{
            background: #2d5a4f;
            transform: translateY(-2px);
        }}
        
        .nav-btn.active {{
            background: #28a745;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            display: none;
        }}
        
        .section.active {{
            display: block;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #18453b;
        }}
        
        .stat-card h3 {{
            color: #18453b;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2d5a4f;
        }}
        
        .games-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .games-table th,
        .games-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .games-table th {{
            background: #18453b;
            color: white;
            font-weight: bold;
        }}
        
        .games-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .search-box {{
            width: 100%;
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 25px;
            font-size: 16px;
            margin-bottom: 20px;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: #18453b;
        }}
        
        .best-performance {{
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        
        .best-performance h3 {{
            margin-bottom: 15px;
        }}
        
        .performance-item {{
            margin: 10px 0;
            padding: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 5px;
        }}
        
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .month-section {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        
        .month-section h3 {{
            color: #18453b;
            margin-bottom: 15px;
        }}
        
        .game-item {{
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 5px;
            border-left: 3px solid #18453b;
        }}
        
        .export-section {{
            text-align: center;
            margin: 30px 0;
        }}
        
        .export-btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            margin: 0 10px;
            transition: all 0.3s ease;
        }}
        
        .export-btn:hover {{
            background: #0056b3;
            transform: translateY(-2px);
        }}
        
        @media (max-width: 768px) {{
            .nav-buttons {{
                flex-direction: column;
                align-items: center;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .games-table {{
                font-size: 14px;
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
            <p>Michigan State Spartans • 2024 Season</p>
        </div>
        
        <div class="nav">
            <div class="nav-buttons">
                <button class="nav-btn active" onclick="showSection('overview')">📈 Season Overview</button>
                <button class="nav-btn" onclick="showSection('games')">🎮 Game-by-Game</button>
                <button class="nav-btn" onclick="showSection('search')">🔍 Search Games</button>
                <button class="nav-btn" onclick="showSection('analysis')">📊 Analysis</button>
                <button class="nav-btn" onclick="showSection('best')">🏆 Best Games</button>
                <button class="nav-btn" onclick="showSection('calendar')">📅 Calendar</button>
            </div>
        </div>
        
        <div class="content">
            <!-- Season Overview -->
            <div id="overview" class="section active">
                <h2>📈 Season Overview</h2>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Games Played</h3>
                        <div class="stat-value">{total_games}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Total Points</h3>
                        <div class="stat-value">{total_points}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Points Per Game</h3>
                        <div class="stat-value">{avg_points}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Total Rebounds</h3>
                        <div class="stat-value">{total_rebounds}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Rebounds Per Game</h3>
                        <div class="stat-value">{avg_rebounds}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Total Assists</h3>
                        <div class="stat-value">{total_assists}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Assists Per Game</h3>
                        <div class="stat-value">{avg_assists}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Games Started</h3>
                        <div class="stat-value">{sum(1 for g in game_stats if g.get('starter'))}</div>
                    </div>
                </div>
                
                {f'''
                <div class="stat-card" style="grid-column: 1 / -1;">
                    <h3>Shooting Statistics</h3>
                    <p><strong>Field Goals:</strong> {season_stats.get('fieldGoals', {}).get('made', 0)}-{season_stats.get('fieldGoals', {}).get('attempted', 0)} ({season_stats.get('fieldGoals', {}).get('pct', 0)}%)</p>
                    <p><strong>3-Pointers:</strong> {season_stats.get('threePointFieldGoals', {}).get('made', 0)}-{season_stats.get('threePointFieldGoals', {}).get('attempted', 0)} ({season_stats.get('threePointFieldGoals', {}).get('pct', 0)}%)</p>
                    <p><strong>Free Throws:</strong> {season_stats.get('freeThrows', {}).get('made', 0)}-{season_stats.get('freeThrows', {}).get('attempted', 0)} ({season_stats.get('freeThrows', {}).get('pct', 0)}%)</p>
                </div>
                ''' if season_stats else ''}
            </div>
            
            <!-- Game-by-Game -->
            <div id="games" class="section">
                <h2>🎮 Game-by-Game Statistics</h2>
                <table class="games-table">
                    <thead>
                        <tr>
                            <th>Game</th>
                            <th>Date</th>
                            <th>Opponent</th>
                            <th>PTS</th>
                            <th>REB</th>
                            <th>AST</th>
                            <th>MIN</th>
                            <th>Started</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td>{i+1}</td>
                            <td>{game.get('startDate', '')[:10] if game.get('startDate') else 'N/A'}</td>
                            <td>{game.get('opponent', 'N/A')}</td>
                            <td>{game.get('points', 0)}</td>
                            <td>{game.get('rebounds', {}).get('total', 0)}</td>
                            <td>{game.get('assists', 0)}</td>
                            <td>{game.get('minutes', 0)}</td>
                            <td>{'Yes' if game.get('starter') else 'No'}</td>
                        </tr>
                        ''' for i, game in enumerate(game_stats)])}
                    </tbody>
                </table>
            </div>
            
            <!-- Search Games -->
            <div id="search" class="section">
                <h2>🔍 Search Games</h2>
                <input type="text" class="search-box" id="searchInput" placeholder="Search by opponent name..." onkeyup="filterGames()">
                <div id="searchResults"></div>
            </div>
            
            <!-- Analysis -->
            <div id="analysis" class="section">
                <h2>📊 Statistical Analysis</h2>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Scoring Range</h3>
                        <div class="stat-value">{min(g.get('points', 0) for g in game_stats)} - {max(g.get('points', 0) for g in game_stats)}</div>
                        <p>Lowest to highest points in a game</p>
                    </div>
                    <div class="stat-card">
                        <h3>Rebounding Range</h3>
                        <div class="stat-value">{min(g.get('rebounds', {}).get('total', 0) for g in game_stats)} - {max(g.get('rebounds', {}).get('total', 0) for g in game_stats)}</div>
                        <p>Lowest to highest rebounds in a game</p>
                    </div>
                    <div class="stat-card">
                        <h3>High Scoring Games</h3>
                        <div class="stat-value">{len([g for g in game_stats if g.get('points', 0) >= avg_points + 2])}</div>
                        <p>Games with {avg_points + 2}+ points</p>
                    </div>
                    <div class="stat-card">
                        <h3>Double-Digit Games</h3>
                        <div class="stat-value">{len([g for g in game_stats if g.get('points', 0) >= 10])}</div>
                        <p>Games with 10+ points</p>
                    </div>
                </div>
            </div>
            
            <!-- Best Performances -->
            <div id="best" class="section">
                <h2>🏆 Best Performances</h2>
                
                <div class="best-performance">
                    <h3>🔥 Top Scoring Games</h3>
                    {''.join([f'''
                    <div class="performance-item">
                        <strong>{game.get('points', 0)} points</strong> vs {game.get('opponent', 'N/A')} 
                        ({game.get('startDate', '')[:10] if game.get('startDate') else 'N/A'})
                    </div>
                    ''' for game in sorted(game_stats, key=lambda x: x.get('points', 0), reverse=True)[:5]])}
                </div>
                
                <div class="best-performance" style="background: linear-gradient(135deg, #4ecdc4, #44a08d);">
                    <h3>🏀 Top Rebounding Games</h3>
                    {''.join([f'''
                    <div class="performance-item">
                        <strong>{game.get('rebounds', {}).get('total', 0)} rebounds</strong> vs {game.get('opponent', 'N/A')} 
                        ({game.get('startDate', '')[:10] if game.get('startDate') else 'N/A'})
                    </div>
                    ''' for game in sorted(game_stats, key=lambda x: x.get('rebounds', {}).get('total', 0), reverse=True)[:5]])}
                </div>
                
                <div class="best-performance" style="background: linear-gradient(135deg, #f093fb, #f5576c);">
                    <h3>🎯 Top Assist Games</h3>
                    {''.join([f'''
                    <div class="performance-item">
                        <strong>{game.get('assists', 0)} assists</strong> vs {game.get('opponent', 'N/A')} 
                        ({game.get('startDate', '')[:10] if game.get('startDate') else 'N/A'})
                    </div>
                    ''' for game in sorted(game_stats, key=lambda x: x.get('assists', 0), reverse=True)[:5]])}
                </div>
            </div>
            
            <!-- Calendar -->
            <div id="calendar" class="section">
                <h2>📅 Game Calendar</h2>
                {generate_calendar_html(game_stats)}
            </div>
        </div>
    </div>
    
    <script>
        // Game data for JavaScript
        const gameData = {json.dumps(game_stats)};
        
        function showSection(sectionId) {{
            // Hide all sections
            document.querySelectorAll('.section').forEach(section => {{
                section.classList.remove('active');
            }});
            
            // Remove active class from all buttons
            document.querySelectorAll('.nav-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Show selected section
            document.getElementById(sectionId).classList.add('active');
            
            // Add active class to clicked button
            event.target.classList.add('active');
        }}
        
        function filterGames() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const results = gameData.filter(game => 
                game.opponent.toLowerCase().includes(searchTerm)
            );
            
            const resultsHtml = results.map((game, index) => `
                <div class="game-item">
                    <strong>Game ${{index + 1}}:</strong> ${{game.startDate ? game.startDate.substring(0, 10) : 'N/A'}} vs ${{game.opponent || 'N/A'}} 
                    - ${{game.points || 0}}PTS, ${{game.rebounds ? game.rebounds.total || 0 : 0}}REB, ${{game.assists || 0}}AST
                </div>
            `).join('');
            
            document.getElementById('searchResults').innerHTML = resultsHtml || '<p>No games found matching your search.</p>';
        }}
        
        // Initialize search results
        filterGames();
    </script>
</body>
</html>
"""
    
    return html_content


def generate_calendar_html(game_stats):
    """Generate calendar view HTML."""
    # Group games by month
    months = {}
    for game in game_stats:
        date_str = game.get('startDate', '')
        if date_str:
            month = date_str[:7]  # YYYY-MM
            if month not in months:
                months[month] = []
            months[month].append(game)
    
    calendar_html = ""
    for month in sorted(months.keys()):
        games = months[month]
        month_name = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
        
        calendar_html += f'''
        <div class="month-section">
            <h3>📆 {month_name}</h3>
            {''.join([f'''
            <div class="game-item">
                <strong>{game.get('startDate', '')[:10] if game.get('startDate') else 'N/A'}</strong> 
                {'vs' if game.get('isHome') else '@'} {game.get('opponent', 'N/A')} 
                - {game.get('points', 0)}PTS, {game.get('rebounds', {}).get('total', 0)}REB, {game.get('assists', 0)}AST
            </div>
            ''' for game in sorted(games, key=lambda x: x.get('startDate', ''))])}
        </div>
        '''
    
    return calendar_html


if __name__ == "__main__":
    try:
        html_content = generate_html_explorer()
        
        # Save to file
        with open('jaxon_kohler_explorer.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✅ HTML explorer generated successfully!")
        print("📁 File saved as: jaxon_kohler_explorer.html")
        print("🌐 Open the file in your web browser to explore the data!")
        
    except Exception as e:
        print(f"❌ Error generating HTML: {e}")
        print("Make sure your API key is set up correctly.")
