#!/usr/bin/env python3
"""
Generate centralized team registry from existing mapping files.

This script merges:
- team_ids_mapping.json (CBB API IDs → team names with mascots)
- bballnet_team_mapping.json (team names → bballnet slugs)
- sports_ref_team_mapping.json (team names → sports reference slugs)
- TEAM_WIKIPEDIA_MAPPING (team names → wikipedia page titles)

Output: config/team_registry.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Input files
TEAM_IDS_FILE = PROJECT_ROOT / 'foxsports_rosters' / 'team_ids_mapping.json'
BBALLNET_MAPPING_FILE = PROJECT_ROOT / 'misc_data_sources' / 'quadrants' / 'mappings' / 'bballnet_team_mapping.json'
SPORTS_REF_MAPPING_FILE = PROJECT_ROOT / 'misc_data_sources' / 'coaching_history' / 'mappings' / 'sports_ref_team_mapping.json'

# Output file
OUTPUT_FILE = PROJECT_ROOT / 'config' / 'team_registry.json'

# Manual alias overrides - common abbreviations that can't be auto-generated
# Key: team_id, Value: list of additional aliases
MANUAL_ALIASES = {
    "28": ["nc state", "nc state wolfpack"],  # North Carolina State
    "333": ["usc", "usc trojans"],  # Southern California
    "342": ["ole miss", "ole miss rebels"],  # Mississippi
    "162": ["miami oh", "miami ohio", "miami redhawks"],  # Miami (OH)
    "55": ["miami fl", "miami florida"],  # Miami (FL)
    "296": ["wku", "wku hilltoppers"],  # Western Kentucky
    "339": ["lsu", "lsu tigers"],  # Louisiana State
    "223": ["cal", "cal bears", "california bears"],  # California
    "252": ["uconn", "uconn huskies"],  # Connecticut
    "151": ["smu", "smu mustangs"],  # Southern Methodist
    "271": ["utsa", "utsa roadrunners"],  # UTSA
    "87": ["utep", "utep miners"],  # UTEP
    "251": ["ucf", "ucf knights"],  # UCF
    "277": ["unlv", "unlv rebels", "unlv runnin rebels"],  # UNLV
    "96": ["uab", "uab blazers"],  # UAB
}


def load_team_ids() -> Dict[str, str]:
    """Load CBB API team IDs → team names with mascots"""
    if not TEAM_IDS_FILE.exists():
        print(f"Warning: {TEAM_IDS_FILE} not found")
        return {}

    with open(TEAM_IDS_FILE, 'r') as f:
        return json.load(f)


def load_bballnet_mapping() -> Dict[str, str]:
    """Load bballnet team name → slug mapping"""
    if not BBALLNET_MAPPING_FILE.exists():
        print(f"Warning: {BBALLNET_MAPPING_FILE} not found")
        return {}

    with open(BBALLNET_MAPPING_FILE, 'r') as f:
        data = json.load(f)
        return data.get('team_slug_mapping', {})


def load_sports_ref_mapping() -> Dict[str, str]:
    """Load sports reference team name → slug mapping"""
    if not SPORTS_REF_MAPPING_FILE.exists():
        print(f"Warning: {SPORTS_REF_MAPPING_FILE} not found")
        return {}

    with open(SPORTS_REF_MAPPING_FILE, 'r') as f:
        data = json.load(f)
        return data.get('team_slug_mapping', {})


def load_wikipedia_mapping() -> Dict[str, str]:
    """Load Wikipedia team name → page title mapping from Python file"""
    wiki_script = PROJECT_ROOT / 'misc_data_sources' / 'wikipedia' / 'scripts' / 'team_name_mapping.py'

    if not wiki_script.exists():
        print(f"Warning: {wiki_script} not found")
        return {}

    # Import the mapping from the Python file
    sys.path.insert(0, str(wiki_script.parent))
    try:
        from team_name_mapping import TEAM_WIKIPEDIA_MAPPING
        return TEAM_WIKIPEDIA_MAPPING
    except ImportError as e:
        print(f"Warning: Could not import TEAM_WIKIPEDIA_MAPPING: {e}")
        return {}


def extract_canonical_name(full_name: str) -> str:
    """
    Extract canonical team name from full name with mascot.

    Examples:
        "UCLA Bruins" → "UCLA"
        "Boston College Eagles" → "Boston College"
        "Miami (FL) Hurricanes" → "Miami"
        "St. John's Red Storm" → "St. John's"
    """
    # Common mascots to strip (order matters - longer/multi-word first)
    mascots = [
        # Multi-word mascots (must come first - longest first)
        "Fightin' Blue Hens", "Runnin' Bulldogs", "Runnin' Utes",
        "Golden Eagles", "Golden Lions", "Red Raiders", "Yellow Jackets", "Blue Devils",
        "Demon Deacons", "Golden Bears", "Sun Devils", "Red Storm",
        "Blue Demons", "Fighting Irish", "Crimson Tide", "Tar Heels",
        "Fighting Illini", "Nittany Lions", "Horned Frogs", "Wolf Pack",
        "Golden Flashes", "Golden Griffins", "Golden Grizzlies", "Golden Hurricane",
        "Golden Gophers", "Scarlet Knights", "Black Bears", "River Hawks",
        "Blue Hose", "Purple Eagles", "Black Knights", "Mountain Hawks",
        "Fighting Hawks", "Screaming Eagles", "Delta Devils",
        "Red Wolves", "Red Foxes", "Red Flash", "Blue Raiders", "Blue Hens",
        "Big Red", "Big Green", "Mean Green", "Green Wave", "Great Danes",
        "Fighting Camels", "Purple Aces", "Ragin' Cajuns", "Runnin' Rebels",
        "Rainbow Warriors", "Thundering Herd",
        # Single-word mascots (alphabetized for maintainability)
        "49ers", "Aces", "Aggies", "Anteaters", "Aztecs",
        "Badgers", "Beach", "Beacons", "Bearcats", "Bearkats", "Bears",
        "Beavers", "Bengals", "Billikens", "Bison", "Bisons", "Blazers",
        "Bluejays", "Bobcats", "Boilermakers", "Bonnies", "Braves", "Broncos",
        "Broncs", "Bruins", "Buccaneers", "Buckeyes", "Buffaloes", "Bulldogs", "Bulls",
        "Cajuns", "Camels", "Cardinal", "Cardinals", "Catamounts", "Cavaliers",
        "Chanticleers", "Chargers", "Chippewas", "Colonels", "Colonials",
        "Commodores", "Cornhuskers", "Cougars", "Cowboys", "Coyotes", "Crimson",
        "Crusaders", "Cyclones",
        "Danes", "Demons", "Devils", "Dolphins", "Dons", "Dragons", "Ducks", "Dukes",
        "Eagles", "Explorers",
        "Falcons", "Flames", "Flash", "Flashes", "Flyers", "Foxes", "Friars",
        "Gaels", "Gamecocks", "Gators", "Gauchos", "Gophers", "Governors",
        "Green", "Greyhounds", "Griffins", "Grizzlies",
        "Hatters", "Hawkeyes", "RedHawks", "Redhawks", "Hawks", "Hens", "Herd", "Highlanders",
        "Hilltoppers", "Hokies", "Hoosiers", "Hornets", "Hose", "Hoyas",
        "Hurricane", "Hurricanes", "Huskies", "Huskers",
        "Islanders",
        "Jackrabbits", "Jaguars", "Jaspers", "Jayhawks",
        "Keydets", "Knights",
        "Lakers", "Lancers", "Leathernecks", "Leopards", "Lions", "Lobos", "Lopes",
        "Longhorns", "Lumberjacks",
        "Mastodons", "Matadors", "Mavericks", "Midshipmen", "Miners", "Minutemen",
        "Mocs", "Monarchs", "Mountaineers", "Musketeers", "Mustangs",
        "Norse",
        "Orange", "Ospreys", "Owls",
        "Pack", "Paladins", "Panthers", "Patriots", "Peacocks", "Penguins",
        "Phoenix", "Pilots", "Pioneers", "Pirates", "Pride", "Privateers",
        "Quakers",
        "Racers", "Raiders", "Ramblers", "Rams", "Rattlers", "Razorbacks",
        "Rebels", "Redbirds", "Red", "Retrievers",
        "Revolutionaries", "Roadrunners", "Rockets", "Roos", "Royals",
        "Saints", "Salukis", "Seahawks", "Seawolves", "Seminoles", "Sharks",
        "Shockers", "Skyhawks", "Sooners", "Spartans", "Spiders", "Stags",
        "Sycamores",
        "Terrapins", "Terriers", "Texans", "Thunderbirds", "Tigers", "Titans",
        "Tommies", "Toppers", "Toreros", "Trailblazers", "Tribe", "Tritons",
        "Trojans",
        "Utes",
        "Vandals", "Vaqueros", "Vikings", "Volunteers",
        "Warhawks", "Warriors", "Wave", "Waves", "Wildcats", "Wolfpack",
        "Wolverines", "Wolves",
        "Zips"
    ]

    name = full_name.strip()

    # Remove (FL), (OH), (NY) etc. state indicators for matching
    state_match = re.search(r'\s*\([A-Z]{2}\)\s*', name)
    state_indicator = state_match.group(0) if state_match else ""
    name_without_state = re.sub(r'\s*\([A-Z]{2}\)\s*', ' ', name).strip()

    for mascot in mascots:
        if name_without_state.endswith(mascot):
            canonical = name_without_state[:-len(mascot)].strip()
            # Re-add state indicator if it was present
            if state_indicator:
                canonical = canonical + state_indicator.strip()
            return canonical

    # If no mascot found, return as-is (might be just team name)
    return name


def extract_mascot(full_name: str) -> Optional[str]:
    """Extract mascot from full team name"""
    canonical = extract_canonical_name(full_name)
    # Remove state indicators for comparison
    canonical_clean = re.sub(r'\s*\([A-Z]{2}\)\s*', '', canonical).strip()
    full_clean = re.sub(r'\s*\([A-Z]{2}\)\s*', '', full_name).strip()

    if full_clean != canonical_clean and len(full_clean) > len(canonical_clean):
        mascot = full_clean[len(canonical_clean):].strip()
        return mascot if mascot else None
    return None


def normalize_name(name: str) -> str:
    """Normalize team name for matching"""
    name = name.lower().strip()
    # Normalize common patterns
    name = re.sub(r'\s+', ' ', name)  # Multiple spaces to single
    name = name.replace('.', '')  # Remove periods
    name = name.replace("'", "'")  # Normalize apostrophes
    return name


def generate_name_variations(name: str) -> List[str]:
    """Generate common variations of a team name"""
    variations = [name]

    # Add lowercase version
    variations.append(name.lower())

    # State/St. variations
    if "State" in name:
        variations.append(name.replace("State", "St."))
        variations.append(name.replace("State", "St"))
    if " St." in name or name.endswith(" St."):
        variations.append(name.replace(" St.", " State"))
        variations.append(name.replace("St.", "St"))
    if " St " in name or name.endswith(" St"):
        variations.append(name.replace(" St", " State"))
        variations.append(name.replace(" St", " St."))

    # University variations
    if "University" in name:
        variations.append(name.replace("University", "U."))
        variations.append(name.replace("University", ""))

    # Kentucky/Ky variations (specific common case)
    if "Kentucky" in name:
        variations.append(name.replace("Kentucky", "Ky."))
        variations.append(name.replace("Kentucky", "Ky"))
    if " Ky." in name or name.endswith(" Ky."):
        variations.append(name.replace(" Ky.", " Kentucky"))
    if " Ky" in name and " Ky." not in name:
        variations.append(name.replace(" Ky", " Kentucky"))

    # Michigan/Mich variations
    if "Michigan" in name:
        variations.append(name.replace("Michigan", "Mich."))
    if "Mich." in name:
        variations.append(name.replace("Mich.", "Michigan"))

    # Carolina/Caro variations
    if "Carolina" in name:
        variations.append(name.replace("Carolina", "Caro."))
    if "Caro." in name:
        variations.append(name.replace("Caro.", "Carolina"))

    # Illinois/Ill variations
    if "Illinois" in name:
        variations.append(name.replace("Illinois", "Ill."))
    if "Ill." in name:
        variations.append(name.replace("Ill.", "Illinois"))

    # Connecticut variations
    if "Connecticut" in name:
        variations.append(name.replace("Connecticut", "Conn."))
    if "Conn." in name:
        variations.append(name.replace("Conn.", "Connecticut"))

    # Arkansas/Ark variations
    if "Arkansas" in name:
        variations.append(name.replace("Arkansas", "Ark."))
    if "Ark." in name:
        variations.append(name.replace("Ark.", "Arkansas"))

    # State indicator variations - space vs no space: "(FL)" vs " (FL)"
    import re
    state_match = re.search(r'\(([A-Z]{2})\)', name)
    if state_match:
        # Add version with space before parenthesis
        if not re.search(r'\s\([A-Z]{2}\)', name):
            # Name has no space, add version with space
            variations.append(re.sub(r'\(([A-Z]{2})\)', r' (\1)', name))
        else:
            # Name has space, add version without space
            variations.append(re.sub(r'\s\(([A-Z]{2})\)', r'(\1)', name))

    return variations


def find_slug_in_mapping(team_name: str, mapping: Dict[str, str]) -> Optional[str]:
    """Find a slug for a team name, trying various normalizations"""
    # Try direct match first
    if team_name in mapping:
        return mapping[team_name]

    # Generate variations of the team name
    variations = generate_name_variations(team_name)

    # Also try canonical name variations
    canonical = extract_canonical_name(team_name)
    if canonical != team_name:
        variations.extend(generate_name_variations(canonical))

    # Try each variation
    for variant in variations:
        if variant in mapping:
            return mapping[variant]
        # Also try normalized version
        normalized_variant = normalize_name(variant)
        for key, value in mapping.items():
            if normalize_name(key) == normalized_variant:
                return value

    # Try without state indicator
    without_state = re.sub(r'\s*\([A-Z]{2}\)\s*', '', team_name).strip()
    if without_state != team_name:
        variations = generate_name_variations(without_state)
        for variant in variations:
            if variant in mapping:
                return mapping[variant]
            for key, value in mapping.items():
                if normalize_name(key) == normalize_name(variant):
                    return value

    return None


def build_alias_set(team_name: str, canonical_name: str, full_name: str) -> Set[str]:
    """Build a set of known aliases for a team"""
    aliases = set()

    # Add all variations of canonical name and full name
    for name in [canonical_name, full_name]:
        for variant in generate_name_variations(name):
            aliases.add(variant.lower())

    # Remove state indicators and add those variations too
    canonical_no_state = re.sub(r'\s*\([A-Z]{2}\)\s*', '', canonical_name).strip()
    if canonical_no_state != canonical_name:
        for variant in generate_name_variations(canonical_no_state):
            aliases.add(variant.lower())

    # Also add without periods
    aliases_with_periods = [a for a in aliases if '.' in a]
    for alias in aliases_with_periods:
        aliases.add(alias.replace('.', ''))

    return aliases


def generate_registry():
    """Generate the centralized team registry"""
    print("Loading existing mappings...")

    # Load all source data
    team_ids = load_team_ids()
    bballnet_mapping = load_bballnet_mapping()
    sports_ref_mapping = load_sports_ref_mapping()
    wikipedia_mapping = load_wikipedia_mapping()

    print(f"  - Team IDs: {len(team_ids)} teams")
    print(f"  - Bballnet mappings: {len(bballnet_mapping)} entries")
    print(f"  - Sports Reference mappings: {len(sports_ref_mapping)} entries")
    print(f"  - Wikipedia mappings: {len(wikipedia_mapping)} entries")

    # Build the registry
    teams = {}
    alias_index = {}

    print("\nBuilding team registry...")

    for team_id, full_name in team_ids.items():
        canonical_name = extract_canonical_name(full_name)
        mascot = extract_mascot(full_name)

        # Find service slugs
        bballnet_slug = find_slug_in_mapping(canonical_name, bballnet_mapping)
        if not bballnet_slug:
            bballnet_slug = find_slug_in_mapping(full_name, bballnet_mapping)

        sports_ref_slug = find_slug_in_mapping(canonical_name, sports_ref_mapping)
        if not sports_ref_slug:
            sports_ref_slug = find_slug_in_mapping(full_name, sports_ref_mapping)

        wikipedia_page = find_slug_in_mapping(canonical_name, wikipedia_mapping)
        if not wikipedia_page:
            wikipedia_page = find_slug_in_mapping(full_name, wikipedia_mapping)

        # Build aliases
        aliases = build_alias_set(canonical_name, canonical_name, full_name)

        # Also add the canonical name with mascot variations
        if mascot:
            aliases.add(f"{canonical_name.lower()} {mascot.lower()}")

        # Add manual aliases (common abbreviations that can't be auto-generated)
        if team_id in MANUAL_ALIASES:
            for alias in MANUAL_ALIASES[team_id]:
                aliases.add(alias.lower())

        # Create team entry
        team_entry = {
            "cbb_api_id": int(team_id),
            "canonical_name": canonical_name,
            "display_name": full_name,
            "mascot": mascot,
            "aliases": sorted(list(aliases)),
            "services": {
                "bballnet": bballnet_slug,
                "sports_reference": sports_ref_slug,
                "wikipedia_page": wikipedia_page,
                "barttorvik": canonical_name,  # Bart Torvik uses display names
                "kenpom": canonical_name  # KenPom uses display names
            }
        }

        teams[team_id] = team_entry

        # Add to alias index
        for alias in aliases:
            if alias in alias_index and alias_index[alias] != int(team_id):
                # Conflict - log but keep first
                print(f"  Warning: Alias '{alias}' maps to both {alias_index[alias]} and {team_id}")
            else:
                alias_index[alias] = int(team_id)

    # Build the registry structure
    registry = {
        "version": "1.0.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "team_count": len(teams),
        "alias_count": len(alias_index),
        "teams": teams,
        "alias_index": alias_index
    }

    # Write to file
    print(f"\nWriting registry to {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(registry, f, indent=2)

    print(f"\nRegistry generated successfully!")
    print(f"  - Teams: {len(teams)}")
    print(f"  - Aliases: {len(alias_index)}")

    # Report missing mappings
    missing_bballnet = sum(1 for t in teams.values() if not t['services']['bballnet'])
    missing_sports_ref = sum(1 for t in teams.values() if not t['services']['sports_reference'])
    missing_wikipedia = sum(1 for t in teams.values() if not t['services']['wikipedia_page'])

    print(f"\nMissing service mappings:")
    print(f"  - Bballnet: {missing_bballnet} teams")
    print(f"  - Sports Reference: {missing_sports_ref} teams")
    print(f"  - Wikipedia: {missing_wikipedia} teams")

    return registry


if __name__ == '__main__':
    registry = generate_registry()
