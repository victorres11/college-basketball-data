#!/usr/bin/env python3
"""
FoxSports Roster Scraper

Fetches roster data from FoxSports and updates the cache.
Can be called on-demand during data generation if cache is missing/stale.

Usage:
    from foxsports_scraper import fetch_and_cache_roster

    # Fetch roster for a team using FoxSports numeric ID from team registry
    players = fetch_and_cache_roster("Northwestern", "90")

Note: FoxSports uses numeric team IDs (e.g., "90" for Northwestern).
Use scripts/team_lookup.py to get the foxsports_id for a team:
    lookup = get_team_lookup()
    foxsports_id = lookup.lookup("Northwestern", "foxsports_id")  # → "90"
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Cache directory
CACHE_DIR = Path(__file__).parent / 'rosters_cache'


def fetch_foxsports_roster(foxsports_id: str) -> Optional[Dict]:
    """
    Fetch roster data from FoxSports API.

    Args:
        foxsports_id: FoxSports numeric team ID (e.g., "90" for Northwestern)

    Returns:
        Raw JSON data from FoxSports, or None if fetch fails
    """
    # FoxSports API endpoint - uses numeric team ID, not slug
    url = f"https://api.foxsports.com/bifrost/v1/cbk/team/{foxsports_id}/roster?apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    try:
        request = Request(url, headers=headers)
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except HTTPError as e:
        print(f"HTTP Error fetching {team_slug}: {e.code} {e.reason}")
        return None
    except URLError as e:
        print(f"URL Error fetching {team_slug}: {e.reason}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error for {team_slug}: {e}")
        return None
    except Exception as e:
        print(f"Error fetching {team_slug}: {e}")
        return None


def parse_roster_to_classes(raw_data: Dict) -> List[Dict[str, str]]:
    """
    Parse FoxSports roster JSON into simplified player classes list.

    Args:
        raw_data: Raw JSON from FoxSports API

    Returns:
        List of dicts: [{'name': '...', 'jersey': '...', 'class': '...'}, ...]
    """
    players = []

    if not raw_data or 'groups' not in raw_data:
        return players

    for group in raw_data.get('groups', []):
        # Skip summary/stats groups
        if group.get('template') != 'table-roster':
            continue

        # Check if this is a player roster table (has CLS column)
        headers = group.get('headers', [{}])[0].get('columns', [])
        has_class_column = any(col.get('text') == 'CLS' for col in headers)

        if not has_class_column:
            continue

        for row in group.get('rows', []):
            columns = row.get('columns', [])

            if len(columns) < 3:
                continue

            # Column 0: Name with jersey in superscript
            # Column 1: Position
            # Column 2: Class
            name_col = columns[0]
            position_col = columns[1]
            class_col = columns[2]

            name = name_col.get('text', '').strip()
            jersey = name_col.get('superscript', '').replace('#', '').strip()
            position = position_col.get('text', '').strip()
            player_class = class_col.get('text', '').strip()

            if name and jersey:
                players.append({
                    'name': name,
                    'jersey': jersey,
                    'position': position or 'N/A',
                    'class': player_class or 'N/A'
                })

    return players


def save_to_cache(foxsports_id: str, raw_data: Dict, players: List[Dict]) -> bool:
    """
    Save fetched data to cache files.

    Args:
        foxsports_id: Team ID for cache filename
        raw_data: Raw JSON to save to {id}.json
        players: Parsed player list to save to {id}_classes.json

    Returns:
        True if saved successfully
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Save raw data
        raw_file = CACHE_DIR / f'{foxsports_id}.json'
        with open(raw_file, 'w') as f:
            json.dump(raw_data, f)

        # Save classes data
        classes_file = CACHE_DIR / f'{foxsports_id}_classes.json'
        with open(classes_file, 'w') as f:
            json.dump(players, f, indent=2)

        print(f"[FOXSPORTS] Cached {len(players)} players to {classes_file.name}")
        return True
    except Exception as e:
        print(f"[FOXSPORTS] Error saving cache for {foxsports_id}: {e}")
        return False


def fetch_and_cache_roster(team_name: str, foxsports_id: str) -> List[Dict[str, str]]:
    """
    Fetch roster from FoxSports and update cache.

    This is the main function to call from the generator when cache is missing.

    Args:
        team_name: Team name (e.g., "Northwestern")
        foxsports_id: FoxSports numeric team ID (e.g., "90")

    Returns:
        List of player dicts with name, jersey, class
    """
    print(f"[FOXSPORTS] Fetching fresh roster for {team_name} (ID: {foxsports_id})...")

    # Fetch from API using numeric ID directly
    raw_data = fetch_foxsports_roster(foxsports_id)

    if not raw_data:
        print(f"[FOXSPORTS] Failed to fetch roster for {team_name}")
        return []

    # Parse players
    players = parse_roster_to_classes(raw_data)

    if not players:
        print(f"[FOXSPORTS] No players found in roster for {team_name}")
        return []

    # Save to cache
    save_to_cache(foxsports_id, raw_data, players)

    return players


def get_cached_or_fetch(team_name: str, foxsports_id: str, max_age_hours: int = 24) -> List[Dict[str, str]]:
    """
    Get roster from cache if fresh, otherwise fetch from FoxSports.

    Args:
        team_name: Team name
        foxsports_id: FoxSports team ID
        max_age_hours: Maximum cache age in hours before refreshing

    Returns:
        List of player dicts
    """
    classes_file = CACHE_DIR / f'{foxsports_id}_classes.json'

    # Check if cache exists and is fresh
    if classes_file.exists():
        file_age_hours = (time.time() - classes_file.stat().st_mtime) / 3600

        if file_age_hours < max_age_hours:
            # Use cached data
            with open(classes_file) as f:
                players = json.load(f)
            print(f"[FOXSPORTS] Using cached roster for {team_name} ({len(players)} players, {file_age_hours:.1f}h old)")
            return players
        else:
            print(f"[FOXSPORTS] Cache stale for {team_name} ({file_age_hours:.1f}h old), refreshing...")

    # Fetch fresh data
    return fetch_and_cache_roster(team_name, foxsports_id)


# For testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        team = sys.argv[1]
        # Look up foxsports_id from team name
        import sys as sys2
        sys2.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        from team_lookup import get_team_lookup

        lookup = get_team_lookup()
        fox_id = lookup.lookup(team, 'foxsports_id')

        if fox_id:
            players = fetch_and_cache_roster(team, fox_id)
            print(f"\nFetched {len(players)} players for {team}:")
            for p in players:
                print(f"  #{p['jersey']:>2} {p['name']:<25} {p['class']}")
        else:
            print(f"Team '{team}' not found in registry")
    else:
        print("Usage: python foxsports_scraper.py <team_name>")
        print("Example: python foxsports_scraper.py Northwestern")
