#!/usr/bin/env python3
"""
Read cached rosters - no API calls needed!
Use this in your app to get player classes instantly.
"""

import json
import os
from typing import List, Dict, Optional

CACHE_DIR = "rosters_cache"
ROSTERS_INDEX_FILE = "rosters_index.json"


class RosterCache:
    """Efficient roster cache reader - no API calls."""
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """Load the roster index."""
        try:
            with open(ROSTERS_INDEX_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def get_player_classes(self, team_id: str) -> List[Dict[str, str]]:
        """
        Get player classes for a team (from cache, no API call).
        
        Args:
            team_id: Team ID (e.g., "223")
        
        Returns:
            List of dicts: [{'name': '...', 'jersey': '...', 'class': '...'}, ...]
        """
        class_file = os.path.join(self.cache_dir, f"{team_id}_classes.json")
        
        try:
            with open(class_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def get_class_by_jersey(self, team_id: str, jersey: str) -> Optional[str]:
        """Get a specific player's class by jersey number."""
        players = self.get_player_classes(team_id)
        for player in players:
            if player['jersey'] == jersey:
                return player['class']
        return None
    
    def get_class_by_name(self, team_id: str, player_name: str) -> Optional[str]:
        """Get a specific player's class by name (partial match)."""
        players = self.get_player_classes(team_id)
        player_name_lower = player_name.lower()
        for player in players:
            if player_name_lower in player['name'].lower():
                return player['class']
        return None
    
    def get_full_roster(self, team_id: str) -> Optional[Dict]:
        """Get full roster data (if you need more than just classes)."""
        roster_file = os.path.join(self.cache_dir, f"{team_id}.json")
        try:
            with open(roster_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def list_cached_teams(self) -> Dict[str, Dict]:
        """List all cached teams."""
        return self.index
    
    def is_cached(self, team_id: str) -> bool:
        """Check if a team's roster is cached."""
        return team_id in self.index
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about cached rosters."""
        total_teams = len(self.index)
        total_players = sum(info.get('player_count', 0) for info in self.index.values())
        
        return {
            'total_teams': total_teams,
            'total_players': total_players,
            'cache_dir': self.cache_dir
        }


# Example usage
if __name__ == '__main__':
    cache = RosterCache()
    
    # Get stats
    stats = cache.get_cache_stats()
    print(f"Cached: {stats['total_teams']} teams, {stats['total_players']} players")
    
    # Get player classes for Oregon (team ID: 223)
    print("\n" + "="*60)
    print("Oregon Ducks - Player Classes (from cache)")
    print("="*60)
    
    players = cache.get_player_classes("223")
    for player in sorted(players, key=lambda x: int(x['jersey']) if x['jersey'].isdigit() else 999):
        print(f"#{player['jersey']:>3} {player['name']:<30} {player['class']}")
    
    # Get specific player's class
    print("\n" + "="*60)
    jersey = "12"
    player_class = cache.get_class_by_jersey("223", jersey)
    print(f"Jersey #{jersey} class: {player_class}")

