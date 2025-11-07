#!/usr/bin/env python3
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
Check UCLA roster from API vs generated JSON
"""

from cbb_api_wrapper import CollegeBasketballAPI
import json

def main():
    api = CollegeBasketballAPI()
    
    print("Fetching UCLA roster from API (2026 season)...")
    print("=" * 70)
    
    roster_data = api.get_team_roster(2026, "ucla")
    
    if roster_data and len(roster_data) > 0:
        if 'players' in roster_data[0]:
            players = roster_data[0]['players']
            print(f"\nTotal players in API roster: {len(players)}\n")
            
            print("All players in API roster:")
            print("-" * 70)
            for i, player in enumerate(players, 1):
                name = player.get('name', 'N/A')
                jersey = player.get('jersey', 'N/A')
                position = player.get('position', 'N/A')
                height = player.get('height', 'N/A')
                start_season = player.get('startSeason', 'N/A')
                end_season = player.get('endSeason', 'N/A')
                
                # Format height
                height_str = "N/A"
                if isinstance(height, int):
                    feet = height // 12
                    inches = height % 12
                    height_str = f"{feet}-{inches}"
                
                print(f"{i:2}. {name:30} | #{jersey:3} | {position:10} | {height_str:6} | {start_season}-{end_season}")
        else:
            print("No 'players' key found in roster data")
            print("Full roster data structure:")
            print(json.dumps(roster_data, indent=2))
    else:
        print("No roster data returned from API")
    
    print("\n" + "=" * 70)
    print("\nChecking generated JSON file...")
    
    try:
        with open('data/2026/ucla_scouting_data_2026.json', 'r') as f:
            json_data = json.load(f)
        
        json_players = json_data.get('players', [])
        json_player_names = {p.get('name') for p in json_players}
        
        print(f"\nTotal players in generated JSON: {len(json_players)}")
        print("\nPlayers in generated JSON:")
        print("-" * 70)
        for i, player in enumerate(json_players, 1):
            name = player.get('name', 'N/A')
            jersey = player.get('jerseyNumber', 'N/A')
            games = player.get('seasonTotals', {}).get('games', 0)
            print(f"{i:2}. {name:30} | #{jersey:3} | Games: {games}")
        
        # Compare
        if roster_data and len(roster_data) > 0 and 'players' in roster_data[0]:
            api_players = roster_data[0]['players']
            api_player_names = {p.get('name') for p in api_players}
            
            missing_in_json = api_player_names - json_player_names
            extra_in_json = json_player_names - api_player_names
            
            print("\n" + "=" * 70)
            print("\nCOMPARISON:")
            print(f"API roster: {len(api_players)} players")
            print(f"JSON file: {len(json_players)} players")
            
            if missing_in_json:
                print(f"\n⚠️  Players in API roster but NOT in JSON ({len(missing_in_json)}):")
                for name in sorted(missing_in_json):
                    # Find player details
                    player = next((p for p in api_players if p.get('name') == name), None)
                    if player:
                        jersey = player.get('jersey', 'N/A')
                        position = player.get('position', 'N/A')
                        print(f"  - {name} | #{jersey} | {position}")
            
            if extra_in_json:
                print(f"\n⚠️  Players in JSON but NOT in API roster ({len(extra_in_json)}):")
                for name in sorted(extra_in_json):
                    print(f"  - {name}")
            
            if not missing_in_json and not extra_in_json:
                print("\n✅ All roster players are included in JSON")
            elif missing_in_json:
                print(f"\n❌ Missing {len(missing_in_json)} players from roster in JSON file")
                
    except FileNotFoundError:
        print("Generated JSON file not found")
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

