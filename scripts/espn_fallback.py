"""
ESPN API Fallback for College Basketball Data

When the primary CBBD API returns games with empty player stats,
this module fetches box score data from ESPN's undocumented API
and transforms it to match the CBBD format.

ESPN API endpoints used:
- Team schedule: https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{team_id}/schedule
- Game summary: https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={event_id}
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import time


# ESPN team ID mapping (CBBD team name -> ESPN team ID)
# Run fetch_espn_team_ids() to discover more IDs
ESPN_TEAM_IDS = {
    # Mountain West Conference
    "san diego state": "21",
    "unlv": "2439",
    "new mexico": "167",
    "colorado state": "36",
    "fresno state": "278",
    "utah state": "328",
    "boise state": "68",
    "air force": "2005",
    "nevada": "2440",
    "wyoming": "2704",
    "san jose state": "23",
    "grand canyon": "2253",
    
    # Pac-12 / Big Ten / Major conferences
    "ucla": "26",
    "oregon": "2483",
    "oregon state": "204",
    "usc": "30",
    "arizona": "12",
    "arizona state": "9",
    "washington": "264",
    "washington state": "265",
    "colorado": "38",
    "utah": "254",
    "stanford": "24",
    "california": "25",
    
    "michigan state": "127",
    "michigan": "130",
    "ohio state": "194",
    "indiana": "84",
    "purdue": "2509",
    "illinois": "356",
    "iowa": "2294",
    "wisconsin": "275",
    "minnesota": "135",
    "northwestern": "77",
    "penn state": "213",
    "maryland": "120",
    "nebraska": "158",
    "rutgers": "164",
    
    # SEC
    "kentucky": "96",
    "tennessee": "2633",
    "alabama": "333",
    "auburn": "2",
    "florida": "57",
    "georgia": "61",
    "arkansas": "8",
    "lsu": "99",
    "ole miss": "145",
    "mississippi state": "344",
    "texas a&m": "245",
    "missouri": "142",
    "south carolina": "2579",
    "vanderbilt": "238",
    
    # Big 12
    "kansas": "2305",
    "baylor": "239",
    "texas tech": "2641",
    "texas": "251",
    "oklahoma": "201",
    "oklahoma state": "197",
    "iowa state": "66",
    "west virginia": "277",
    "tcu": "2628",
    "kansas state": "2306",
    "cincinnati": "2132",
    "houston": "248",
    "ucf": "2116",
    "byu": "252",
    
    # ACC
    "duke": "150",
    "north carolina": "153",
    "nc state": "152",
    "virginia": "258",
    "virginia tech": "259",
    "wake forest": "154",
    "clemson": "228",
    "florida state": "52",
    "miami": "2390",
    "georgia tech": "59",
    "syracuse": "183",
    "pittsburgh": "221",
    "louisville": "97",
    "boston college": "103",
    "notre dame": "87",
    
    # Big East
    "uconn": "41",
    "connecticut": "41",
    "villanova": "222",
    "creighton": "156",
    "marquette": "269",
    "xavier": "2752",
    "providence": "2507",
    "seton hall": "2550",
    "st. john's": "2599",
    "butler": "2086",
    "georgetown": "46",
    "depaul": "305",
    
    # WAC / Other
    "eastern washington": "2247",
    "gonzaga": "2250",
    "saint mary's": "2608",
    
    # Add more teams as needed
}


class ESPNFallback:
    """
    Fetches box score data from ESPN when CBBD returns empty player stats.
    """
    
    def __init__(self, verbose: bool = True):
        """Initialize ESPN fallback client."""
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CBB-Data-Generator/1.0'
        })
        self.verbose = verbose
        self.last_request_time = 0
        self.min_request_interval = 0.3  # 300ms between ESPN requests
        
        # Cache team schedules to avoid repeated requests
        self._schedule_cache: Dict[str, List[Dict]] = {}
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[ESPN_FALLBACK] {message}")
    
    def get_espn_team_id(self, team_name: str) -> Optional[str]:
        """
        Get ESPN team ID for a team name.
        
        Args:
            team_name: Team name (e.g., "San Diego State")
            
        Returns:
            ESPN team ID or None if not found
        """
        normalized = team_name.lower().strip()
        
        # Direct lookup
        if normalized in ESPN_TEAM_IDS:
            return ESPN_TEAM_IDS[normalized]
        
        # Try without common suffixes
        for suffix in [' aztecs', ' bruins', ' ducks', ' spartans', ' eagles', ' badgers']:
            if normalized.endswith(suffix):
                base_name = normalized[:-len(suffix)]
                if base_name in ESPN_TEAM_IDS:
                    return ESPN_TEAM_IDS[base_name]
        
        return None
    
    def get_team_schedule(self, espn_team_id: str) -> List[Dict]:
        """
        Get team's season schedule from ESPN.
        
        Args:
            espn_team_id: ESPN team ID
            
        Returns:
            List of game events with IDs and dates
        """
        if espn_team_id in self._schedule_cache:
            return self._schedule_cache[espn_team_id]
        
        self._rate_limit()
        
        url = f"{self.base_url}/teams/{espn_team_id}/schedule"
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            events = data.get('events', [])
            self._schedule_cache[espn_team_id] = events
            self._log(f"Loaded {len(events)} games from ESPN schedule for team {espn_team_id}")
            return events
            
        except Exception as e:
            self._log(f"ERROR: Failed to get ESPN schedule for team {espn_team_id}: {e}")
            return []
    
    def find_espn_event_id(self, espn_team_id: str, game_date: str, opponent: str) -> Optional[str]:
        """
        Find ESPN event ID for a specific game.
        
        Args:
            espn_team_id: ESPN team ID
            game_date: Game date in ISO format (e.g., "2026-01-22T04:00:00.000Z")
            opponent: Opponent team name
            
        Returns:
            ESPN event ID or None if not found
        """
        schedule = self.get_team_schedule(espn_team_id)
        
        # Parse target date (handle various formats)
        try:
            if 'T' in game_date:
                target_date = game_date.split('T')[0]
            else:
                target_date = game_date
        except:
            self._log(f"ERROR: Could not parse game date: {game_date}")
            return None
        
        # Normalize opponent name for matching
        opponent_lower = opponent.lower().strip()
        
        for event in schedule:
            event_date = event.get('date', '')
            if 'T' in event_date:
                event_date_str = event_date.split('T')[0]
            else:
                event_date_str = event_date[:10] if len(event_date) >= 10 else event_date
            
            # Check date match
            if event_date_str == target_date:
                # Check opponent match (ESPN game name includes both teams)
                event_name = event.get('name', '').lower()
                if opponent_lower in event_name or opponent_lower.replace(' ', '') in event_name.replace(' ', ''):
                    event_id = event.get('id')
                    self._log(f"Found ESPN event {event_id} for {target_date} vs {opponent}")
                    return event_id
        
        # Try fuzzy date match (+/- 1 day) in case of timezone issues
        try:
            from datetime import timedelta
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            for delta in [-1, 1]:
                alt_date = (target_dt + timedelta(days=delta)).strftime('%Y-%m-%d')
                for event in schedule:
                    event_date = event.get('date', '')
                    if 'T' in event_date:
                        event_date_str = event_date.split('T')[0]
                    else:
                        event_date_str = event_date[:10] if len(event_date) >= 10 else event_date
                    
                    if event_date_str == alt_date:
                        event_name = event.get('name', '').lower()
                        if opponent_lower in event_name:
                            event_id = event.get('id')
                            self._log(f"Found ESPN event {event_id} for {alt_date} vs {opponent} (date adjusted from {target_date})")
                            return event_id
        except Exception as e:
            self._log(f"Fuzzy date match failed: {e}")
        
        self._log(f"WARNING: Could not find ESPN event for {target_date} vs {opponent}")
        return None
    
    def get_game_box_score(self, event_id: str) -> Optional[Dict]:
        """
        Get full box score data from ESPN for a game.
        
        Args:
            event_id: ESPN event ID
            
        Returns:
            Box score data or None if failed
        """
        self._rate_limit()
        
        url = f"{self.base_url}/summary?event={event_id}"
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            self._log(f"Retrieved box score for event {event_id}")
            return data
            
        except Exception as e:
            self._log(f"ERROR: Failed to get ESPN box score for event {event_id}: {e}")
            return None
    
    def transform_espn_to_cbbd_format(self, espn_data: Dict, target_team: str, cbbd_game: Dict) -> List[Dict]:
        """
        Transform ESPN box score data to CBBD player stats format.
        
        Args:
            espn_data: ESPN summary response
            target_team: Team name to get stats for
            cbbd_game: Original CBBD game data (for context fields)
            
        Returns:
            List of player stat dictionaries in CBBD format
        """
        players = []
        
        try:
            # Find the team in ESPN data
            boxscore_players = espn_data.get('boxscore', {}).get('players', [])
            target_team_lower = target_team.lower()
            
            team_data = None
            for team in boxscore_players:
                team_name = team.get('team', {}).get('displayName', '').lower()
                if target_team_lower in team_name or team_name in target_team_lower:
                    team_data = team
                    break
            
            if not team_data:
                self._log(f"WARNING: Could not find {target_team} in ESPN box score")
                return []
            
            # Get stat column labels
            # ESPN format: statistics[0] contains starters+bench with labels and athletes
            stats_section = team_data.get('statistics', [{}])[0]
            labels = stats_section.get('labels', [])
            athletes = stats_section.get('athletes', [])
            
            # Map ESPN labels to indices
            label_map = {label.upper(): idx for idx, label in enumerate(labels)}
            
            for athlete in athletes:
                stats = athlete.get('stats', [])
                if not stats:
                    continue  # Player didn't play (DNP)
                
                # Extract player info
                athlete_info = athlete.get('athlete', {})
                player_id = athlete_info.get('id')
                player_name = athlete_info.get('displayName', '')
                position = athlete_info.get('position', {}).get('abbreviation', '')
                
                # Parse stats using label indices
                def get_stat(label: str, default: Any = 0) -> Any:
                    idx = label_map.get(label)
                    if idx is not None and idx < len(stats):
                        val = stats[idx]
                        if val == '' or val == '-':
                            return default
                        return val
                    return default
                
                def parse_made_attempted(val: str) -> tuple:
                    """Parse 'made-attempted' format like '7-12'"""
                    if not val or val == '-':
                        return (0, 0)
                    try:
                        parts = val.split('-')
                        return (int(parts[0]), int(parts[1]))
                    except:
                        return (0, 0)
                
                # Parse shooting stats
                fg_made, fg_attempted = parse_made_attempted(get_stat('FG', '0-0'))
                three_made, three_attempted = parse_made_attempted(get_stat('3PT', '0-0'))
                ft_made, ft_attempted = parse_made_attempted(get_stat('FT', '0-0'))
                
                # Calculate 2PT (FG minus 3PT)
                two_made = fg_made - three_made
                two_attempted = fg_attempted - three_attempted
                
                # Parse other stats
                minutes = int(get_stat('MIN', 0)) if get_stat('MIN', 0) != '' else 0
                points = int(get_stat('PTS', 0)) if get_stat('PTS', 0) != '' else 0
                total_reb = int(get_stat('REB', 0)) if get_stat('REB', 0) != '' else 0
                oreb = int(get_stat('OREB', 0)) if get_stat('OREB', 0) != '' else 0
                dreb = int(get_stat('DREB', 0)) if get_stat('DREB', 0) != '' else 0
                assists = int(get_stat('AST', 0)) if get_stat('AST', 0) != '' else 0
                turnovers = int(get_stat('TO', 0)) if get_stat('TO', 0) != '' else 0
                steals = int(get_stat('STL', 0)) if get_stat('STL', 0) != '' else 0
                blocks = int(get_stat('BLK', 0)) if get_stat('BLK', 0) != '' else 0
                fouls = int(get_stat('PF', 0)) if get_stat('PF', 0) != '' else 0
                
                # Determine if starter (first 5 in the list typically)
                starter = athlete.get('starter', False)
                
                # Build CBBD-format player dict
                player_stats = {
                    'athleteId': int(player_id) if player_id else None,
                    'athleteSourceId': player_id,
                    'name': player_name,
                    'position': position,
                    'starter': starter,
                    'ejected': False,
                    'minutes': minutes,
                    'points': points,
                    'turnovers': turnovers,
                    'fouls': fouls,
                    'assists': assists,
                    'steals': steals,
                    'blocks': blocks,
                    'fieldGoals': {
                        'made': fg_made,
                        'attempted': fg_attempted,
                        'pct': round(fg_made / fg_attempted * 100, 1) if fg_attempted > 0 else 0
                    },
                    'twoPointFieldGoals': {
                        'made': two_made,
                        'attempted': two_attempted,
                        'pct': round(two_made / two_attempted * 100, 1) if two_attempted > 0 else 0
                    },
                    'threePointFieldGoals': {
                        'made': three_made,
                        'attempted': three_attempted,
                        'pct': round(three_made / three_attempted * 100, 1) if three_attempted > 0 else 0
                    },
                    'freeThrows': {
                        'made': ft_made,
                        'attempted': ft_attempted,
                        'pct': round(ft_made / ft_attempted * 100, 1) if ft_attempted > 0 else 0
                    },
                    'rebounds': {
                        'offensive': oreb,
                        'defensive': dreb,
                        'total': total_reb if total_reb > 0 else (oreb + dreb)
                    },
                    # ESPN fallback marker for debugging
                    '_source': 'espn_fallback'
                }
                
                players.append(player_stats)
            
            self._log(f"Transformed {len(players)} player stats from ESPN for {target_team}")
            return players
            
        except Exception as e:
            self._log(f"ERROR: Failed to transform ESPN data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def patch_empty_games(self, game_data: List[Dict], team_name: str) -> List[Dict]:
        """
        Patch games with empty player arrays using ESPN fallback.
        
        Args:
            game_data: List of game data from CBBD API
            team_name: Team name for ESPN lookup
            
        Returns:
            Updated game_data with ESPN stats patched in
        """
        if not game_data:
            return game_data
        
        espn_team_id = self.get_espn_team_id(team_name)
        if not espn_team_id:
            self._log(f"WARNING: No ESPN team ID mapping for '{team_name}' - cannot use fallback")
            return game_data
        
        patched_count = 0
        
        for game in game_data:
            players = game.get('players', [])
            
            # Check if this game needs patching
            if players is not None and len(players) > 0:
                continue  # Has player data, skip
            
            # Game has empty players - try ESPN fallback
            game_date = game.get('startDate', '')
            opponent = game.get('opponent', '')
            
            if not game_date or not opponent:
                self._log(f"WARNING: Game missing date or opponent, cannot patch")
                continue
            
            self._log(f"Attempting ESPN fallback for {game_date[:10]} vs {opponent}")
            
            # Find ESPN event
            event_id = self.find_espn_event_id(espn_team_id, game_date, opponent)
            if not event_id:
                continue
            
            # Get box score
            espn_data = self.get_game_box_score(event_id)
            if not espn_data:
                continue
            
            # Transform and patch
            patched_players = self.transform_espn_to_cbbd_format(espn_data, team_name, game)
            if patched_players:
                game['players'] = patched_players
                game['_espn_patched'] = True
                game['_espn_event_id'] = event_id
                patched_count += 1
                self._log(f"✓ Patched {game_date[:10]} vs {opponent} with {len(patched_players)} players from ESPN")
        
        if patched_count > 0:
            self._log(f"Patched {patched_count} games with ESPN fallback data")
        
        return game_data


# Convenience function for quick patching
def patch_game_data_with_espn(game_data: List[Dict], team_name: str, verbose: bool = True) -> List[Dict]:
    """
    Convenience function to patch game data with ESPN fallback.
    
    Args:
        game_data: List of game data from CBBD API
        team_name: Team name for ESPN lookup
        verbose: Whether to print progress
        
    Returns:
        Updated game_data with ESPN stats patched in
    """
    fallback = ESPNFallback(verbose=verbose)
    return fallback.patch_empty_games(game_data, team_name)
