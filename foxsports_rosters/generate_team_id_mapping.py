#!/usr/bin/env python3
"""
Generate CBB API → FoxSports team ID mapping.
Compares all teams from both systems and creates mapping file.
"""
import sys
import os
import json
from difflib import SequenceMatcher

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from cbb_api_wrapper import CollegeBasketballAPI

def similarity(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def normalize_team_name(name):
    """Normalize team name for matching."""
    # Remove common suffixes/prefixes
    name = name.replace("University", "").replace("College", "").strip()
    # Remove extra spaces
    return " ".join(name.split())

def extract_school_name(full_name):
    """
    Extract just the school name from a full team name (e.g., "UTSA Roadrunners" -> "UTSA").
    Removes mascot suffixes.
    """
    # Common mascots to remove
    mascots = [
        'Roadrunners', 'Wildcats', 'Tigers', 'Bears', 'Eagles', 'Bulldogs', 'Lions',
        'Panthers', 'Cougars', 'Hornets', 'Warriors', 'Knights', 'Spartans', 'Wolverines',
        'Buckeyes', 'Badgers', 'Hoosiers', 'Boilermakers', 'Nittany Lions', 'Fighting Illini',
        'Golden Gophers', 'Cornhuskers', 'Scarlet Knights', 'Bruins', 'Trojans', 'Huskies',
        'Ducks', 'Beavers', 'Cardinals', 'Jayhawks', 'Cyclones', 'Red Raiders', 'Longhorns',
        'Aggies', 'Mustangs', 'Horned Frogs', 'Mountaineers', 'Volunteers', 'Crimson Tide',
        'Razorbacks', 'Gators', 'Gamecocks', 'Commodores', 'Rebels', 'Golden Eagles',
        'Blue Devils', 'Tar Heels', 'Wolfpack', 'Seminoles', 'Yellow Jackets', 'Cavaliers',
        'Hokies', 'Demon Deacons', 'Orange', 'Sun Devils', 'Buffaloes', 'Bearcats',
        'Musketeers', 'Golden Griffins', 'Stags', 'Gaels', 'Jaspers', 'Red Foxes',
        'Mountaineers', 'Purple Eagles', 'Bobcats', 'Broncs', 'Pioneers', 'Peacocks',
        'Saints', 'Zips', 'Falcons', 'Bulls', 'Chippewas', 'Golden Flashes', 'RedHawks',
        'Rockets', 'Broncos', 'Minutemen', 'Seahawks', 'Anteaters', 'Gauchos', 'Tritons',
        'Highlanders', 'Beach', 'Titans', 'Matadors', 'Rainbow Warriors', 'Catamounts',
        'Big Green', 'Big Red', 'Crimson', 'Quakers', 'Billikens', 'Bonnies', 'Rams',
        'Spiders', 'Hawks', 'Flyers', 'Dukes', 'Patriots', 'Revolutionaries', 'Explorers',
        'Ramblers', 'Colonials', 'Retrievers', 'River Hawks', 'Great Danes', 'Seawolves',
        'Pride', 'Phoenix', 'Pirates', 'Tribe', 'Dragons', 'Blue Hose', 'Lancers',
        'Highlanders', 'Red Flash', 'Dolphins', 'Royals', 'Hatters', 'Wolves', 'Owls',
        'Mean Green', 'Green Wave', 'Golden Hurricane', 'Blazers', 'Shockers', 'Bearcats',
        'Buccaneers', 'Paladins', 'Mocs', 'Terriers', 'Keydets', 'Fighting Hawks',
        'Bison', 'Mavericks', 'Coyotes', 'Jackrabbits', 'Tommies', 'Red Wolves',
        'Chanticleers', 'Jaguars', 'Ragin Cajuns', 'Warhawks', 'Thundering Herd',
        'Monarchs', 'Texans', 'Trailblazers', 'Pilots', 'Toreros', 'Dons', 'Redhawks',
        'Flames', 'Hilltoppers', 'Gamecocks', 'Blue Raiders', 'Colonels', 'Privateers',
        'Lumberjacks', 'Demons', 'Lions', 'Islanders', 'Vaqueros', 'Governors', 'Sycamores',
        'Racers', 'Salukis', 'Beacons', 'Braves', 'Falcons', 'Wolf Pack', 'Lobos',
        'Aztecs', 'Runnin Rebels', 'Cowboys', 'Blue Devils', 'Sharks', 'Skyhawks',
        'Lakers', 'Chargers', 'Black Knights', 'Terriers', 'Raiders', 'Crusaders',
        'Leopards', 'Mountain Hawks', 'Greyhounds', 'Midshipmen', 'Norse', 'Golden Grizzlies',
        'Mastodons', 'Penguins', 'Vikings', 'Titans', 'Flames', 'Jaguars', 'Grizzlies',
        'Bobcats', 'Vandals', 'Bengals', 'Lopes', 'Hornets', 'Aggies', 'Leathernecks',
        'Redhawks', 'Golden Eagles', 'Screaming Eagles', 'Trojans', 'Rattlers', 'Delta Devils',
        'Golden Lions', 'Jaguars', 'Braves', 'Fighting Camels', 'Blue Hens'
    ]

    name = full_name.strip()
    for mascot in sorted(mascots, key=len, reverse=True):  # Try longest first
        if name.lower().endswith(' ' + mascot.lower()):
            name = name[:-(len(mascot)+1)].strip()
            break
    return name

def main():
    # Load API key
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'api_config.txt')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('CBB_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    os.environ['CBB_API_KEY'] = api_key
                    break
    
    # Load FoxSports teams
    foxsports_path = os.path.dirname(__file__)
    foxsports_mapping_path = os.path.join(foxsports_path, 'team_ids_mapping.json')
    with open(foxsports_mapping_path, 'r') as f:
        foxsports_teams = json.load(f)
    
    # Fetch CBB API teams
    print("Fetching teams from CBB API...")
    api = CollegeBasketballAPI()
    cbb_teams = api.get_teams()
    
    print(f"Found {len(cbb_teams)} CBB teams")
    print(f"Found {len(foxsports_teams)} FoxSports teams\n")
    
    # Create mapping
    mapping = {}
    mismatches = {}
    missing_in_foxsports = []
    missing_in_cbb = []
    matched = []
    
    # Build FoxSports lookup by school name (without mascot)
    fox_by_school_name = {}  # school_name (lowercase) -> fox_id
    for fox_id_str, fox_full_name in foxsports_teams.items():
        school_name = extract_school_name(fox_full_name).lower()
        fox_by_school_name[school_name] = fox_id_str
        # Also add full name
        fox_by_school_name[fox_full_name.lower()] = fox_id_str

    # Match CBB teams to FoxSports teams
    for cbb_team in cbb_teams:
        cbb_id = str(cbb_team.get('id'))
        cbb_name = cbb_team.get('school') or cbb_team.get('name') or ''

        if not cbb_id or not cbb_name:
            continue

        # First check: if IDs match, use that (simplest case)
        if cbb_id in foxsports_teams:
            mapping[cbb_id] = cbb_id
            matched.append((cbb_id, cbb_name, cbb_id, foxsports_teams[cbb_id]))
            continue

        fox_id = None

        # Try exact match on school name (CBB name -> FoxSports school name)
        cbb_name_lower = cbb_name.lower()
        if cbb_name_lower in fox_by_school_name:
            fox_id = fox_by_school_name[cbb_name_lower]

        # Try matching CBB school name to FoxSports school name
        if not fox_id:
            cbb_school = extract_school_name(cbb_name).lower()
            if cbb_school in fox_by_school_name:
                fox_id = fox_by_school_name[cbb_school]

        # Try high-confidence similarity matching (0.95+ threshold to avoid false positives)
        if not fox_id:
            best_match = None
            best_similarity = 0
            for fox_id_str, fox_name in foxsports_teams.items():
                fox_school = extract_school_name(fox_name)
                cbb_school = extract_school_name(cbb_name)

                # Compare school names without mascots
                sim = similarity(cbb_school, fox_school)
                if sim > best_similarity and sim >= 0.95:  # High threshold to avoid false positives
                    best_similarity = sim
                    best_match = fox_id_str

            if best_match:
                fox_id = best_match

        if fox_id:
            # Check if IDs match
            if cbb_id == fox_id:
                mapping[cbb_id] = fox_id
                matched.append((cbb_id, cbb_name, fox_id, foxsports_teams[fox_id]))
            else:
                mismatches[cbb_id] = fox_id
                print(f"⚠️  ID MISMATCH: CBB {cbb_id} ({cbb_name}) → FoxSports {fox_id} ({foxsports_teams[fox_id]})")
        else:
            missing_in_foxsports.append({'id': cbb_id, 'name': cbb_name})
            # Only print for D1 teams (likely to be important)
            if len(cbb_name) > 2:  # Skip very short names
                print(f"❌ NOT FOUND IN FOXSPORTS: CBB {cbb_id} ({cbb_name})")
    
    # Find FoxSports teams not in CBB
    cbb_ids = {str(t.get('id')) for t in cbb_teams if t.get('id')}
    for fox_id, fox_name in foxsports_teams.items():
        if fox_id not in mapping.values() and fox_id not in mismatches.values():
            missing_in_cbb.append({'id': fox_id, 'name': fox_name})
    
    # Create final mapping structure
    result = {
        **mapping,  # Direct matches
        'MISMATCHES': mismatches,
        'MISSING_IN_FOXSPORTS': missing_in_foxsports,
        'MISSING_IN_CBB': missing_in_cbb,
        '_stats': {
            'total_cbb_teams': len(cbb_teams),
            'total_foxsports_teams': len(foxsports_teams),
            'matched': len(matched),
            'mismatches': len(mismatches),
            'missing_in_foxsports': len(missing_in_foxsports),
            'missing_in_cbb': len(missing_in_cbb)
        }
    }
    
    # Save mapping
    output_path = os.path.join(foxsports_path, 'cbb_to_foxsports_team_mapping.json')
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ Mapping generated: {output_path}")
    print(f"{'='*80}")
    print(f"📊 Stats:")
    print(f"   Total CBB teams: {result['_stats']['total_cbb_teams']}")
    print(f"   Total FoxSports teams: {result['_stats']['total_foxsports_teams']}")
    print(f"   ✅ Matched (same ID): {result['_stats']['matched']}")
    if mismatches:
        print(f"   ⚠️  Mismatches (different IDs): {result['_stats']['mismatches']}")
    if missing_in_foxsports:
        print(f"   ❌ Missing in FoxSports: {result['_stats']['missing_in_foxsports']}")
    if missing_in_cbb:
        print(f"   ❌ Missing in CBB: {result['_stats']['missing_in_cbb']}")

if __name__ == '__main__':
    main()

