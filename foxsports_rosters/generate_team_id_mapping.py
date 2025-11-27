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
        
        # Try exact match first
        fox_id = None
        best_match = None
        best_similarity = 0
        
        # Normalize names for better matching (remove common suffixes)
        def normalize_for_matching(name):
            # Remove common mascot suffixes
            suffixes = [' ducks', ' bears', ' tigers', ' wildcats', ' eagles', ' bulldogs', 
                       ' lions', ' panthers', ' cougars', ' hornets', ' warriors', ' knights',
                       ' spartans', ' wolverines', ' buckeyes', ' badgers', ' hoosiers',
                       ' boilermakers', ' nittany lions', ' fighting illini', ' golden gophers',
                       ' cornhuskers', ' scarlet knights', ' bruins', ' trojans', ' huskies']
            name_lower = name.lower()
            for suffix in suffixes:
                if name_lower.endswith(suffix):
                    name_lower = name_lower[:-len(suffix)].strip()
                    break
            return name_lower
        
        cbb_normalized = normalize_for_matching(cbb_name)
        
        for fox_id_str, fox_name in foxsports_teams.items():
            # Exact match
            if cbb_name.lower() == fox_name.lower():
                fox_id = fox_id_str
                break
            
            # Normalized match (without mascot)
            fox_normalized = normalize_for_matching(fox_name)
            if cbb_normalized == fox_normalized:
                fox_id = fox_id_str
                break
            
            # Similarity match (lower threshold for better matching)
            sim = similarity(cbb_name, fox_name)
            if sim > best_similarity and sim > 0.7:  # Lowered to 70% similarity threshold
                best_similarity = sim
                best_match = fox_id_str
        
        if not fox_id and best_match:
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

