#!/usr/bin/env python3
"""
Check if venues endpoint has capacity field
"""
import sys
import os
import json
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
print("CHECKING FOR VENUE CAPACITY FIELD")
print("=" * 100)
print()

# Check venues endpoint for capacity field
print("Method 1: Checking /venues endpoint structure...")
print("-" * 100)
try:
    venues = api._make_request("venues")
    if venues and isinstance(venues, list):
        print(f"Found {len(venues)} venues")
        print()
        
        # Check first several venues for all fields
        print("Checking first 10 venues for all available fields:")
        print()
        for i, venue in enumerate(venues[:10]):
            print(f"Venue {i+1}: {venue.get('name', 'N/A')}")
            print(f"  All fields: {list(venue.keys())}")
            print(f"  Full structure:")
            print(json.dumps(venue, indent=4))
            print()
        
        # Specifically look for capacity-related fields
        print("=" * 100)
        print("Searching for capacity-related fields in all venues...")
        print("-" * 100)
        
        capacity_fields = set()
        for venue in venues:
            for key in venue.keys():
                if 'capacity' in key.lower() or 'seats' in key.lower() or 'size' in key.lower():
                    capacity_fields.add(key)
        
        if capacity_fields:
            print(f"Found capacity-related fields: {capacity_fields}")
            print()
            print("Sample venues with capacity data:")
            count = 0
            for venue in venues:
                has_capacity = any('capacity' in k.lower() or 'seats' in k.lower() or 'size' in k.lower() 
                                 for k in venue.keys())
                if has_capacity and count < 5:
                    print(json.dumps(venue, indent=2))
                    print()
                    count += 1
        else:
            print("No capacity-related fields found in venue objects")
            print()
            print("All available fields in venue objects:")
            if venues:
                all_fields = set()
                for venue in venues:
                    all_fields.update(venue.keys())
                print(f"  {sorted(all_fields)}")
    else:
        print("Venues endpoint returned unexpected format")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 100)
print("Method 2: Check specific well-known venues (Pauley Pavilion, Matthew Knight Arena)...")
print("-" * 100)

try:
    venues = api._make_request("venues")
    if venues and isinstance(venues, list):
        # Look for Pauley Pavilion and Matthew Knight Arena
        target_venues = []
        for venue in venues:
            name = str(venue.get('name', '')).lower()
            if 'pauley' in name or 'matthew knight' in name or 'matthew k' in name:
                target_venues.append(venue)
        
        if target_venues:
            print(f"Found {len(target_venues)} target venues:")
            for venue in target_venues:
                print()
                print(f"Venue: {venue.get('name')}")
                print(f"All fields and values:")
                print(json.dumps(venue, indent=2))
        else:
            print("Target venues not found")
except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()
print("Venue fields available:")
print("  - id: Integer venue ID")
print("  - sourceId: String source identifier")
print("  - name: String venue name")
print("  - city: String city name")
print("  - state: String state name (may be null)")
print("  - country: String country name")
print()
print("Game fields available:")
print("  - attendance: Integer (actual attendance for that game, often null)")
print("  - venueId: Integer (links to venue, often null)")
print("  - venue: String (venue name, often null)")
print("  - city: String (city, often null)")
print("  - state: String (state, often null)")
print()

