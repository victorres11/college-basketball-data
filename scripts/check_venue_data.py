#!/usr/bin/env python3
"""
Check what venue/location data is available from CBB API for games
"""
import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from cbb_api_wrapper import CollegeBasketballAPI

# Load API key
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'api_config.txt')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        for line in f:
            if line.startswith('CBB_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                os.environ['CBB_API_KEY'] = api_key
                break

api = CollegeBasketballAPI()

print("=" * 100)
print("VENUE DATA AVAILABILITY IN CBB API")
print("=" * 100)
print()

# Check venues endpoint
print("Method 1: Checking /venues endpoint...")
print("-" * 100)
try:
    venues = api._make_request("venues")
    if venues and isinstance(venues, list):
        print(f"Found {len(venues)} venues in the database")
        print()
        print("Sample venues (first 5):")
        for i, venue in enumerate(venues[:5]):
            print(f"\nVenue {i+1}:")
            print(json.dumps(venue, indent=2))
        
        # Look for Oregon or UCLA related venues
        print()
        print("Searching for Oregon/UCLA related venues...")
        oregon_ucla_venues = []
        for venue in venues:
            name = str(venue.get('name', '')).lower()
            city = str(venue.get('city', '')).lower()
            if 'oregon' in name or 'ucla' in name or 'pauley' in name or 'matthew' in name or 'knight' in name:
                oregon_ucla_venues.append(venue)
        
        if oregon_ucla_venues:
            print(f"Found {len(oregon_ucla_venues)} potentially relevant venues:")
            for venue in oregon_ucla_venues:
                print(json.dumps(venue, indent=2))
        else:
            print("No obvious Oregon/UCLA venues found")
    else:
        print("Venues endpoint returned unexpected format")
except Exception as e:
    print(f"Error accessing venues endpoint: {e}")

print()
print("=" * 100)
print("Method 2: Looking for upcoming Oregon vs UCLA game (2025-2026 season)...")
print("-" * 100)

# Search for upcoming Oregon vs UCLA game
try:
    # Check December 2025 and January 2026
    found_game = None
    for year, month in [(2025, 12), (2026, 1), (2026, 2)]:
        games = api.get_games(year, month)
        print(f"Checking {year}-{month:02d}: Found {len(games)} games")
        
        for game in games:
            home = str(game.get('homeTeam', '')).lower()
            away = str(game.get('awayTeam', '')).lower()
            
            # Check for Oregon vs UCLA
            if (('oregon' in home or 'oregon' in away) and 
                ('ucla' in home or 'ucla' in away)):
                # Check if it's a future game (not from 1950s)
                start_date = game.get('startDate', '')
                if '2025' in start_date or '2026' in start_date:
                    found_game = game
                    break
        
        if found_game:
            break
    
    if found_game:
        print()
        print("Found upcoming Oregon vs UCLA game:")
        print(json.dumps(found_game, indent=2))
        print()
        print("Venue-related fields:")
        print(f"  venueId: {found_game.get('venueId')}")
        print(f"  venue: {found_game.get('venue')}")
        print(f"  city: {found_game.get('city')}")
        print(f"  state: {found_game.get('state')}")
        print(f"  neutralSite: {found_game.get('neutralSite')}")
        print(f"  attendance: {found_game.get('attendance')}")
        print(f"  gameNotes: {found_game.get('gameNotes')}")
        print(f"  startDate: {found_game.get('startDate')}")
        print(f"  homeTeam: {found_game.get('homeTeam')}")
        print(f"  awayTeam: {found_game.get('awayTeam')}")
        
        # If venueId exists, try to look it up
        venue_id = found_game.get('venueId')
        if venue_id:
            print()
            print(f"Looking up venue details for venueId {venue_id}...")
            try:
                venue_details = api._make_request("venues", {"id": venue_id})
                if venue_details:
                    print("Venue details:")
                    print(json.dumps(venue_details, indent=2))
            except Exception as e:
                print(f"Could not fetch venue details: {e}")
    else:
        print("No upcoming Oregon vs UCLA game found in Dec 2025, Jan 2026, or Feb 2026")
        print("Checking for any recent games with venue data...")
        
        # Check recent games for any with venue data
        recent_games = api.get_games(2025, 11)
        games_with_venue = []
        for game in recent_games[:100]:
            if game.get('venueId') or game.get('venue') or game.get('city'):
                games_with_venue.append(game)
                if len(games_with_venue) >= 3:
                    break
        
        if games_with_venue:
            print(f"Found {len(games_with_venue)} recent games with venue data:")
            for game in games_with_venue:
                print()
                print(f"Game: {game.get('homeTeam')} vs {game.get('awayTeam')}")
                print(f"  venueId: {game.get('venueId')}")
                print(f"  venue: {game.get('venue')}")
                print(f"  city: {game.get('city')}")
                print(f"  state: {game.get('state')}")
                print(f"  startDate: {game.get('startDate')}")
        else:
            print("No recent games found with venue data populated")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 100)
print("SUMMARY: Available Venue Data in CBB API")
print("=" * 100)
print()
print("1. /games endpoint provides these venue-related fields:")
print("   - venueId: Integer ID linking to venues table (often null)")
print("   - venue: String name of venue (often null)")
print("   - city: String city name (often null)")
print("   - state: String state name (often null)")
print("   - neutralSite: Boolean (always populated)")
print("   - attendance: Integer (often null)")
print("   - gameNotes: String (often null)")
print()
print("2. /venues endpoint provides venue details:")
print("   - id: Integer venue ID")
print("   - sourceId: String source identifier")
print("   - name: String venue name")
print("   - city: String city name")
print("   - state: String state name (may be null)")
print("   - country: String country name")
print()
print("3. To get complete venue info for a game:")
print("   - Check game.venueId")
print("   - If venueId exists, query /venues?id={venueId}")
print("   - Fallback to game.venue, game.city, game.state if venueId is null")
print()
