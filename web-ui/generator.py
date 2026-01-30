"""
Generic team data generator that works with any team.
Refactored from the team-specific generator scripts.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from cbb_api_wrapper import CollegeBasketballAPI

# Import ESPN fallback for patching games with missing player stats
try:
    from espn_fallback import ESPNFallback, patch_game_data_with_espn
    ESPN_FALLBACK_AVAILABLE = True
    print("[GENERATOR] ESPN fallback import: OK")
except ImportError as e:
    ESPN_FALLBACK_AVAILABLE = False
    print(f"Warning: ESPN fallback not available: {e}")

# Import centralized team lookup
try:
    from team_lookup import get_team_lookup
    TEAM_LOOKUP_AVAILABLE = True
    print("[GENERATOR] Team lookup import: OK")
except ImportError as e:
    TEAM_LOOKUP_AVAILABLE = False
    print(f"Warning: Team lookup not available: {e}")
import json
from datetime import datetime, timezone
import time
from s3_handler import load_historical_stats_from_s3

# Import FoxSports roster cache and on-demand scraper
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
foxsports_path = os.path.join(project_root, 'foxsports_rosters')
sys.path.insert(0, foxsports_path)
try:
    from roster_cache_reader import RosterCache
    FOXSPORTS_CACHE_AVAILABLE = True
except ImportError:
    FOXSPORTS_CACHE_AVAILABLE = False
    print("Warning: FoxSports roster cache not available")

# Import FoxSports on-demand scraper (fetches fresh roster when cache is missing)
try:
    from foxsports_scraper import fetch_and_cache_roster, get_cached_or_fetch
    FOXSPORTS_SCRAPER_AVAILABLE = True
    print("[GENERATOR] FoxSports scraper import: OK")
except ImportError as e:
    FOXSPORTS_SCRAPER_AVAILABLE = False
    print(f"Warning: FoxSports scraper not available: {e}")

# Import data quality monitoring framework
try:
    from data_quality import DataQualityHub, Severity, ValidationResult, normalize_name
    from validators import (
        validate_foxsports_roster_match,
        validate_class_year_coverage,
        validate_roster_size,
    )
    DATA_QUALITY_AVAILABLE = True
    print("[GENERATOR] Data quality framework import: OK")
except ImportError as e:
    DATA_QUALITY_AVAILABLE = False
    # Fallback normalize_name if data_quality not available
    def normalize_name(name):
        return name.lower().strip() if name else ''
    print(f"Warning: Data quality framework not available: {e}")

# Import quadrant scraper
misc_data_sources_path = os.path.join(project_root, 'misc_data_sources')
sys.path.insert(0, os.path.join(misc_data_sources_path, 'quadrants', 'scripts'))
try:
    from quadrant_wins import get_quadrant_data
    QUADRANT_SCRAPER_AVAILABLE = True
    print("[GENERATOR] Quadrant scraper import: OK")
except ImportError:
    QUADRANT_SCRAPER_AVAILABLE = False
    print("Warning: Quadrant scraper not available")

# Import NET rating scraper
sys.path.insert(0, os.path.join(misc_data_sources_path, 'quadrants', 'scripts'))
try:
    from net_rating import get_net_rating
    NET_RATING_SCRAPER_AVAILABLE = True
    print("[GENERATOR] NET rating scraper import: OK")
except ImportError:
    NET_RATING_SCRAPER_AVAILABLE = False
    print("Warning: NET rating scraper not available")

# Import coach history scraper
sys.path.insert(0, os.path.join(misc_data_sources_path, 'coaching_history', 'scripts'))
try:
    from coach_history import get_coach_history, get_winningest_coach
    COACH_HISTORY_SCRAPER_AVAILABLE = True
    print("[GENERATOR] Coach history scraper import: OK")
except ImportError:
    COACH_HISTORY_SCRAPER_AVAILABLE = False
    print("Warning: Coach history scraper not available")

# Import KenPom API client
sys.path.insert(0, os.path.join(misc_data_sources_path, 'kenpom', 'scripts'))
try:
    from kenpom_api import get_kenpom_team_data
    KENPOM_API_AVAILABLE = True
    print("[GENERATOR] KenPom API import: OK")
except ImportError as e:
    KENPOM_API_AVAILABLE = False
    print(f"Warning: KenPom API not available: {e}")

# Import Bart Torvik teamsheets scraper
sys.path.insert(0, os.path.join(misc_data_sources_path, 'barttorvik', 'scripts'))
try:
    from barttorvik_teamsheets import get_team_teamsheet_data
    BARTTORVIK_SCRAPER_AVAILABLE = True
    print("[GENERATOR] Bart Torvik scraper import: OK")
except ImportError as e:
    BARTTORVIK_SCRAPER_AVAILABLE = False
    print(f"Warning: Bart Torvik scraper not available: {e}")

# Import Wikipedia scraper
sys.path.insert(0, os.path.join(misc_data_sources_path, 'wikipedia', 'scripts'))
try:
    from wikipedia_data import get_wikipedia_team_data, get_season_rankings
    from team_name_mapping import get_wikipedia_page_title_safe
    WIKIPEDIA_SCRAPER_AVAILABLE = True
    print("[GENERATOR] Wikipedia scraper import: OK")
except ImportError as e:
    WIKIPEDIA_SCRAPER_AVAILABLE = False
    print(f"Warning: Wikipedia scraper not available: {e}")

# Import Pydantic schema validation
try:
    from schemas import validate_team_data
    SCHEMA_VALIDATION_AVAILABLE = True
    print("[GENERATOR] Schema validation import: OK")
except ImportError as e:
    SCHEMA_VALIDATION_AVAILABLE = False
    print(f"Warning: Schema validation not available: {e}")

# Import helper functions - we'll need to import from a shared location
# For now, we'll import from one of the existing generators
# In production, these should be in a shared utilities module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "generator_utils", 
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'generate_oregon_data_json_2026.py')
)
generator_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator_utils)

get_player_career_season_stats = generator_utils.get_player_career_season_stats
calculate_player_conference_rankings_from_list = generator_utils.calculate_player_conference_rankings_from_list
calculate_conference_rankings = generator_utils.calculate_conference_rankings
calculate_per_game_stats = generator_utils.calculate_per_game_stats
calculate_regular_season_stats = generator_utils.calculate_regular_season_stats


def calculate_possession_game_records(team_game_stats):
    """
    Calculate win/loss records for 1-possession and 2-possession games.
    
    Rules:
    - 1 possession: margin of 0-3 points (inclusive)
    - 2 possession: margin of 4-6 points (inclusive)
    
    Args:
        team_game_stats: List of game stat objects
        
    Returns:
        Dictionary with 'onePossession' and 'twoPossession' records
        Each record has 'wins' and 'losses'
    """
    one_possession = {'wins': 0, 'losses': 0}
    two_possession = {'wins': 0, 'losses': 0}
    
    for game in team_game_stats:
        team_points = game.get('teamStats', {}).get('points', {}).get('total', 0)
        opponent_points = game.get('opponentStats', {}).get('points', {}).get('total', 0)
        
        # Calculate margin (always positive, we'll determine win/loss separately)
        margin = abs(team_points - opponent_points)
        
        # Determine if it's a win or loss
        is_win = team_points > opponent_points
        is_loss = opponent_points > team_points
        
        # Categorize by margin
        if 0 <= margin <= 3:  # 1 possession game
            if is_win:
                one_possession['wins'] += 1
            elif is_loss:
                one_possession['losses'] += 1
        elif 4 <= margin <= 6:  # 2 possession game
            if is_win:
                two_possession['wins'] += 1
            elif is_loss:
                two_possession['losses'] += 1
    
    return {
        'onePossession': one_possession,
        'twoPossession': two_possession
    }


def normalize_jersey(jersey):
    """
    Normalize jersey number for matching.
    - Strip whitespace
    - Keep leading zeros (00 stays 00, 0 stays 0)
    - Handle None/"N/A"/empty strings
    """
    if not jersey or jersey == "N/A":
        return None
    normalized = str(jersey).strip()
    if not normalized:  # Empty string after stripping
        return None
    return normalized


def load_cached_roster(team_name, season):
    """Load cached roster file if it exists."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    team_slug = team_name.lower().replace(' ', '_')
    roster_path = os.path.join(project_root, 'data', 'rosters', str(season), f'{team_slug}_roster.json')
    
    if os.path.exists(roster_path):
        try:
            with open(roster_path, 'r') as f:
                cached_data = json.load(f)
                # Create lookup by player name (unicode-normalized for safe matching)
                cached_lookup = {}
                for player in cached_data.get('players', []):
                    player_name = player.get('name', '')
                    if player_name:
                        cached_lookup[normalize_name(player_name)] = player
                return cached_lookup
        except Exception as e:
            print(f"Warning: Could not load cached roster: {e}")
    return {}


def generate_team_data(team_name, season, progress_callback=None, include_historical_stats=None, force_historical_refresh=False, force_refresh_roster=False):
    """
    Generate team data JSON file for any team.

    Args:
        team_name: Team name (e.g., "Oregon", "Wisconsin", "UCLA")
        season: Season year (e.g., 2026)
        progress_callback: Optional dict to update progress
        include_historical_stats: DEPRECATED - for backward compatibility only.
            If explicitly set (True/False), uses legacy behavior.
            If None (default), uses smart auto-detection.
        force_historical_refresh: When True, re-fetches all historical stats from API
            regardless of cached data. Default: False (uses cache when available).
        force_refresh_roster: When True, always fetches fresh roster from FoxSports
            regardless of cache age. Default: False (uses cache if < 1 week old).

    Returns:
        Path to generated JSON file

    Raises:
        Exception: If generation is cancelled
    """
    # Initialize status tracking
    # Use 'dataStatus' key to avoid conflict with 'status' key (which is 'queued', 'running', etc.)
    if progress_callback is not None:
        if 'dataStatus' not in progress_callback:
            progress_callback['dataStatus'] = []
    
    def check_cancelled():
        """Check if generation has been cancelled"""
        if progress_callback is not None and progress_callback.get('cancelled', False):
            raise Exception('Generation cancelled by user')
    
    def add_status(name, status, message=None, details=None):
        """Helper to add status entry"""
        if progress_callback is not None:
            status_entry = {
                'name': name,
                'status': status,  # 'success', 'failed', 'skipped', 'pending', 'warning'
                'message': message or '',
                'details': details or ''
            }
            if 'dataStatus' not in progress_callback:
                progress_callback['dataStatus'] = []
            progress_callback['dataStatus'].append(status_entry)
    # Load API key from config file before initializing API
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'api_config.txt')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                for line in f:
                    if line.startswith('CBB_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        os.environ['CBB_API_KEY'] = api_key
                        break
        except Exception as e:
            print(f"Warning: Could not load API key from config: {e}")
    
    if progress_callback:
        progress_callback['message'] = 'Initializing API...'
        progress_callback['progress'] = 2
    
    check_cancelled()
    
    api = CollegeBasketballAPI()
    
    # Add initial delay to help reset rate limit window if there were previous requests
    print(f"[GENERATOR] Initial delay (1s) to help reset rate limit window...")
    time.sleep(1)
    
    check_cancelled()

    # Team name normalization - use registry to get canonical name for API
    canonical_name = team_name
    if TEAM_LOOKUP_AVAILABLE:
        lookup = get_team_lookup()
        team_id = lookup.get_team_id(team_name)
        if team_id:
            resolved_name = lookup.get_canonical_name(team_name)
            if resolved_name:
                canonical_name = resolved_name
                print(f"[GENERATOR] Resolved '{team_name}' → '{canonical_name}' (ID: {team_id})")
            else:
                print(f"[GENERATOR] Team ID {team_id} found but no canonical name, using '{team_name}'")
        else:
            print(f"[GENERATOR] Team '{team_name}' not found in registry, using as-is")
    team_slug = canonical_name.lower()

    # Initialize data quality monitoring
    quality_hub = None
    if DATA_QUALITY_AVAILABLE:
        quality_hub = DataQualityHub(team_name, season, progress_callback)
        print(f"[GENERATOR] Data quality monitoring: ENABLED")
    
    # Helper function to get Sports Reference slug
    def get_sports_ref_slug(team_name_lower):
        """Convert team name to Sports Reference URL slug."""
        # Load comprehensive mapping from auto-generated file
        import os
        mapping_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'misc_data_sources', 'coaching_history', 'mappings', 'sports_ref_team_mapping.json')
        sports_ref_mapping = {}
        
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    mapping_data = json.load(f)
                    sports_ref_mapping = mapping_data.get('team_slug_mapping', {})
            except Exception as e:
                print(f"[GENERATOR] Warning: Could not load Sports Reference mapping: {e}")
        
        # First check comprehensive mapping
        if team_name_lower in sports_ref_mapping:
            return sports_ref_mapping[team_name_lower]
        
        # Fallback: convert underscores to hyphens (Sports Reference uses hyphens)
        # e.g., "michigan_state" -> "michigan-state"
        return team_name_lower.replace('_', '-')
    
    # Calculate date range based on season
    start_date = f'{season-1}-11-04'
    end_date = f'{season}-03-17'
    
    if progress_callback:
        progress_callback['message'] = 'Fetching game data...'
        progress_callback['progress'] = 3
    
    check_cancelled()
    
    # Fetch game data
    print(f"[GENERATOR] Fetching game data for {team_name} ({season})...")
    try:
        game_data = api.get_player_game_stats_by_date(start_date, end_date, team_slug)
        count = len(game_data) if game_data else 0
        print(f"[GENERATOR] Retrieved {count} game records")
        add_status('Game Data', 'success', f'Retrieved {count} game records')
        
        # Check for games with empty player stats and patch with ESPN fallback
        if game_data and ESPN_FALLBACK_AVAILABLE:
            empty_games = sum(1 for g in game_data if not g.get('players'))
            if empty_games > 0:
                print(f"[GENERATOR] Found {empty_games} games with empty player stats, attempting ESPN fallback...")
                try:
                    game_data = patch_game_data_with_espn(game_data, team_name, verbose=True)
                    patched = sum(1 for g in game_data if g.get('_espn_patched'))
                    if patched > 0:
                        print(f"[GENERATOR] ESPN fallback patched {patched}/{empty_games} games")
                        add_status('ESPN Fallback', 'success', f'Patched {patched} games with missing stats')
                    else:
                        print(f"[GENERATOR] ESPN fallback could not patch any games")
                        add_status('ESPN Fallback', 'warning', f'{empty_games} games still missing player stats')
                except Exception as espn_e:
                    print(f"[GENERATOR] ESPN fallback error: {espn_e}")
                    add_status('ESPN Fallback', 'failed', str(espn_e))
    except Exception as e:
        check_cancelled()  # Check before reporting error (might be cancellation)
        print(f"[GENERATOR] ERROR: Failed to fetch game data: {e}")
        add_status('Game Data', 'failed', str(e))
        game_data = None
    
    check_cancelled()
    
    if progress_callback:
        progress_callback['message'] = 'Fetching roster data...'
        progress_callback['progress'] = 4
    
    check_cancelled()
    
    # Fetch roster data
    print(f"[GENERATOR] Fetching roster data for {team_name} ({season})...")
    try:
        roster_data = api.get_team_roster(season, team_slug)
        player_count = len(roster_data[0]['players']) if roster_data and len(roster_data) > 0 and 'players' in roster_data[0] else 0
        print(f"[GENERATOR] Retrieved roster data ({player_count} players)")
        add_status('Roster Data', 'success', f'Retrieved {player_count} players')
    except Exception as e:
        check_cancelled()  # Check before reporting error
        print(f"[GENERATOR] ERROR: Failed to fetch roster data: {e}")
        add_status('Roster Data', 'failed', str(e))
        roster_data = None

    # Collect roster data for quality validation
    if quality_hub and roster_data and len(roster_data) > 0 and 'players' in roster_data[0]:
        quality_hub.collect('api_roster_players', roster_data[0]['players'])

    check_cancelled()

    if progress_callback:
        progress_callback['message'] = 'Fetching recruiting data...'
        progress_callback['progress'] = 5
    
    # Fetch recruiting data
    print(f"[GENERATOR] Fetching recruiting data for {team_name}...")
    try:
        recruiting_data = api.get_recruiting_players(team_name)
        count = len(recruiting_data) if recruiting_data else 0
        print(f"[GENERATOR] Retrieved {count} recruiting records")
        add_status('Recruiting Data', 'success', f'Retrieved {count} records')
    except Exception as e:
        print(f"[GENERATOR] ERROR: Failed to fetch recruiting data: {e}")
        add_status('Recruiting Data', 'failed', str(e))
        recruiting_data = []
    
    if progress_callback:
        progress_callback['message'] = 'Fetching team game stats...'
        progress_callback['progress'] = 6
    
    # Fetch team game stats
    print(f"[GENERATOR] Fetching team game stats for {team_name} ({season})...")
    try:
        team_game_stats = api.get_team_game_stats(season, start_date, end_date, team_slug, "regular")
        count = len(team_game_stats) if team_game_stats else 0
        print(f"[GENERATOR] Retrieved {count} team game stats")
        add_status('Team Game Stats', 'success', f'Retrieved {count} games')
    except Exception as e:
        print(f"[GENERATOR] ERROR: Failed to fetch team game stats: {e}")
        add_status('Team Game Stats', 'failed', str(e))
        team_game_stats = None
    
    if progress_callback:
        progress_callback['message'] = 'Fetching player season stats...'
        progress_callback['progress'] = 7
    
    # Fetch player season stats
    print(f"[GENERATOR] Fetching player season stats for {team_name} ({season})...")
    try:
        player_season_stats = api.get_player_season_stats(season, team_slug, "regular")
        count = len(player_season_stats) if player_season_stats else 0
        print(f"[GENERATOR] Retrieved {count} player season stats")
        add_status('Player Season Stats', 'success', f'Retrieved {count} players')
    except Exception as e:
        print(f"[GENERATOR] ERROR: Failed to fetch player season stats: {e}")
        add_status('Player Season Stats', 'failed', str(e))
        player_season_stats = []
    
    if progress_callback:
        progress_callback['message'] = 'Fetching player shooting stats...'
        progress_callback['progress'] = 7.5
    
    # Fetch player shooting stats (includes dunks, layups, jumpers, etc.)
    print(f"[GENERATOR] Fetching player shooting stats for {team_name} ({season})...")
    try:
        player_shooting_stats = api.get_player_shooting_stats(season, team_slug, "regular")
        count = len(player_shooting_stats) if player_shooting_stats else 0
        print(f"[GENERATOR] Retrieved {count} player shooting stats")
        add_status('Player Shooting Stats', 'success', f'Retrieved {count} players with tracked shots')
    except Exception as e:
        print(f"[GENERATOR] ERROR: Failed to fetch player shooting stats: {e}")
        add_status('Player Shooting Stats', 'failed', str(e))
        player_shooting_stats = []
    
    if progress_callback:
        progress_callback['message'] = 'Fetching team season stats...'
        progress_callback['progress'] = 8
    
    # Fetch team season stats
    print(f"[GENERATOR] Fetching team season stats for {team_name} ({season})...")
    try:
        team_season_stats = api.get_team_season_stats(season, team_slug, "regular")
        count = len(team_season_stats) if team_season_stats else 0
        print(f"[GENERATOR] Retrieved {count} team season stats")
        add_status('Team Season Stats', 'success', f'Retrieved team stats')
    except Exception as e:
        print(f"[GENERATOR] ERROR: Failed to fetch team season stats: {e}")
        add_status('Team Season Stats', 'failed', str(e))
        team_season_stats = []
    
    if progress_callback:
        progress_callback['message'] = 'Calculating conference rankings...'
        progress_callback['progress'] = 9
    
    check_cancelled()
    
    # Get conference name from team season stats
    conference_name = None
    if team_season_stats and len(team_season_stats) > 0:
        conference_name = team_season_stats[0].get('conference', 'Unknown')
    
    # Calculate conference rankings
    # Note: calculate_conference_rankings is hardcoded to 2026 in the function
    # We'll need to modify it to accept season parameter, but for MVP this works
    # The function calls api.get_team_season_stats(2026, ...) - we'll patch it
    try:
        # Temporarily monkey-patch the function to use our season
        original_func = calculate_conference_rankings
        # For now, only works for 2026 - we'd need to refactor the function
        if season == 2026:
            print(f"[GENERATOR] Calculating conference rankings for {team_name} in {conference_name}...")
            print(f"[GENERATOR] WARNING: This will fetch ALL team season stats (large API call)")
            conference_rankings = calculate_conference_rankings(api, team_name, conference_name or "Unknown")
            print(f"[GENERATOR] Conference rankings calculated")
            add_status('Conference Rankings', 'success', f'Calculated rankings for {conference_name}')
        else:
            # For other seasons, create empty rankings for now
            conference_rankings = {'conference': {}, 'd1': {}}
            add_status('Conference Rankings', 'skipped', 'Only available for 2026 season')
    except Exception as e:
        print(f"[GENERATOR] WARNING: Could not calculate rankings: {e}")
        import traceback
        traceback.print_exc()
        conference_rankings = {'conference': {}, 'd1': {}}
        add_status('Conference Rankings', 'failed', str(e))
    
    if progress_callback:
        progress_callback['message'] = 'Fetching all player stats for rankings...'
        progress_callback['progress'] = 10
    
    check_cancelled()
    
    # Fetch all conference players for individual player rankings
    print(f"[GENERATOR] WARNING: Fetching ALL player season stats (large API call - no team filter)")
    print(f"[GENERATOR] This is needed for conference player rankings but may trigger rate limits")
    try:
        all_conference_players = api.get_player_season_stats(season, season_type='regular')
        count = len(all_conference_players) if all_conference_players else 0
        print(f"[GENERATOR] Retrieved {count} total player records")
        add_status('All Player Stats (Rankings)', 'success', f'Retrieved {count} player records')
    except Exception as e:
        check_cancelled()  # Check before reporting error
        print(f"[GENERATOR] ERROR: Failed to fetch all player stats: {e}")
        add_status('All Player Stats (Rankings)', 'failed', str(e))
        all_conference_players = []
    
    check_cancelled()
    
    # Get FoxSports team ID from centralized team registry
    # IMPORTANT: Each service has its own ID system - never assume IDs match between services.
    # The team registry is the single source of truth for all service IDs/slugs.
    foxsports_team_id = None
    player_classes_by_jersey = {}
    foxsports_cache_loaded = False  # Track if we successfully loaded cache data

    if FOXSPORTS_CACHE_AVAILABLE and TEAM_LOOKUP_AVAILABLE:
        try:
            lookup = get_team_lookup()
            foxsports_team_id = lookup.lookup(team_name, "foxsports_id")

            if foxsports_team_id:
                print(f"[GENERATOR] FoxSports ID for '{team_name}': {foxsports_team_id}")
                cache_dir = os.path.join(foxsports_path, 'rosters_cache')

                # Ensure cache directory exists
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir, exist_ok=True)
                    print(f"[GENERATOR] Created FoxSports cache directory: {cache_dir}")

                # Load FoxSports roster with staleness-aware caching
                if force_refresh_roster and FOXSPORTS_SCRAPER_AVAILABLE:
                    # Force refresh requested - always fetch fresh
                    print(f"[FOXSPORTS] Force refresh requested for {team_name}")
                    add_status('Player Classes', 'pending', f'Force-refreshing roster from FoxSports...')
                    try:
                        cached_players = fetch_and_cache_roster(team_name, foxsports_team_id)
                        if cached_players:
                            print(f"[GENERATOR] Successfully fetched {len(cached_players)} players from FoxSports")
                        else:
                            print(f"[GENERATOR] FoxSports scraper returned no players for {team_name}")
                    except Exception as scrape_err:
                        print(f"[GENERATOR] Error fetching from FoxSports: {scrape_err}")
                        cached_players = []
                elif FOXSPORTS_SCRAPER_AVAILABLE:
                    # Use staleness-aware fetch (refreshes if > 168 hours / 1 week)
                    add_status('Player Classes', 'pending', f'Loading roster (refreshes if > 1 week old)...')
                    try:
                        cached_players = get_cached_or_fetch(team_name, foxsports_team_id, max_age_hours=168)
                    except Exception as scrape_err:
                        print(f"[GENERATOR] Error in staleness-aware fetch: {scrape_err}")
                        cached_players = []
                else:
                    # Fallback to read-only cache when scraper unavailable
                    cache = RosterCache(cache_dir=cache_dir)
                    cached_players = cache.get_player_classes(foxsports_team_id)

                if cached_players:
                    # Create lookup by normalized jersey number
                    for player in cached_players:
                        jersey = normalize_jersey(player.get('jersey'))
                        if jersey:
                            player_classes_by_jersey[jersey] = player.get('class')
                    print(f"Loaded {len(player_classes_by_jersey)} players from FoxSports for team {foxsports_team_id}")
                    add_status('Player Classes', 'success', f'Loaded {len(player_classes_by_jersey)} player classes')
                    foxsports_cache_loaded = True
                else:
                    print(f"WARNING: No players found from FoxSports for team {foxsports_team_id}")
                    print(f"  Cache file location: rosters_cache/{foxsports_team_id}_classes.json")
                    add_status('Player Classes', 'warning', f'No players found from FoxSports for team {foxsports_team_id}')
            else:
                print(f"Warning: No FoxSports ID found in registry for '{team_name}'")
                add_status('Player Classes', 'warning', f'No FoxSports ID in registry for {team_name}')
        except Exception as e:
            import traceback
            print(f"Error loading FoxSports roster cache: {e}")
            print(f"Traceback: {traceback.format_exc()}")

    # Collect FoxSports data for quality validation and run cross-validation
    if quality_hub:
        quality_hub.collect('foxsports_id', foxsports_team_id)
        quality_hub.collect('foxsports_source', 'cache' if foxsports_cache_loaded else 'fetched')

        # Collect FoxSports players if available
        if FOXSPORTS_CACHE_AVAILABLE and foxsports_team_id:
            try:
                cache_dir = os.path.join(foxsports_path, 'rosters_cache')
                cache = RosterCache(cache_dir=cache_dir)
                foxsports_players = cache.get_player_classes(foxsports_team_id)
                quality_hub.collect('foxsports_players', foxsports_players or [])
            except Exception:
                quality_hub.collect('foxsports_players', [])

        # Run FoxSports roster cross-validation immediately (CRITICAL check)
        if DATA_QUALITY_AVAILABLE:
            print("[GENERATOR] Running FoxSports roster cross-validation...")
            quality_hub.run_immediate(validate_foxsports_roster_match)

    # Load cached roster if available (for better class/year and high school data)
    cached_roster_lookup = load_cached_roster(team_name, season)
    
    # Create lookups - use normalize_name for unicode-safe matching
    roster_lookup = {}
    if roster_data and len(roster_data) > 0 and 'players' in roster_data[0]:
        for player in roster_data[0]['players']:
            player_name = player.get('name', '')
            roster_lookup[normalize_name(player_name)] = player
    
    recruiting_lookup = {}
    for recruit in recruiting_data:
        player_name = recruit.get('name', '')
        recruiting_lookup[normalize_name(player_name)] = recruit
    
    # Merge recruiting data (high school) into roster data
    for player_name, player_data in roster_lookup.items():
        if player_name in recruiting_lookup:
            recruit_data = recruiting_lookup[player_name]
            player_data['highSchool'] = recruit_data.get('school', 'N/A')
        else:
            # Try partial matching
            for recruit_name, recruit_data in recruiting_lookup.items():
                if player_name in recruit_name or recruit_name in player_name:
                    player_data['highSchool'] = recruit_data.get('school', 'N/A')
                    break
    
    # Get all players from roster - CBB API is the primary source
    # The roster endpoint determines who is on the team
    # Game data is only used for stats, not for discovering players
    # NOTE: We use normalize_name() to handle unicode diacritics (e.g., "Grbović" vs "Grbovic")
    all_roster_players = set()
    if roster_data and len(roster_data) > 0 and 'players' in roster_data[0]:
        for player in roster_data[0]['players']:
            player_name = player.get('name', '')
            if player_name:
                all_roster_players.add(normalize_name(player_name))

    # Add FoxSports-only players (players in FoxSports but not in CBB API)
    # This handles mid-season transfers and roster updates that CBB API hasn't caught up with
    foxsports_only_players = set()
    if FOXSPORTS_CACHE_AVAILABLE and foxsports_team_id:
        try:
            cache_dir = os.path.join(foxsports_path, 'rosters_cache')
            cache = RosterCache(cache_dir=cache_dir)

            # Load full FoxSports roster data (includes position, height, weight)
            full_foxsports_roster = cache.get_full_roster(foxsports_team_id)
            foxsports_full_data = {}  # name_lower -> {position, height, weight, jersey, class}

            if full_foxsports_roster:
                # Parse full roster data from FoxSports JSON format
                for group in full_foxsports_roster.get('groups', []):
                    # Skip summary groups (PLAYER COUNT)
                    header_text = ""
                    if group.get('headers') and len(group['headers']) > 0:
                        cols = group['headers'][0].get('columns', [])
                        if cols:
                            header_text = cols[0].get('text', '')

                    if header_text in ['GUARD', 'FORWARD', 'CENTER']:
                        for row in group.get('rows', []):
                            cols = row.get('columns', [])
                            if len(cols) >= 5:
                                name = cols[0].get('text', '')
                                jersey = cols[0].get('superscript', '').replace('#', '')
                                position = cols[1].get('text', '')
                                player_class = cols[2].get('text', '')
                                height = cols[3].get('text', '')
                                weight = cols[4].get('text', '')

                                if name:
                                    # Use normalize_name for unicode-safe comparison
                                    foxsports_full_data[normalize_name(name)] = {
                                        'name': name,
                                        'jersey': jersey,
                                        'position': position,
                                        'class': player_class,
                                        'height': height,
                                        'weight': weight
                                    }

            # Check for players in FoxSports but not in CBB API
            for fox_name_lower, fox_data in foxsports_full_data.items():
                if fox_name_lower not in all_roster_players:
                    # Add to players to process
                    foxsports_only_players.add(fox_name_lower)
                    all_roster_players.add(fox_name_lower)

                    # Create a roster_lookup entry with full FoxSports data
                    # Position and height format matches what the rest of the code expects
                    roster_lookup[fox_name_lower] = {
                        'name': fox_data['name'],
                        'jersey': fox_data['jersey'],
                        'position': fox_data['position'],
                        'height': fox_data['height'],  # Already formatted as "6'2\"" etc.
                        'weight': fox_data['weight'],  # Already formatted as "185 lbs" etc.
                        'playerClass': fox_data['class'],
                        'source': 'foxsports'  # Mark as FoxSports-only player
                    }
                    print(f"[GENERATOR] Added FoxSports-only player: {fox_data['name']} (#{fox_data['jersey']}, {fox_data['position']}, {fox_data['height']})")

            if foxsports_only_players:
                print(f"[GENERATOR] Added {len(foxsports_only_players)} players from FoxSports not in CBB API")
                add_status('FoxSports Roster Sync', 'success', f'Added {len(foxsports_only_players)} missing players')
        except Exception as e:
            import traceback
            print(f"[GENERATOR] Warning: Could not check FoxSports for missing players: {e}")
            traceback.print_exc()

    # Use roster players (CBB API + FoxSports-only) - game data is only for stats, not roster discovery
    # This ensures we only process players from the target team, not opponents
    all_players_to_process = all_roster_players
    
    if progress_callback:
        progress_callback['message'] = f'Processing {len(all_players_to_process)} players...'
        progress_callback['progress'] = 10  # Start of player processing
    
    check_cancelled()

    # Build consolidated data structure
    team_data = {
        'team': team_name,
        'season': f'{season-1}-{str(season)[2:]}',
        'seasonType': 'Regular',
        'dataGenerated': datetime.now(timezone.utc).isoformat(),
        'players': []
    }
    
    # Add team game stats if available
    if team_game_stats:
        team_data['teamGameStats'] = team_game_stats
    
    # Add team season stats with rankings if available
    if team_season_stats and len(team_season_stats) > 0:
        team_data['teamSeasonStats'] = team_season_stats[0]
        
        # Calculate and add per-game stats
        per_game_stats = calculate_per_game_stats(team_data['teamSeasonStats'])
        if per_game_stats:
            team_data['teamSeasonStats']['perGameStats'] = per_game_stats
        
        # Calculate and add possession game records
        if team_game_stats:
            possession_records = calculate_possession_game_records(team_game_stats)
            team_data['teamSeasonStats']['possessionGameRecords'] = possession_records
    
    # Add conference and D1 rankings if available
    if conference_rankings:
        team_data['conferenceRankings'] = conference_rankings['conference']
        team_data['d1Rankings'] = conference_rankings['d1']
    
    # Add total record from team season stats
    if team_season_stats and len(team_season_stats) > 0:
        season_stats = team_season_stats[0]
        team_data['totalRecord'] = {
            'wins': season_stats.get('wins', 0),
            'losses': season_stats.get('losses', 0),
            'games': season_stats.get('games', 0)
        }
    
    # Calculate conference record from game data
    if team_game_stats:
        conference_games = [game for game in team_game_stats if game.get('conferenceGame') == True]
        conference_wins = 0
        conference_losses = 0
        
        for game in conference_games:
            team_points = game.get('teamStats', {}).get('points', {}).get('total', 0)
            opponent_points = game.get('opponentStats', {}).get('points', {}).get('total', 0)
            
            if team_points > opponent_points:
                conference_wins += 1
            elif opponent_points > team_points:
                conference_losses += 1
        
        team_data['conferenceRecord'] = {
            'wins': conference_wins,
            'losses': conference_losses,
            'games': len(conference_games)
        }
        
        # Calculate home, away, and neutral site records
        home_wins = 0
        home_losses = 0
        away_wins = 0
        away_losses = 0
        neutral_wins = 0
        neutral_losses = 0
        
        for game in team_game_stats:
            is_home = game.get('isHome', False)
            is_neutral = game.get('neutralSite', False)
            team_points = game.get('teamStats', {}).get('points', {}).get('total', 0)
            opponent_points = game.get('opponentStats', {}).get('points', {}).get('total', 0)
            
            if team_points > opponent_points:
                if is_neutral:
                    neutral_wins += 1
                elif is_home:
                    home_wins += 1
                else:
                    away_wins += 1
            elif opponent_points > team_points:
                if is_neutral:
                    neutral_losses += 1
                elif is_home:
                    home_losses += 1
                else:
                    away_losses += 1
        
        team_data['homeRecord'] = {
            'wins': home_wins,
            'losses': home_losses,
            'games': home_wins + home_losses
        }
        
        team_data['awayRecord'] = {
            'wins': away_wins,
            'losses': away_losses,
            'games': away_wins + away_losses
        }
        
        team_data['neutralRecord'] = {
            'wins': neutral_wins,
            'losses': neutral_losses,
            'games': neutral_wins + neutral_losses
        }
    else:
        team_data['conferenceRecord'] = {
            'wins': 0,
            'losses': 0,
            'games': 0
        }
    
    # Fetch quadrant data from bballnet.com (optional)
    if QUADRANT_SCRAPER_AVAILABLE:
        if progress_callback:
            progress_callback['message'] = 'Fetching quadrant records...'
        print(f"[GENERATOR] Fetching quadrant data for {team_name}...")
        try:
            # Use centralized team lookup for bballnet slug
            bballnet_slug = None
            if TEAM_LOOKUP_AVAILABLE:
                lookup = get_team_lookup()
                bballnet_slug = lookup.lookup(team_name, "bballnet")
                if bballnet_slug:
                    print(f"[GENERATOR] Using bballnet slug from registry: {bballnet_slug}")

            # Fallback to team_slug if lookup fails
            if not bballnet_slug:
                bballnet_slug = team_slug
                print(f"[GENERATOR] Using fallback slug: {bballnet_slug}")

            quadrant_data = get_quadrant_data(bballnet_slug)
            
            # Format quadrant data for JSON output
            quadrant_records = {}
            for quad_num in ['1', '2', '3', '4']:
                quad_key = f'quad{quad_num}'
                if quad_key in quadrant_data.get('quadrants', {}):
                    quad_info = quadrant_data['quadrants'][quad_key]
                    quadrant_records[f'quad{quad_num}'] = {
                        'record': quad_info.get('record', '0-0'),
                        'wins': quad_info.get('wins', 0),
                        'losses': quad_info.get('losses', 0),
                        'opponents': quad_info.get('opponents', [])
                    }
            
            if quadrant_records:
                team_data['quadrantRecords'] = quadrant_records
                print(f"[GENERATOR] Successfully loaded quadrant data: {len(quadrant_records)} quadrants")
                add_status('Quadrant Records', 'success', f'Retrieved {len(quadrant_records)} quadrants')
            else:
                print(f"[GENERATOR] WARNING: Quadrant data returned but no quadrants found")
                add_status('Quadrant Records', 'failed', 'No quadrants found in response')
            
            # Add upcoming games if available (filter out already-played games)
            upcoming_games = quadrant_data.get('upcoming_games', [])
            if upcoming_games:
                # Filter out games that already appear in teamGameStats (already played)
                played_opponents = set()
                if team_data.get('teamGameStats'):
                    for game in team_data['teamGameStats']:
                        opponent = game.get('opponent', '').lower().strip()
                        if opponent:
                            played_opponents.add(opponent)

                # Filter upcoming games to exclude already-played opponents
                # Note: This is a simple filter by opponent name. For teams that play
                # the same opponent twice (home/away), this may filter too aggressively,
                # but it's better than showing duplicate games.
                original_count = len(upcoming_games)
                filtered_upcoming = []
                for game in upcoming_games:
                    opponent = game.get('opponent', '').lower().strip()
                    if opponent not in played_opponents:
                        filtered_upcoming.append(game)
                    else:
                        print(f"[GENERATOR] Filtered out already-played game vs {game.get('opponent')}")

                if filtered_upcoming:
                    team_data['upcomingGames'] = filtered_upcoming
                    filtered_count = original_count - len(filtered_upcoming)
                    msg = f'Retrieved {len(filtered_upcoming)} upcoming games'
                    if filtered_count > 0:
                        msg += f' (filtered {filtered_count} already played)'
                    print(f"[GENERATOR] Successfully loaded upcoming games: {len(filtered_upcoming)} games (filtered {filtered_count})")
                    add_status('Upcoming Games', 'success', msg)
                else:
                    print(f"[GENERATOR] INFO: All upcoming games already played")
                    add_status('Upcoming Games', 'skipped', 'All games already played')
            else:
                print(f"[GENERATOR] INFO: No upcoming games found")
                add_status('Upcoming Games', 'skipped', 'No upcoming games found')
        except Exception as e:
            print(f"[GENERATOR] WARNING: Failed to fetch quadrant data: {e}")
            import traceback
            traceback.print_exc()
            add_status('Quadrant Records', 'failed', str(e))
            # Don't fail the entire generation if quadrant scraping fails
    else:
        print(f"[GENERATOR] INFO: Quadrant scraper not available, skipping quadrant data")
        add_status('Quadrant Records', 'skipped', 'Scraper not available')
    
    # Fetch NET rating from bballnet.com (optional)
    if NET_RATING_SCRAPER_AVAILABLE:
        if progress_callback:
            progress_callback['message'] = 'Fetching NET rating...'
        # Use canonical_name for NET rating lookup
        net_team = canonical_name if canonical_name else team_name
        print(f"[GENERATOR] Searching for NET rating for {net_team}...")
        try:
            net_data = get_net_rating(net_team)
            if net_data and net_data.get('net_rating') is not None:
                team_data['netRating'] = {
                    'rating': net_data['net_rating'],
                    'previousRating': net_data.get('previous_rating'),
                    'source': 'bballnet.com',
                    'url': net_data.get('url')
                }
                found_name = net_data.get('team_name_found', team_name)
                print(f"[GENERATOR] Found NET rating for {team_name} (matched as: {found_name})")
                print(f"[GENERATOR] NET Rank: {net_data['net_rating']} (Previous: {net_data.get('previous_rating', 'N/A')})")
                add_status('NET Rating', 'success', f'Rank #{net_data["net_rating"]}')
            else:
                error_msg = net_data.get('error', 'Unknown error') if net_data else 'No data returned'
                print(f"[GENERATOR] WARNING: NET rating not found for {team_name}: {error_msg}")
                add_status('NET Rating', 'failed', error_msg)
        except Exception as e:
            print(f"[GENERATOR] WARNING: Failed to fetch NET rating for {team_name}: {e}")
            import traceback
            traceback.print_exc()
            add_status('NET Rating', 'failed', str(e))
            # Don't fail the entire generation if NET scraping fails
    else:
        print(f"[GENERATOR] INFO: NET rating scraper not available, skipping NET rating")
        add_status('NET Rating', 'skipped', 'Scraper not available')
    
    # Fetch coach history from Sports Reference (optional)
    if COACH_HISTORY_SCRAPER_AVAILABLE:
        if progress_callback:
            progress_callback['message'] = 'Fetching coach history...'
        print(f"[GENERATOR] Searching for coach history for {team_name}...")
        try:
            # Use centralized team lookup for sports reference slug
            sports_ref_slug = None
            if TEAM_LOOKUP_AVAILABLE:
                lookup = get_team_lookup()
                sports_ref_slug = lookup.lookup(team_name, "sports_reference")
                if sports_ref_slug:
                    print(f"[GENERATOR] Using sports_reference slug from registry: {sports_ref_slug}")

            # Fallback to old method if lookup fails
            if not sports_ref_slug:
                sports_ref_slug = get_sports_ref_slug(team_slug)
                print(f"[GENERATOR] Using fallback sports_ref_slug: {sports_ref_slug}")
            coach_history = get_coach_history(sports_ref_slug, years=None)  # Get all seasons
            if coach_history and len(coach_history) > 0:
                # Calculate average wins (overall and conference) for all seasons
                total_overall_wins = 0
                total_conference_wins = 0
                seasons_counted = 0
                
                for season_data in coach_history:
                    try:
                        overall_w = int(season_data.get('overallW', 0))
                        conf_w = int(season_data.get('conferenceW', 0))
                        total_overall_wins += overall_w
                        total_conference_wins += conf_w
                        seasons_counted += 1
                    except (ValueError, TypeError):
                        # Skip seasons with invalid win data
                        continue
                
                avg_overall_wins = round(total_overall_wins / seasons_counted, 1) if seasons_counted > 0 else 0
                avg_conference_wins = round(total_conference_wins / seasons_counted, 1) if seasons_counted > 0 else 0
                
                # Fetch winningest coach
                winningest_coach = None
                try:
                    winningest_coach = get_winningest_coach(sports_ref_slug)
                    if winningest_coach:
                        print(f"[GENERATOR] Found winningest coach: {winningest_coach['coach']} ({winningest_coach['wins']}-{winningest_coach['losses']})")
                except Exception as e:
                    print(f"[GENERATOR] WARNING: Failed to fetch winningest coach: {e}")
                
                team_data['coachHistory'] = {
                    'seasons': coach_history,
                    'source': 'sports-reference.com',
                    'url': f"https://www.sports-reference.com/cbb/schools/{sports_ref_slug}/men/",
                    'averageOverallWins': avg_overall_wins,
                    'averageConferenceWins': avg_conference_wins,
                    'seasonsCounted': seasons_counted
                }
                
                # Add winningest coach if found
                if winningest_coach:
                    team_data['coachHistory']['winningestCoach'] = winningest_coach
                    team_data['coachHistory']['winningestCoachUrl'] = f"https://www.sports-reference.com/cbb/schools/{sports_ref_slug}/men/coaches.html"
                
                print(f"[GENERATOR] Found coach history for {team_name}")
                print(f"[GENERATOR] Retrieved {len(coach_history)} complete seasons (excluding current incomplete season)")
                print(f"[GENERATOR] Average overall wins (all seasons): {avg_overall_wins:.1f}")
                print(f"[GENERATOR] Average conference wins (all seasons): {avg_conference_wins:.1f}")
                # Log first and last seasons
                if len(coach_history) > 0:
                    first = coach_history[0]
                    last = coach_history[-1]
                    print(f"[GENERATOR] Seasons: {first['season']} to {last['season']}")
                    print(f"[GENERATOR] Current coach: {first['coach']}")
                    add_status('Coach History', 'success', f'{len(coach_history)} seasons ({first["season"]} to {last["season"]})')
            else:
                print(f"[GENERATOR] WARNING: Coach history returned but no seasons found")
                add_status('Coach History', 'failed', 'No seasons found')
        except Exception as e:
            print(f"[GENERATOR] WARNING: Failed to fetch coach history for {team_name}: {e}")
            import traceback
            traceback.print_exc()
            add_status('Coach History', 'failed', str(e))
            # Don't fail the entire generation if coach history scraping fails
    else:
        print(f"[GENERATOR] INFO: Coach history scraper not available, skipping coach history")
        add_status('Coach History', 'skipped', 'Scraper not available')
    
    # Fetch KenPom data (optional)
    if KENPOM_API_AVAILABLE:
        if progress_callback:
            progress_callback['message'] = 'Fetching KenPom data...'
        # Use canonical_name for KenPom lookup (KenPom uses full team names like "Michigan State")
        kenpom_team = canonical_name if canonical_name else team_name
        print(f"[GENERATOR] Fetching KenPom data for {kenpom_team} (season {season})...")
        try:
            # Pass season parameter to ensure correct season data is fetched
            kenpom_result = get_kenpom_team_data(kenpom_team, season=season)
            
            if kenpom_result and 'data' in kenpom_result:
                kenpom_data = kenpom_result['data']
                structured_report = kenpom_data.get('report_table_structured', {})
                
                if structured_report:
                    team_data['kenpom'] = {
                        'reportTable': structured_report,
                        'source': 'kenpom.com',
                        'url': kenpom_result.get('url'),
                        'teamName': kenpom_result.get('team_name', team_name)
                    }
                    
                    # Log key metrics
                    if 'Adj. Efficiency' in structured_report:
                        adj_eff = structured_report['Adj. Efficiency']
                        offense = adj_eff.get('offense', 'N/A')
                        defense = adj_eff.get('defense', 'N/A')
                        offense_rank = adj_eff.get('offense_ranking', 'N/A')
                        defense_rank = adj_eff.get('defense_ranking', 'N/A')
                        print(f"[GENERATOR] KenPom Adj. Efficiency - Offense: {offense} (rank {offense_rank}), Defense: {defense} (rank {defense_rank})")
                    
                    if 'Adj. Tempo' in structured_report:
                        tempo = structured_report['Adj. Tempo']
                        combined = tempo.get('combined', 'N/A')
                        tempo_rank = tempo.get('ranking', 'N/A')
                        print(f"[GENERATOR] KenPom Adj. Tempo: {combined} (rank {tempo_rank})")
                    
                    categories_count = len([k for k in structured_report.keys() if structured_report[k]])
                    print(f"[GENERATOR] Successfully loaded KenPom data: {categories_count} categories")
                    add_status('KenPom Data', 'success', f'Retrieved {categories_count} categories')
                else:
                    print(f"[GENERATOR] WARNING: KenPom data returned but no report table found")
                    add_status('KenPom Data', 'failed', 'No report table found')
            else:
                print(f"[GENERATOR] WARNING: KenPom data returned but no structured data found")
                add_status('KenPom Data', 'failed', 'No structured data found')
        except Exception as e:
            print(f"[GENERATOR] WARNING: Failed to fetch KenPom data for {team_name}: {e}")
            import traceback
            traceback.print_exc()
            add_status('KenPom Data', 'failed', str(e))
            # Don't fail the entire generation if KenPom scraping fails
    else:
        print(f"[GENERATOR] INFO: KenPom scraper not available, skipping KenPom data")
        add_status('KenPom Data', 'skipped', 'Scraper not available')
    
    # Fetch Bart Torvik teamsheet data (optional)
    if BARTTORVIK_SCRAPER_AVAILABLE:
        if progress_callback:
            progress_callback['message'] = 'Fetching Bart Torvik teamsheet data...'
        # Use canonical_name for Bart Torvik lookup (uses full team names like "Michigan State")
        barttorvik_team = canonical_name if canonical_name else team_name
        print(f"[GENERATOR] Fetching Bart Torvik teamsheet data for {barttorvik_team}...")
        try:
            barttorvik_data = get_team_teamsheet_data(barttorvik_team, year=season)
            
            if barttorvik_data:
                team_data['barttorvik'] = {
                    'rank': barttorvik_data.get('rank'),
                    'seed': barttorvik_data.get('seed'),
                    'resume': barttorvik_data.get('resume', {}),
                    'quality': barttorvik_data.get('quality', {}),
                    'quadrants': barttorvik_data.get('quadrants', {}),
                    'source': 'barttorvik.com',
                    'url': f'https://barttorvik.com/teamsheets.php?conlimit=All&sort=8&year={season}'
                }
                
                # Log key metrics
                resume = barttorvik_data.get('resume', {})
                quality = barttorvik_data.get('quality', {})
                print(f"[GENERATOR] Bart Torvik - Rank: {barttorvik_data.get('rank', 'N/A')}, Seed: {barttorvik_data.get('seed', 'N/A')}")
                print(f"[GENERATOR] Bart Torvik Resume - NET: {resume.get('net', 'N/A')}, KPI: {resume.get('kpi', 'N/A')}, Avg: {resume.get('avg', 'N/A')}")
                print(f"[GENERATOR] Bart Torvik Quality - BPI: {quality.get('bpi', 'N/A')}, KenPom: {quality.get('kenpom', 'N/A')}, Avg: {quality.get('avg', 'N/A')}")
                
                # Log quadrant records
                quadrants = barttorvik_data.get('quadrants', {})
                if quadrants:
                    q1_record = quadrants.get('q1', {}).get('record', 'N/A')
                    q2_record = quadrants.get('q2', {}).get('record', 'N/A')
                    print(f"[GENERATOR] Bart Torvik Quadrants - Q1: {q1_record}, Q2: {q2_record}")
                
                add_status('Bart Torvik Data', 'success', f'Retrieved teamsheet data (Rank: {barttorvik_data.get("rank", "N/A")})')
            else:
                print(f"[GENERATOR] WARNING: Bart Torvik data not found for {team_name}")
                add_status('Bart Torvik Data', 'failed', 'Team not found in Bart Torvik data')
        except Exception as e:
            print(f"[GENERATOR] WARNING: Failed to fetch Bart Torvik data for {team_name}: {e}")
            import traceback
            traceback.print_exc()
            add_status('Bart Torvik Data', 'failed', str(e))
            # Don't fail the entire generation if Bart Torvik scraping fails
    else:
        print(f"[GENERATOR] INFO: Bart Torvik scraper not available, skipping Bart Torvik data")
        add_status('Bart Torvik Data', 'skipped', 'Scraper not available')
    
    # Fetch Wikipedia data (optional)
    if WIKIPEDIA_SCRAPER_AVAILABLE:
        if progress_callback:
            progress_callback['message'] = 'Fetching Wikipedia data...'
        print(f"[GENERATOR] Fetching Wikipedia data for {team_name}...")
        try:
            # Get Wikipedia page title
            wikipedia_page_title = get_wikipedia_page_title_safe(team_name)
            if wikipedia_page_title:
                print(f"[GENERATOR] Using Wikipedia page: {wikipedia_page_title}")
                wikipedia_data = get_wikipedia_team_data(wikipedia_page_title)
                
                if wikipedia_data:
                    # Add Wikipedia data to team_data
                    team_data['wikipedia'] = {
                        'universityName': wikipedia_data.get('university_name'),
                        'mascot': wikipedia_data.get('mascot'),
                        'headCoach': wikipedia_data.get('head_coach'),
                        'headCoachSeasons': wikipedia_data.get('head_coach_seasons'),
                        'conference': wikipedia_data.get('conference'),
                        'location': wikipedia_data.get('location'),
                        'arena': wikipedia_data.get('arena'),
                        'capacity': wikipedia_data.get('capacity'),
                        'allTimeRecord': wikipedia_data.get('all_time_record'),
                        'championships': {
                            'ncaaTournament': wikipedia_data.get('championships', {}).get('ncaa_tournament', []),
                            'ncaaRunnerUp': wikipedia_data.get('championships', {}).get('ncaa_runner_up', []),
                            'conferenceTournament': wikipedia_data.get('championships', {}).get('conference_tournament', []),
                            'regularSeason': wikipedia_data.get('championships', {}).get('regular_season', [])
                        },
                        'tournamentAppearances': {
                            'ncaaTournament': wikipedia_data.get('tournament_appearances', {}).get('ncaa_tournament'),
                            'ncaaTournamentYears': wikipedia_data.get('tournament_appearances', {}).get('ncaa_tournament_years', []),
                            'finalFour': wikipedia_data.get('tournament_appearances', {}).get('final_four'),
                            'finalFourYears': wikipedia_data.get('tournament_appearances', {}).get('final_four_years', []),
                            'eliteEight': wikipedia_data.get('tournament_appearances', {}).get('elite_eight'),
                            'eliteEightYears': wikipedia_data.get('tournament_appearances', {}).get('elite_eight_years', []),
                            'sweetSixteen': wikipedia_data.get('tournament_appearances', {}).get('sweet_sixteen'),
                            'sweetSixteenYears': wikipedia_data.get('tournament_appearances', {}).get('sweet_sixteen_years', [])
                        },
                        'source': 'wikipedia.org',
                        'url': f"https://en.wikipedia.org/wiki/{wikipedia_page_title.replace(' ', '_')}",
                        'pageTitle': wikipedia_data.get('page_title')
                    }

                    # Set mascot from Wikipedia (primary source) with fallback to team registry
                    if wikipedia_data.get('mascot'):
                        team_data['mascot'] = wikipedia_data.get('mascot')
                        print(f"[GENERATOR] Mascot: {wikipedia_data.get('mascot')}")
                    else:
                        # Fallback: try team registry for mascot
                        registry_mascot = None
                        if TEAM_LOOKUP_AVAILABLE:
                            lookup = get_team_lookup()
                            team_id = lookup.get_team_id(team_name)
                            if team_id:
                                team_info = lookup.get_team(team_id)
                                if team_info:
                                    registry_mascot = team_info.get('mascot')

                        if registry_mascot:
                            team_data['mascot'] = registry_mascot
                            team_data['wikipedia']['mascot'] = registry_mascot  # Also update wikipedia section
                            print(f"[GENERATOR] Mascot (from registry fallback): {registry_mascot}")
                        else:
                            print(f"[GENERATOR] WARNING: No mascot found in Wikipedia or registry for {team_name}")
                    
                    # Get season rankings (current and highest AP rankings)
                    try:
                        print(f"[GENERATOR] Fetching AP rankings for {team_name} ({season})...")
                        season_rankings = get_season_rankings(team_name, season)
                        if season_rankings:
                            team_data['wikipedia']['apRankings'] = {
                                'current': season_rankings.get('current_rank'),
                                'highest': season_rankings.get('highest_rank')
                            }
                            current_str = f"#{season_rankings.get('current_rank')}" if season_rankings.get('current_rank') else "Unranked"
                            highest_str = f"#{season_rankings.get('highest_rank')}" if season_rankings.get('highest_rank') else "Unranked"
                            print(f"[GENERATOR] AP Rankings retrieved - Current: {current_str}, Highest: {highest_str}")
                            add_status('AP Rankings', 'success', f'Current: {current_str}, Highest: {highest_str}')
                        else:
                            print(f"[GENERATOR] No AP rankings found for {team_name}")
                            add_status('AP Rankings', 'skipped', 'No rankings available')
                    except Exception as e:
                        print(f"[GENERATOR] WARNING: Could not fetch season rankings: {e}")
                        add_status('AP Rankings', 'failed', str(e))
                        # Don't fail if rankings can't be fetched
                    
                    # Log key information
                    ncaa_champs = len(wikipedia_data.get('championships', {}).get('ncaa_tournament', []))
                    final_four_count = wikipedia_data.get('tournament_appearances', {}).get('final_four', 0)
                    print(f"[GENERATOR] Wikipedia data retrieved successfully")
                    print(f"[GENERATOR] NCAA Championships: {ncaa_champs}, Final Four appearances: {final_four_count}")
                    add_status('Wikipedia Data', 'success', f'{ncaa_champs} NCAA titles, {final_four_count} Final Fours')
                else:
                    print(f"[GENERATOR] WARNING: Wikipedia data returned but is empty")
                    add_status('Wikipedia Data', 'failed', 'No data returned')
            else:
                print(f"[GENERATOR] WARNING: Could not find Wikipedia page for {team_name}")
                add_status('Wikipedia Data', 'failed', f'Page not found for {team_name}')
        except Exception as e:
            print(f"[GENERATOR] WARNING: Failed to fetch Wikipedia data for {team_name}: {e}")
            import traceback
            traceback.print_exc()
            add_status('Wikipedia Data', 'failed', str(e))
            # Don't fail the entire generation if Wikipedia scraping fails
    else:
        print(f"[GENERATOR] INFO: Wikipedia scraper not available, skipping Wikipedia data")
        add_status('Wikipedia Data', 'skipped', 'Scraper not available')
    
    # Create lookup for player season stats (for rankings)
    # Use normalize_name for unicode-safe matching
    player_stats_lookup = {}
    if player_season_stats:
        for player in player_season_stats:
            player_name = player.get('name', '')
            if player_name:
                player_stats_lookup[normalize_name(player_name)] = player
    
    # Create lookup for player shooting stats (dunks, layups, etc.)
    # Use normalize_name for unicode-safe matching
    player_shooting_lookup = {}
    if player_shooting_stats:
        for player in player_shooting_stats:
            player_name = player.get('athleteName', '')
            if player_name:
                player_shooting_lookup[normalize_name(player_name)] = player
    
    # Process each player from roster
    total_players = len(all_players_to_process)
    # Reserve 10% for initial setup, 10% for saving
    # Player processing gets 80% of progress (10% to 90%)
    player_progress_range = 80  # 80% of total progress for players
    player_progress_start = 10   # Start player progress at 10%
    
    # Smart historical stats handling
    # Priority: legacy mode (explicit include_historical_stats) > force_refresh > auto-detect from S3
    existing_historical_stats = None
    cached_player_names = set()

    # Determine mode
    if include_historical_stats is not None:
        # Legacy mode: explicit include_historical_stats parameter was passed
        if not include_historical_stats:
            # Legacy: include_historical_stats=False means load from S3
            if progress_callback:
                progress_callback['message'] = 'Loading historical stats from existing file...'
            existing_historical_stats = load_historical_stats_from_s3(team_name, season)
            if existing_historical_stats:
                cached_player_names = set(existing_historical_stats.keys())
                print(f"[Generator] Loaded historical stats for {len(existing_historical_stats)} players from existing S3 file")
                add_status('Historical Stats (from S3)', 'success', f'Loaded from existing file for {len(existing_historical_stats)} players')
            else:
                print(f"[Generator] No existing historical stats found in S3")
                add_status('Historical Stats (from S3)', 'skipped', 'No existing file found')
        else:
            # Legacy: include_historical_stats=True means fetch all from API
            print(f"[Generator] Legacy mode: will fetch all historical stats from API")
            add_status('Historical Stats Mode', 'pending', 'Will fetch all from API (legacy mode)')
    else:
        # New smart mode: auto-detect + selective fetch
        if force_historical_refresh:
            if progress_callback:
                progress_callback['message'] = 'Force refreshing all historical stats...'
            print(f"[Generator] Force refresh enabled - will fetch all historical stats from API")
            add_status('Historical Stats Mode', 'pending', 'Force refresh - fetching all from API')
            # existing_historical_stats stays None, will fetch all from API
        else:
            # Auto-detect: try to load from S3
            if progress_callback:
                progress_callback['message'] = 'Checking for cached historical stats...'
            existing_historical_stats = load_historical_stats_from_s3(team_name, season)
            if existing_historical_stats:
                cached_player_names = set(existing_historical_stats.keys())
                print(f"[Generator] Auto-detected cached historical stats for {len(existing_historical_stats)} players")
                add_status('Historical Stats Mode', 'success', f'Using cached data ({len(existing_historical_stats)} players). New players will be fetched.')
            else:
                print(f"[Generator] No cached historical stats found - will fetch all from API")
                add_status('Historical Stats Mode', 'pending', 'No cache found - fetching all from API (normal for first-time generation)')
    
    for idx, player_name_key in enumerate(sorted(all_players_to_process)):
        # Check for cancellation periodically (every 5 players to avoid overhead)
        if idx % 5 == 0:
            check_cancelled()

        # Get the actual player name (with proper casing) from roster for progress message
        player_roster_data_temp = roster_lookup.get(player_name_key, {})
        player_name_for_progress = player_roster_data_temp.get('name', player_name_key.title()) if player_roster_data_temp else player_name_key.title()

        if progress_callback:
            # Calculate progress based on players completed
            # For player 4 out of 15: (4/15) * 80 = 21.33%, plus 10% start = 31.33%
            players_completed = idx + 1  # 1-indexed for display
            player_progress = (players_completed / total_players) * player_progress_range
            progress_pct = int(player_progress_start + player_progress)
            progress_callback['progress'] = progress_pct
            progress_callback['message'] = f'Processing {player_name_for_progress} ({players_completed}/{total_players})...'

        # Get the actual player name (with proper casing) from roster
        player_roster_data = roster_lookup.get(player_name_key, {})

        # Get cached player data if available
        cached_player = cached_roster_lookup.get(player_name_key, {})

        # Get player name - prefer from roster, fallback to title case
        if player_roster_data:
            player_name = player_roster_data.get('name', player_name_key.title())
        else:
            # Try to find the name from the original roster data
            player_name = None
            if roster_data and len(roster_data) > 0 and 'players' in roster_data[0]:
                for p in roster_data[0]['players']:
                    if normalize_name(p.get('name', '')) == player_name_key:
                        player_name = p.get('name')
                        player_roster_data = p
                        break

            # If still not found, use title case
            if not player_name:
                player_name = player_name_key.title()
        
        # Calculate stats (will return None if no game data)
        # Filter game_data to only include games in our date range
        # The calculate_regular_season_stats function has hardcoded dates, so we filter first
        filtered_game_data = []
        start_date_obj = datetime(season-1, 11, 4)
        end_date_obj = datetime(season, 3, 16)
        
        for game in game_data:
            game_date = game.get('startDate', '')
            if game_date:
                try:
                    date_part = game_date.split('T')[0]
                    year, month, day = date_part.split('-')
                    game_date_obj = datetime(int(year), int(month), int(day))
                    if start_date_obj <= game_date_obj <= end_date_obj:
                        filtered_game_data.append(game)
                except:
                    continue
        
        stats = calculate_regular_season_stats(player_name, filtered_game_data)
        
        # If no stats (player didn't play), create empty stats structure
        if not stats:
            stats = {
                'games': 0,
                'starts': 0,
                'minutes': 0,
                'mpg': 0.0,
                'points': 0,
                'ppg': 0.0,
                'total_reb': 0,
                'rpg': 0.0,
                'assists': 0,
                'apg': 0.0,
                'turnovers': 0,
                'steals': 0,
                'spg': 0.0,
                'blocks': 0,
                'bpg': 0.0,
                'fouls': 0,
                'foulOuts': 0,
                'ejections': 0,
                'fgm': 0,
                'fga': 0,
                'fg_pct': 0.0,
                'three_pm': 0,
                'three_pa': 0,
                'three_pct': 0.0,
                'ftm': 0,
                'fta': 0,
                'ft_pct': 0.0,
                'or_reb': 0,
                'dr_reb': 0,
                'ratio': 0.0,
                'game_by_game': []
            }
        
        # Get jersey number from roster or use "N/A"
        jersey_number = "N/A"
        if player_roster_data:
            jersey_number = str(player_roster_data.get('jersey', 'N/A'))
        
        # Normalize jersey for matching
        normalized_jersey = normalize_jersey(jersey_number)
        
        # Determine if freshman - only from cache data, no calculation
        is_freshman = False
        # We'll set this based on class from cache, not calculation
        
        # Extract height
        # Handles both CBB API format (inches as int) and FoxSports format (e.g., "6'2\"")
        height_str = "N/A"
        height_value = player_roster_data.get('height')
        if height_value:
            if isinstance(height_value, int):
                # CBB API format: height in inches
                feet = height_value // 12
                inches = height_value % 12
                height_str = f"{feet}-{inches}"
            elif isinstance(height_value, str) and height_value != "N/A":
                # FoxSports format: "6'2\"" -> convert to "6-2"
                import re
                match = re.match(r"(\d+)'(\d+)\"?", height_value)
                if match:
                    height_str = f"{match.group(1)}-{match.group(2)}"
                else:
                    height_str = height_value  # Use as-is if format not recognized
        
        # Extract hometown
        hometown_str = "N/A"
        hometown = player_roster_data.get('hometown', {})
        city = hometown.get('city', '')
        state = hometown.get('state', '')
        if city and state:
            hometown_str = f"{city}, {state}"
        
        # Class year - Priority: FoxSports-only player data → FoxSports cache (by jersey) → cached roster file → "N/A"
        # NO CALCULATION - only use cached data to avoid incorrect predictions
        class_year_str = "N/A"
        class_source = None

        # For FoxSports-only players, class is directly in player_roster_data
        if player_roster_data.get('source') == 'foxsports' and player_roster_data.get('playerClass'):
            class_year_str = player_roster_data.get('playerClass')
            class_source = "foxsports_direct"

        # Try FoxSports cache by jersey (for CBB API players)
        if class_year_str == "N/A" and normalized_jersey and foxsports_team_id:
            cached_class = player_classes_by_jersey.get(normalized_jersey)
            if cached_class:
                class_year_str = cached_class
                class_source = "foxsports_cache_jersey"

        # Fallback: Try FoxSports cache by player name (handles jersey number mismatches)
        if class_year_str == "N/A" and foxsports_team_id and FOXSPORTS_CACHE_AVAILABLE:
            try:
                cached_class = cache.get_class_by_name(foxsports_team_id, player_name)
                if cached_class:
                    class_year_str = cached_class
                    class_source = "foxsports_cache_name"
                    if os.environ.get('CBB_DEBUG'):
                        print(f"  Found class via name match for {player_name}: {cached_class}")
            except Exception as e:
                if os.environ.get('CBB_DEBUG'):
                    print(f"  Warning: Name-based class lookup failed for {player_name}: {e}")

        # Fallback to cached roster file (only if FoxSports cache didn't have it)
        if class_year_str == "N/A":
            cached_year = cached_player.get('year')  # Already normalized to FR/SO/JR/SR/R-FR/etc.
            if cached_year:
                class_year_str = cached_year
                class_source = "cached_roster"

        # Log warning if we couldn't determine class from any source
        if class_year_str == "N/A":
            print(f"WARNING: No class data for {player_name} (jersey: {jersey_number})")
            print(f"  - FoxSports cache by jersey: {'skipped (no foxsports_id)' if not foxsports_team_id else f'not found for jersey {normalized_jersey}'}")
            print(f"  - FoxSports cache by name: {'skipped (no foxsports_id)' if not foxsports_team_id else 'not found'}")
            print(f"  - Cached roster lookup: {'not found' if not cached_player else 'no year field'}")
        
        # Set is_freshman based on class from cache (not calculation)
        if class_year_str and class_year_str != "N/A":
            is_freshman = class_year_str in ['FR', 'R-FR']
        
        # High School - prefer cached, fallback to API/recruiting
        high_school_str = cached_player.get('high_school') or player_roster_data.get('highSchool', 'N/A')
        if not high_school_str or high_school_str == "":
            high_school_str = "N/A"
        
        player_record = {
            'name': player_name,
            'jerseyNumber': jersey_number,
            'position': player_roster_data.get('position', 'N/A'),
            'height': height_str,
            'class': class_year_str,
            'isFreshman': is_freshman,
            'hometown': hometown_str,
            'highSchool': high_school_str,
            'seasonTotals': {
                'games': stats['games'],
                'gamesStarted': stats['starts'],
                'minutes': stats['minutes'],
                'mpg': stats['mpg'],
                'points': stats['points'],
                'ppg': stats['ppg'],
                'rebounds': stats['total_reb'],
                'rpg': stats['rpg'],
                'assists': stats['assists'],
                'apg': stats['apg'],
                'turnovers': stats['turnovers'],
                'steals': stats['steals'],
                'spg': stats['spg'],
                'blocks': stats['blocks'],
                'bpg': stats['bpg'],
                'fouls': stats['fouls'],
                'foulOuts': stats['foulOuts'],
                'ejections': stats['ejections'],
                'fieldGoals': {
                    'made': stats['fgm'],
                    'attempted': stats['fga'],
                    'percentage': stats['fg_pct']
                },
                'threePointFieldGoals': {
                    'made': stats['three_pm'],
                    'attempted': stats['three_pa'],
                    'percentage': stats['three_pct']
                },
                'freeThrows': {
                    'made': stats['ftm'],
                    'attempted': stats['fta'],
                    'percentage': stats['ft_pct']
                },
                'rebounds': {
                    'offensive': stats['or_reb'],
                    'defensive': stats['dr_reb'],
                    'total': stats['total_reb']
                },
                'assistToTurnoverRatio': stats['ratio']
            },
            'gameByGame': stats.get('game_by_game', [])
        }
        
        # Add player season stats with rankings if available
        player_season_data = player_stats_lookup.get(normalize_name(player_name))
        if player_season_data:
            player_record['seasonStatsWithRankings'] = player_season_data
        
        # Add player shooting stats (dunks, layups, jumpers, etc.)
        # Always add shootingStats field, even if player has no tracked shots (use zeros)
        player_shooting_data = player_shooting_lookup.get(normalize_name(player_name))
        if player_shooting_data:
            # Extract just the shooting breakdown (dunks, layups, etc.)
            shooting_breakdown = {
                'dunks': player_shooting_data.get('dunks', {}),
                'layups': player_shooting_data.get('layups', {}),
                'tipIns': player_shooting_data.get('tipIns', {}),
                'twoPointJumpers': player_shooting_data.get('twoPointJumpers', {}),
                'threePointJumpers': player_shooting_data.get('threePointJumpers', {}),
                'freeThrows': player_shooting_data.get('freeThrows', {}),
                'trackedShots': player_shooting_data.get('trackedShots', 0),
                'freeThrowRate': player_shooting_data.get('freeThrowRate', 0),
                'assistedPct': player_shooting_data.get('assistedPct', 0),
                'attemptsBreakdown': player_shooting_data.get('attemptsBreakdown', {})
            }
        else:
            # Player not in shooting stats API (no tracked shots) - use zeros for consistency
            shooting_breakdown = {
                'dunks': {'attempted': 0, 'made': 0, 'pct': 0, 'assisted': 0, 'assistedPct': 0},
                'layups': {'attempted': 0, 'made': 0, 'pct': 0, 'assisted': 0, 'assistedPct': 0},
                'tipIns': {'attempted': 0, 'made': 0, 'pct': 0, 'assisted': 0, 'assistedPct': 0},
                'twoPointJumpers': {'attempted': 0, 'made': 0, 'pct': 0, 'assisted': 0, 'assistedPct': 0},
                'threePointJumpers': {'attempted': 0, 'made': 0, 'pct': 0, 'assisted': 0, 'assistedPct': 0},
                'freeThrows': {'attempted': 0, 'made': 0, 'pct': 0},
                'trackedShots': 0,
                'freeThrowRate': 0,
                'assistedPct': 0,
                'attemptsBreakdown': {'dunks': 0, 'layups': 0, 'tipIns': 0, 'twoPointJumpers': 0, 'threePointJumpers': 0}
            }
        player_record['shootingStats'] = shooting_breakdown
        
        # Calculate player's conference rankings (using cached conference players)
        if conference_name:
            player_conference_rankings = calculate_player_conference_rankings_from_list(
                all_conference_players, conference_name, player_name
            )
            if player_conference_rankings:
                player_record['conferenceRankings'] = player_conference_rankings
        
        # Get player's historical season stats from previous schools
        # Smart hybrid logic: use cache when available, fetch from API only when needed
        player_key = normalize_name(player_name)
        players_completed = idx + 1  # 1-indexed for display

        if include_historical_stats is not None:
            # Legacy mode: explicit include_historical_stats parameter controls behavior
            if include_historical_stats:
                # Legacy: fetch all from API
                if progress_callback:
                    progress_callback['message'] = f'Fetching historical stats for {player_name} ({players_completed}/{total_players})...'
                historical_seasons = get_player_career_season_stats(api, player_name, team_slug)
                if historical_seasons:
                    player_record['previousSeasons'] = historical_seasons
            else:
                # Legacy: use cached data only
                if existing_historical_stats and player_key in existing_historical_stats:
                    player_record['previousSeasons'] = existing_historical_stats[player_key]
                    if progress_callback and idx == 0:
                        progress_callback['message'] = 'Using cached historical stats...'
        else:
            # New smart mode: auto-detect + selective fetch
            if force_historical_refresh:
                # Force refresh: fetch all from API
                if progress_callback:
                    progress_callback['message'] = f'Force refreshing history for {player_name} ({players_completed}/{total_players})...'
                historical_seasons = get_player_career_season_stats(api, player_name, team_slug)
                if historical_seasons:
                    player_record['previousSeasons'] = historical_seasons
            elif player_key in cached_player_names:
                # Player exists in cache: use cached data (fast path)
                player_record['previousSeasons'] = existing_historical_stats[player_key]
                if progress_callback and idx == 0:
                    progress_callback['message'] = 'Using cached historical stats...'
            else:
                # New player not in cache: fetch just this player from API
                if progress_callback:
                    progress_callback['message'] = f'Fetching history for new player {player_name} ({players_completed}/{total_players})...'
                print(f"[Generator] New player {player_name} not in cache - fetching from API")
                historical_seasons = get_player_career_season_stats(api, player_name, team_slug)
                if historical_seasons:
                    player_record['previousSeasons'] = historical_seasons
        
        team_data['players'].append(player_record)
    
    # Sort players by MPG (descending)
    team_data['players'].sort(key=lambda x: x['seasonTotals']['mpg'], reverse=True)
    
    # Add metadata
    total_api_calls = api.api_call_count if hasattr(api, 'api_call_count') else 0
    team_data['metadata'] = {
        'totalPlayers': len(team_data['players']),
        'apiCalls': total_api_calls
    }
    
    # Add AP Rankings to metadata if available
    if team_data.get('wikipedia', {}).get('apRankings'):
        ap_rankings = team_data['wikipedia']['apRankings']
        team_data['metadata']['apRankings'] = {
            'current': ap_rankings.get('current'),
            'highest': ap_rankings.get('highest')
        }
    
    print(f"[GENERATOR] Completed processing {len(team_data['players'])} players")
    print(f"[GENERATOR] Total API calls made: {total_api_calls}")
    
    # Add summary status for player historical stats
    if include_historical_stats:
        players_with_history = sum(1 for p in team_data['players'] if 'previousSeasons' in p and p['previousSeasons'])
        add_status('Player Historical Stats', 'success', f'Retrieved history for {players_with_history}/{len(team_data["players"])} players')
    else:
        # Check if we loaded any from S3
        players_with_history = sum(1 for p in team_data['players'] if 'previousSeasons' in p and p['previousSeasons'])
        if players_with_history > 0:
            add_status('Player Historical Stats', 'success', f'Loaded from existing file for {players_with_history}/{len(team_data["players"])} players')
        else:
            add_status('Player Historical Stats', 'skipped', 'Historical stats disabled and no existing file found')
    
    # Finalize data quality validation
    quality_report = None
    if quality_hub and DATA_QUALITY_AVAILABLE:
        print("[GENERATOR] Running final data quality validation...")

        # Collect final players for validation
        quality_hub.collect('players', team_data['players'])

        # Register and run remaining validators
        quality_hub.register_validator(validate_class_year_coverage)
        quality_hub.register_validator(validate_roster_size)

        # Finalize and get report
        quality_report = quality_hub.finalize()

        # Add quality summary to status
        if quality_report.has_critical:
            critical_issues = [r for r in quality_report.results if r.severity == Severity.CRITICAL]
            add_status('Data Quality', 'warning',
                      f'CRITICAL: {critical_issues[0].message if critical_issues else "Issues found"}',
                      'Review immediately')
        elif quality_report.has_errors:
            error_count = len([r for r in quality_report.results if r.severity >= Severity.ERROR])
            add_status('Data Quality', 'warning', f'{error_count} data quality errors found')
        else:
            add_status('Data Quality', 'success',
                      f'{quality_report.checks_passed}/{quality_report.checks_run} checks passed ({quality_report.pass_rate:.0f}%)')

        # Add quality report to team data
        team_data['dataQuality'] = quality_report.to_dict()

        # Add quality report to progress callback for email notifications
        if progress_callback:
            progress_callback['qualityReport'] = quality_report.to_dict()

        print(f"[GENERATOR] {quality_report.summary()}")

    if progress_callback:
        progress_callback['message'] = 'Saving JSON file...'
        progress_callback['progress'] = 95

    # Extract game dates for UI display
    game_dates = []
    if team_data.get('teamGameStats'):
        for game in team_data['teamGameStats']:
            start_date = game.get('startDate', '')
            opponent = game.get('opponent', 'Unknown')
            if start_date:
                # Parse date and format for display
                try:
                    # Parse ISO format date
                    date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    # Format as readable date
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                    game_dates.append({
                        'date': formatted_date,
                        'opponent': opponent,
                        'isHome': game.get('isHome', False),
                        'conferenceGame': game.get('conferenceGame', False)
                    })
                except:
                    # Fallback to raw date string
                    game_dates.append({
                        'date': start_date.split('T')[0] if 'T' in start_date else start_date,
                        'opponent': opponent,
                        'isHome': game.get('isHome', False),
                        'conferenceGame': game.get('conferenceGame', False)
                    })
    
    # Sort by date (most recent first)
    game_dates.sort(key=lambda x: x['date'], reverse=True)
    
    # Save to JSON file (relative to project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Validate data before writing
    validation_errors = None
    if SCHEMA_VALIDATION_AVAILABLE:
        try:
            validate_team_data(team_data)
            print("✅ Schema validation passed")
        except Exception as e:
            validation_errors = str(e)
            print(f"⚠️ Schema validation warning: {e}")

            # Log to file
            log_dir = os.path.join(project_root, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'validation_errors.log')
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"Team: {team_name}\n")
                f.write(f"Season: {season}\n")
                f.write(f"Errors:\n{validation_errors}\n")
            print(f"📝 Validation errors logged to {log_file}")
            # Continue with writing - validation is non-blocking

    output_dir = os.path.join(project_root, 'data', str(season))
    os.makedirs(output_dir, exist_ok=True)
    filename = f'{team_slug.replace(" ", "_")}_scouting_data_{season}.json'
    output_path = os.path.join(output_dir, filename)

    with open(output_path, 'w') as f:
        json.dump(team_data, f, indent=2)
    
    # Return path relative to project root for git operations
    relative_path = os.path.relpath(output_path, project_root)
    
    if progress_callback:
        progress_callback['progress'] = 100
        progress_callback['message'] = 'Complete!' if not validation_errors else 'Complete with validation warnings'
        # Add game dates to progress callback for UI display
        progress_callback['gameDates'] = game_dates
        # Add validation status
        if validation_errors:
            progress_callback['validationErrors'] = validation_errors

    return relative_path

