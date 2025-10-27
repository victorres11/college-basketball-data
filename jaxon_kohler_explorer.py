#!/usr/bin/env python3
"""
Jaxon Kohler Data Explorer
Interactive script to navigate and explore player data from the College Basketball Data API
"""

from cbb_api_wrapper import CollegeBasketballAPI
import json
from datetime import datetime
from typing import Dict, List, Any


class PlayerDataExplorer:
    """Interactive explorer for player data."""
    
    def __init__(self):
        self.api = CollegeBasketballAPI()
        self.player_name = "Jaxon Kohler"
        self.team = "michigan state"
        self.season = 2024
        
        # Load player data
        self.season_stats = None
        self.game_stats = []
        self.load_data()
    
    def load_data(self):
        """Load all player data from API."""
        print("Loading Jaxon Kohler's data...")
        
        # Get season stats
        msu_players = self.api.get_player_season_stats(self.season, self.team)
        for player in msu_players:
            if 'jaxon' in player.get('name', '').lower() and 'kohler' in player.get('name', '').lower():
                self.season_stats = player
                break
        
        # Get per-game stats
        game_data = self.api.get_player_game_stats_by_date('2024-11-04', '2025-03-09', self.team)
        for game_record in game_data:
            if 'players' in game_record:
                for player in game_record['players']:
                    if 'jaxon' in player.get('name', '').lower() and 'kohler' in player.get('name', '').lower():
                        # Add game context
                        player_data = player.copy()
                        player_data['gameId'] = game_record.get('gameId')
                        player_data['startDate'] = game_record.get('startDate')
                        player_data['opponent'] = game_record.get('opponent')
                        player_data['isHome'] = game_record.get('isHome')
                        self.game_stats.append(player_data)
        
        print(f"✅ Loaded {len(self.game_stats)} games of data")
    
    def display_main_menu(self):
        """Display the main navigation menu."""
        print("\n" + "="*60)
        print(f"🏀 {self.player_name.upper()} - MICHIGAN STATE {self.season} SEASON")
        print("="*60)
        print("\n📊 NAVIGATION MENU:")
        print("1. 📈 Season Overview")
        print("2. 🎮 Game-by-Game Stats")
        print("3. 🔍 Search Games")
        print("4. 📊 Statistical Analysis")
        print("5. 🏆 Best Performances")
        print("6. 📅 Game Calendar")
        print("7. 💾 Export Data")
        print("8. ❓ Help")
        print("0. 🚪 Exit")
        print("\n" + "-"*60)
    
    def season_overview(self):
        """Display season overview statistics."""
        if not self.season_stats:
            print("❌ No season data available")
            return
        
        print(f"\n📈 {self.player_name.upper()} - SEASON OVERVIEW")
        print("="*50)
        
        # Basic Info
        print(f"\n👤 PLAYER INFO:")
        print(f"   Name: {self.season_stats.get('name', 'N/A')}")
        print(f"   Position: {self.season_stats.get('position', 'N/A')}")
        print(f"   Team: {self.season_stats.get('team', 'N/A')}")
        print(f"   Conference: {self.season_stats.get('conference', 'N/A')}")
        
        # Games
        games = self.season_stats.get('games', 0)
        starts = self.season_stats.get('starts', 0)
        print(f"\n🎮 GAMES:")
        print(f"   Games Played: {games}")
        print(f"   Games Started: {starts}")
        print(f"   Started %: {(starts/games*100):.1f}%" if games > 0 else "   Started %: N/A")
        
        # Scoring
        points = self.season_stats.get('points', 0)
        ppg = round(points / games, 1) if games > 0 else 0
        print(f"\n🏀 SCORING:")
        print(f"   Total Points: {points}")
        print(f"   Points Per Game: {ppg}")
        
        # Shooting
        fg = self.season_stats.get('fieldGoals', {})
        fg_pct = fg.get('pct', 0)
        print(f"\n🎯 SHOOTING:")
        print(f"   Field Goals: {fg.get('made', 0)}-{fg.get('attempted', 0)} ({fg_pct}%)")
        
        three_pt = self.season_stats.get('threePointFieldGoals', {})
        three_pct = three_pt.get('pct', 0)
        print(f"   3-Pointers: {three_pt.get('made', 0)}-{three_pt.get('attempted', 0)} ({three_pct}%)")
        
        ft = self.season_stats.get('freeThrows', {})
        ft_pct = ft.get('pct', 0)
        print(f"   Free Throws: {ft.get('made', 0)}-{ft.get('attempted', 0)} ({ft_pct}%)")
        
        # Rebounds
        rebounds = self.season_stats.get('rebounds', {})
        rpg = round(rebounds.get('total', 0) / games, 1) if games > 0 else 0
        print(f"\n🏀 REBOUNDING:")
        print(f"   Total Rebounds: {rebounds.get('total', 0)}")
        print(f"   Offensive: {rebounds.get('offensive', 0)}")
        print(f"   Defensive: {rebounds.get('defensive', 0)}")
        print(f"   Rebounds Per Game: {rpg}")
        
        # Other Stats
        assists = self.season_stats.get('assists', 0)
        apg = round(assists / games, 1) if games > 0 else 0
        steals = self.season_stats.get('steals', 0)
        blocks = self.season_stats.get('blocks', 0)
        turnovers = self.season_stats.get('turnovers', 0)
        fouls = self.season_stats.get('fouls', 0)
        
        print(f"\n📊 OTHER STATS:")
        print(f"   Assists: {assists} ({apg} per game)")
        print(f"   Steals: {steals}")
        print(f"   Blocks: {blocks}")
        print(f"   Turnovers: {turnovers}")
        print(f"   Fouls: {fouls}")
        
        # Advanced Stats
        print(f"\n🔬 ADVANCED METRICS:")
        print(f"   Offensive Rating: {self.season_stats.get('offensiveRating', 'N/A')}")
        print(f"   Defensive Rating: {self.season_stats.get('defensiveRating', 'N/A')}")
        print(f"   Usage Rate: {self.season_stats.get('usage', 'N/A')}%")
        print(f"   True Shooting %: {self.season_stats.get('trueShootingPct', 'N/A')}")
        print(f"   Effective FG %: {self.season_stats.get('effectiveFieldGoalPct', 'N/A')}%")
    
    def game_by_game_stats(self):
        """Display game-by-game statistics."""
        if not self.game_stats:
            print("❌ No game data available")
            return
        
        print(f"\n🎮 {self.player_name.upper()} - GAME-BY-GAME STATS")
        print("="*60)
        
        # Sort games by date
        sorted_games = sorted(self.game_stats, key=lambda x: x.get('startDate', ''))
        
        print(f"\n📅 Showing all {len(sorted_games)} games:")
        print("\nGame | Date       | Opponent        | PTS | REB | AST | MIN | Starter")
        print("-" * 70)
        
        for i, game in enumerate(sorted_games, 1):
            date = game.get('startDate', '')[:10] if game.get('startDate') else 'N/A'
            opponent = game.get('opponent', 'N/A')[:15]
            points = game.get('points', 0)
            rebounds = game.get('rebounds', {}).get('total', 0)
            assists = game.get('assists', 0)
            minutes = game.get('minutes', 0)
            starter = "Yes" if game.get('starter') else "No"
            
            print(f"{i:4} | {date} | {opponent:<15} | {points:3} | {rebounds:3} | {assists:3} | {minutes:3} | {starter}")
    
    def search_games(self):
        """Search and filter games."""
        if not self.game_stats:
            print("❌ No game data available")
            return
        
        print(f"\n🔍 SEARCH GAMES")
        print("="*30)
        print("Search options:")
        print("1. By opponent")
        print("2. By points scored")
        print("3. By rebounds")
        print("4. By date range")
        print("5. By starter status")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            opponent = input("Enter opponent name: ").strip().lower()
            filtered = [g for g in self.game_stats if opponent in g.get('opponent', '').lower()]
            self.display_filtered_games(filtered, f"Games vs {opponent.title()}")
        
        elif choice == "2":
            try:
                min_points = int(input("Enter minimum points: "))
                filtered = [g for g in self.game_stats if g.get('points', 0) >= min_points]
                self.display_filtered_games(filtered, f"Games with {min_points}+ points")
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == "3":
            try:
                min_rebounds = int(input("Enter minimum rebounds: "))
                filtered = [g for g in self.game_stats if g.get('rebounds', {}).get('total', 0) >= min_rebounds]
                self.display_filtered_games(filtered, f"Games with {min_rebounds}+ rebounds")
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == "4":
            start_date = input("Enter start date (YYYY-MM-DD): ").strip()
            end_date = input("Enter end date (YYYY-MM-DD): ").strip()
            filtered = [g for g in self.game_stats if start_date <= g.get('startDate', '')[:10] <= end_date]
            self.display_filtered_games(filtered, f"Games from {start_date} to {end_date}")
        
        elif choice == "5":
            starter_only = input("Show only games started? (y/n): ").strip().lower() == 'y'
            filtered = [g for g in self.game_stats if g.get('starter') == starter_only]
            status = "started" if starter_only else "not started"
            self.display_filtered_games(filtered, f"Games {status}")
    
    def display_filtered_games(self, games: List[Dict], title: str):
        """Display filtered game results."""
        if not games:
            print(f"❌ No games found for: {title}")
            return
        
        print(f"\n📊 {title.upper()} ({len(games)} games)")
        print("="*50)
        
        for game in games:
            date = game.get('startDate', '')[:10]
            opponent = game.get('opponent', 'N/A')
            points = game.get('points', 0)
            rebounds = game.get('rebounds', {}).get('total', 0)
            assists = game.get('assists', 0)
            minutes = game.get('minutes', 0)
            starter = "Started" if game.get('starter') else "Bench"
            
            print(f"{date} vs {opponent}: {points}PTS, {rebounds}REB, {assists}AST, {minutes}MIN ({starter})")
    
    def statistical_analysis(self):
        """Display statistical analysis."""
        if not self.game_stats:
            print("❌ No game data available")
            return
        
        print(f"\n📊 {self.player_name.upper()} - STATISTICAL ANALYSIS")
        print("="*50)
        
        # Calculate averages
        total_games = len(self.game_stats)
        total_points = sum(g.get('points', 0) for g in self.game_stats)
        total_rebounds = sum(g.get('rebounds', {}).get('total', 0) for g in self.game_stats)
        total_assists = sum(g.get('assists', 0) for g in self.game_stats)
        total_minutes = sum(g.get('minutes', 0) for g in self.game_stats)
        
        avg_points = round(total_points / total_games, 1)
        avg_rebounds = round(total_rebounds / total_games, 1)
        avg_assists = round(total_assists / total_games, 1)
        avg_minutes = round(total_minutes / total_games, 1)
        
        print(f"\n📈 AVERAGES:")
        print(f"   Points: {avg_points}")
        print(f"   Rebounds: {avg_rebounds}")
        print(f"   Assists: {avg_assists}")
        print(f"   Minutes: {avg_minutes}")
        
        # Find highs and lows
        points_list = [g.get('points', 0) for g in self.game_stats]
        rebounds_list = [g.get('rebounds', {}).get('total', 0) for g in self.game_stats]
        
        max_points = max(points_list)
        min_points = min(points_list)
        max_rebounds = max(rebounds_list)
        min_rebounds = min(rebounds_list)
        
        print(f"\n📊 RANGES:")
        print(f"   Points: {min_points} - {max_points}")
        print(f"   Rebounds: {min_rebounds} - {max_rebounds}")
        
        # Consistency analysis
        high_point_games = len([p for p in points_list if p >= avg_points + 2])
        low_point_games = len([p for p in points_list if p <= avg_points - 2])
        
        print(f"\n🎯 CONSISTENCY:")
        print(f"   High scoring games (≥{avg_points + 2} pts): {high_point_games}")
        print(f"   Low scoring games (≤{avg_points - 2} pts): {low_point_games}")
        print(f"   Consistent games: {total_games - high_point_games - low_point_games}")
    
    def best_performances(self):
        """Display best performances."""
        if not self.game_stats:
            print("❌ No game data available")
            return
        
        print(f"\n🏆 {self.player_name.upper()} - BEST PERFORMANCES")
        print("="*50)
        
        # Sort by different criteria
        by_points = sorted(self.game_stats, key=lambda x: x.get('points', 0), reverse=True)
        by_rebounds = sorted(self.game_stats, key=lambda x: x.get('rebounds', {}).get('total', 0), reverse=True)
        by_assists = sorted(self.game_stats, key=lambda x: x.get('assists', 0), reverse=True)
        
        print(f"\n🔥 TOP 5 SCORING GAMES:")
        for i, game in enumerate(by_points[:5], 1):
            date = game.get('startDate', '')[:10]
            opponent = game.get('opponent', 'N/A')
            points = game.get('points', 0)
            print(f"   {i}. {date} vs {opponent}: {points} points")
        
        print(f"\n🏀 TOP 5 REBOUNDING GAMES:")
        for i, game in enumerate(by_rebounds[:5], 1):
            date = game.get('startDate', '')[:10]
            opponent = game.get('opponent', 'N/A')
            rebounds = game.get('rebounds', {}).get('total', 0)
            print(f"   {i}. {date} vs {opponent}: {rebounds} rebounds")
        
        print(f"\n🎯 TOP 5 ASSIST GAMES:")
        for i, game in enumerate(by_assists[:5], 1):
            date = game.get('startDate', '')[:10]
            opponent = game.get('opponent', 'N/A')
            assists = game.get('assists', 0)
            print(f"   {i}. {date} vs {opponent}: {assists} assists")
    
    def game_calendar(self):
        """Display game calendar view."""
        if not self.game_stats:
            print("❌ No game data available")
            return
        
        print(f"\n📅 {self.player_name.upper()} - GAME CALENDAR")
        print("="*50)
        
        # Group by month
        months = {}
        for game in self.game_stats:
            date_str = game.get('startDate', '')
            if date_str:
                month = date_str[:7]  # YYYY-MM
                if month not in months:
                    months[month] = []
                months[month].append(game)
        
        for month in sorted(months.keys()):
            games = months[month]
            print(f"\n📆 {month}:")
            for game in sorted(games, key=lambda x: x.get('startDate', '')):
                date = game.get('startDate', '')[:10]
                opponent = game.get('opponent', 'N/A')
                points = game.get('points', 0)
                rebounds = game.get('rebounds', {}).get('total', 0)
                home_away = "vs" if game.get('isHome') else "@"
                print(f"   {date} {home_away} {opponent}: {points}PTS, {rebounds}REB")
    
    def export_data(self):
        """Export data to files."""
        if not self.game_stats:
            print("❌ No game data available")
            return
        
        print(f"\n💾 EXPORT DATA")
        print("="*20)
        print("Export options:")
        print("1. JSON format")
        print("2. CSV format")
        print("3. Summary report")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            filename = f"jaxon_kohler_{self.season}_data.json"
            data = {
                'player': self.player_name,
                'team': self.team,
                'season': self.season,
                'season_stats': self.season_stats,
                'game_stats': self.game_stats
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Data exported to {filename}")
        
        elif choice == "2":
            filename = f"jaxon_kohler_{self.season}_games.csv"
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Opponent', 'Points', 'Rebounds', 'Assists', 'Minutes', 'Starter'])
                for game in sorted(self.game_stats, key=lambda x: x.get('startDate', '')):
                    writer.writerow([
                        game.get('startDate', '')[:10],
                        game.get('opponent', ''),
                        game.get('points', 0),
                        game.get('rebounds', {}).get('total', 0),
                        game.get('assists', 0),
                        game.get('minutes', 0),
                        'Yes' if game.get('starter') else 'No'
                    ])
            print(f"✅ Data exported to {filename}")
        
        elif choice == "3":
            filename = f"jaxon_kohler_{self.season}_summary.txt"
            with open(filename, 'w') as f:
                f.write(f"{self.player_name.upper()} - MICHIGAN STATE {self.season} SEASON SUMMARY\n")
                f.write("="*60 + "\n\n")
                
                if self.season_stats:
                    f.write("SEASON STATS:\n")
                    f.write(f"Games: {self.season_stats.get('games', 0)}\n")
                    f.write(f"Points: {self.season_stats.get('points', 0)}\n")
                    f.write(f"Rebounds: {self.season_stats.get('rebounds', {}).get('total', 0)}\n")
                    f.write(f"Assists: {self.season_stats.get('assists', 0)}\n\n")
                
                f.write("GAME-BY-GAME:\n")
                for game in sorted(self.game_stats, key=lambda x: x.get('startDate', '')):
                    date = game.get('startDate', '')[:10]
                    opponent = game.get('opponent', 'N/A')
                    points = game.get('points', 0)
                    rebounds = game.get('rebounds', {}).get('total', 0)
                    f.write(f"{date} vs {opponent}: {points}PTS, {rebounds}REB\n")
            
            print(f"✅ Summary exported to {filename}")
    
    def help(self):
        """Display help information."""
        print(f"\n❓ HELP - {self.player_name.upper()} DATA EXPLORER")
        print("="*50)
        print("\nThis tool helps you navigate and explore Jaxon Kohler's")
        print("basketball statistics from the 2024 season.")
        print("\n📊 Available Data:")
        print("• Season aggregate statistics")
        print("• Per-game statistics for all 30 games")
        print("• Game context (opponent, date, home/away)")
        print("• Advanced metrics and analysis")
        print("\n🔍 Navigation Tips:")
        print("• Use numbers to select menu options")
        print("• Search games by opponent, stats, or date")
        print("• Export data in multiple formats")
        print("• View best performances and trends")
    
    def run(self):
        """Main application loop."""
        while True:
            self.display_main_menu()
            choice = input("Enter your choice (0-8): ").strip()
            
            if choice == "0":
                print("\n👋 Thanks for exploring Jaxon Kohler's data!")
                break
            elif choice == "1":
                self.season_overview()
            elif choice == "2":
                self.game_by_game_stats()
            elif choice == "3":
                self.search_games()
            elif choice == "4":
                self.statistical_analysis()
            elif choice == "5":
                self.best_performances()
            elif choice == "6":
                self.game_calendar()
            elif choice == "7":
                self.export_data()
            elif choice == "8":
                self.help()
            else:
                print("❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        explorer = PlayerDataExplorer()
        explorer.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure your API key is set up correctly.")
