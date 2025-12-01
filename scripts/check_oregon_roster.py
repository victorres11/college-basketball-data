#!/usr/bin/env python3
"""
Check Oregon roster from API to see startSeason/endSeason values
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cbb_api_wrapper import CollegeBasketballAPI
import json

def main():
    # Load API key
    config_path = 'config/api_config.txt'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('CBB_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    os.environ['CBB_API_KEY'] = api_key
                    break
    
    api = CollegeBasketballAPI()
    
    print("Fetching Oregon roster from API (2026 season)...")
    print("=" * 80)
    
    roster_data = api.get_team_roster(2026, "oregon")
    
    if roster_data and len(roster_data) > 0:
        if 'players' in roster_data[0]:
            players = roster_data[0]['players']
            print(f"\nTotal players in API roster: {len(players)}\n")
            
            # Show first player's full structure
            if len(players) > 0:
                print("First player's full API response structure:")
                print("-" * 80)
                print(json.dumps(players[0], indent=2))
                print("\n" + "-" * 80)
            
            print(f"\nAll players with startSeason/endSeason:")
            print("-" * 80)
            print(f"{'Name':<30} | {'Jersey':<8} | {'startSeason':<12} | {'endSeason':<12} | {'Years':<6} | {'Calculated Class'}")
            print("-" * 80)
            
            for player in players:
                name = player.get('name', 'N/A')
                jersey = player.get('jersey', 'N/A')
                start_season = player.get('startSeason', 'N/A')
                end_season = player.get('endSeason', 'N/A')
                
                years = 'N/A'
                calculated_class = 'N/A'
                if isinstance(start_season, int) and isinstance(end_season, int):
                    years = end_season - start_season + 1
                    if years == 1:
                        calculated_class = "FR"
                    elif years == 2:
                        calculated_class = "SO"
                    elif years == 3:
                        calculated_class = "JR"
                    else:
                        calculated_class = "SR"
                
                print(f"{name:<30} | {str(jersey):<8} | {str(start_season):<12} | {str(end_season):<12} | {str(years):<6} | {calculated_class}")
            
            # Check if any player has a 'year' or 'class' field directly from API
            print("\n" + "-" * 80)
            print("Checking for year/class fields in API response...")
            has_year = False
            has_class = False
            for player in players:
                if 'year' in player:
                    has_year = True
                    print(f"Found player with year field: {player.get('name')} = {player.get('year')}")
                if 'class' in player:
                    has_class = True
                    print(f"Found player with class field: {player.get('name')} = {player.get('class')}")
            
            if not has_year and not has_class:
                print("❌ No 'year' or 'class' fields found in API response")
                print("   API only provides startSeason/endSeason, requiring calculation")
            else:
                print("✅ API provides year/class field directly")
        else:
            print("No 'players' key found in roster data")
            print("Full roster data structure:")
            print(json.dumps(roster_data, indent=2))
    else:
        print("No roster data returned from API")

if __name__ == '__main__':
    main()

