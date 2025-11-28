"""
Generic team data generator that works with any team.
Refactored from the team-specific generator scripts.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from cbb_api_wrapper import CollegeBasketballAPI
import json
from datetime import datetime

# Import FoxSports roster cache
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
foxsports_path = os.path.join(project_root, 'foxsports_rosters')
sys.path.insert(0, foxsports_path)
try:
    from roster_cache_reader import RosterCache
    FOXSPORTS_CACHE_AVAILABLE = True
except ImportError:
    FOXSPORTS_CACHE_AVAILABLE = False
    print("Warning: FoxSports roster cache not available")

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
                # Create lookup by player name (case-insensitive)
                cached_lookup = {}
                for player in cached_data.get('players', []):
                    player_name = player.get('name', '')
                    if player_name:
                        cached_lookup[player_name.lower()] = player
                return cached_lookup
        except Exception as e:
            print(f"Warning: Could not load cached roster: {e}")
    return {}


def generate_team_data(team_name, season, progress_callback=None):
    """
    Generate team data JSON file for any team.
    
    Args:
        team_name: Team name (e.g., "Oregon", "Wisconsin", "UCLA")
        season: Season year (e.g., 2026)
        progress_callback: Optional dict to update progress
    
    Returns:
        Path to generated JSON file
    """
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
    
    api = CollegeBasketballAPI()
    
    # Team name normalization (lowercase for API)
    team_slug = team_name.lower()
    
    # Calculate date range based on season
    start_date = f'{season-1}-11-04'
    end_date = f'{season}-03-17'
    
    if progress_callback:
        progress_callback['message'] = 'Fetching game data...'
        progress_callback['progress'] = 3
    
    # Fetch game data
    game_data = api.get_player_game_stats_by_date(start_date, end_date, team_slug)
    
    if progress_callback:
        progress_callback['message'] = 'Fetching roster data...'
        progress_callback['progress'] = 4
    
    # Fetch roster data
    roster_data = api.get_team_roster(season, team_slug)
    
    if progress_callback:
        progress_callback['message'] = 'Fetching recruiting data...'
        progress_callback['progress'] = 5
    
    # Fetch recruiting data
    recruiting_data = api.get_recruiting_players(team_name)
    
    if progress_callback:
        progress_callback['message'] = 'Fetching team game stats...'
        progress_callback['progress'] = 6
    
    # Fetch team game stats
    team_game_stats = api.get_team_game_stats(season, start_date, end_date, team_slug, "regular")
    
    if progress_callback:
        progress_callback['message'] = 'Fetching player season stats...'
        progress_callback['progress'] = 7
    
    # Fetch player season stats
    player_season_stats = api.get_player_season_stats(season, team_slug, "regular")
    
    if progress_callback:
        progress_callback['message'] = 'Fetching team season stats...'
        progress_callback['progress'] = 8
    
    # Fetch team season stats
    team_season_stats = api.get_team_season_stats(season, team_slug, "regular")
    
    if progress_callback:
        progress_callback['message'] = 'Calculating conference rankings...'
        progress_callback['progress'] = 9
    
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
            conference_rankings = calculate_conference_rankings(api, team_name, conference_name or "Unknown")
        else:
            # For other seasons, create empty rankings for now
            conference_rankings = {'conference': {}, 'd1': {}}
    except Exception as e:
        print(f"Warning: Could not calculate rankings: {e}")
        conference_rankings = {'conference': {}, 'd1': {}}
    
    if progress_callback:
        progress_callback['message'] = 'Fetching all player stats for rankings...'
        progress_callback['progress'] = 10
    
    # Fetch all conference players for individual player rankings
    all_conference_players = api.get_player_season_stats(season, season_type='regular')
    
    # Get CBB API teamId for FoxSports cache lookup
    cbb_team_id = None
    if team_season_stats and len(team_season_stats) > 0:
        cbb_team_id = team_season_stats[0].get('teamId')
        print(f"DEBUG: Team '{team_name}' - CBB API teamId: {cbb_team_id}")
    
    # Load FoxSports roster cache for player classes
    foxsports_team_id = None
    player_classes_by_jersey = {}
    
    if FOXSPORTS_CACHE_AVAILABLE and cbb_team_id:
        try:
            # Load CBB → FoxSports mapping
            mapping_path = os.path.join(foxsports_path, 'cbb_to_foxsports_team_mapping.json')
            if not os.path.exists(mapping_path):
                print(f"Warning: FoxSports mapping file not found at: {mapping_path}")
                print(f"  Project root: {project_root}")
                print(f"  FoxSports path: {foxsports_path}")
            else:
                with open(mapping_path, 'r') as f:
                    cbb_to_fox_mapping = json.load(f)
                
                # Map CBB ID to FoxSports ID
                cbb_id_str = str(cbb_team_id)
                print(f"DEBUG: Looking up CBB ID '{cbb_id_str}' in mapping...")
                # Check direct mapping first
                if cbb_id_str in cbb_to_fox_mapping:
                    foxsports_team_id = cbb_to_fox_mapping[cbb_id_str]
                    print(f"DEBUG: Found direct mapping: {cbb_id_str} -> {foxsports_team_id}")
                # Check mismatches
                elif 'MISMATCHES' in cbb_to_fox_mapping and cbb_id_str in cbb_to_fox_mapping['MISMATCHES']:
                    foxsports_team_id = cbb_to_fox_mapping['MISMATCHES'][cbb_id_str]
                    print(f"DEBUG: Found mismatch mapping: {cbb_id_str} -> {foxsports_team_id}")
                else:
                    print(f"DEBUG: No mapping found for CBB ID '{cbb_id_str}'")
                
                # Get player classes from FoxSports cache
                if foxsports_team_id:
                    cache_dir = os.path.join(foxsports_path, 'rosters_cache')
                    if not os.path.exists(cache_dir):
                        print(f"Warning: FoxSports cache directory not found at: {cache_dir}")
                    else:
                        cache = RosterCache(cache_dir=cache_dir)
                        cached_players = cache.get_player_classes(foxsports_team_id)
                        
                        if cached_players:
                            # Create lookup by normalized jersey number
                            for player in cached_players:
                                jersey = normalize_jersey(player.get('jersey'))
                                if jersey:
                                    player_classes_by_jersey[jersey] = player.get('class')
                            print(f"Loaded {len(player_classes_by_jersey)} players from FoxSports cache for team {foxsports_team_id}")
                        else:
                            print(f"Warning: No players found in FoxSports cache for team {foxsports_team_id}")
                else:
                    print(f"Warning: No FoxSports team ID found for CBB team ID {cbb_team_id}")
        except Exception as e:
            import traceback
            print(f"Error loading FoxSports roster cache: {e}")
            print(f"Traceback: {traceback.format_exc()}")
    
    # Load cached roster if available (for better class/year and high school data)
    cached_roster_lookup = load_cached_roster(team_name, season)
    
    # Create lookups
    roster_lookup = {}
    if roster_data and len(roster_data) > 0 and 'players' in roster_data[0]:
        for player in roster_data[0]['players']:
            player_name = player.get('name', '')
            roster_lookup[player_name.lower()] = player
    
    recruiting_lookup = {}
    for recruit in recruiting_data:
        player_name = recruit.get('name', '')
        recruiting_lookup[player_name.lower()] = recruit
    
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
    
    # Get all players from roster - this is the SOURCE OF TRUTH
    # The roster endpoint determines who is on the team
    # Game data is only used for stats, not for discovering players
    all_roster_players = set()
    if roster_data and len(roster_data) > 0 and 'players' in roster_data[0]:
        for player in roster_data[0]['players']:
            player_name = player.get('name', '')
            if player_name:
                all_roster_players.add(player_name.lower())
    
    # Use ONLY roster players - game data is only for stats, not roster discovery
    # This ensures we only process players from the target team, not opponents
    all_players_to_process = all_roster_players
    
    if progress_callback:
        progress_callback['message'] = f'Processing {len(all_players_to_process)} players...'
        progress_callback['progress'] = 10  # Start of player processing
    
    # Get mascot from cached roster if available
    mascot = None
    if cached_roster_lookup:
        # Try to get mascot from first player's roster data structure
        # Actually, we need to load the full roster file to get mascot
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        team_slug = team_name.lower().replace(' ', '_')
        roster_path = os.path.join(project_root, 'data', 'rosters', str(season), f'{team_slug}_roster.json')
        if os.path.exists(roster_path):
            try:
                with open(roster_path, 'r') as f:
                    roster_file_data = json.load(f)
                    mascot = roster_file_data.get('mascot')
            except:
                pass
    
    # Build consolidated data structure
    team_data = {
        'team': team_name,
        'season': f'{season-1}-{str(season)[2:]}',
        'seasonType': 'Regular',
        'dataGenerated': datetime.now().isoformat(),
        'players': []
    }
    
    # Add mascot if available
    if mascot:
        team_data['mascot'] = mascot
    
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
    
    # Create lookup for player season stats (for rankings)
    player_stats_lookup = {}
    if player_season_stats:
        for player in player_season_stats:
            player_name = player.get('name', '')
            if player_name:
                player_stats_lookup[player_name.lower()] = player
    
    # Process each player from roster
    total_players = len(all_players_to_process)
    # Reserve 10% for initial setup, 10% for saving
    # Player processing gets 80% of progress (10% to 90%)
    player_progress_range = 80  # 80% of total progress for players
    player_progress_start = 10   # Start player progress at 10%
    
    for idx, player_name_lower in enumerate(sorted(all_players_to_process)):
        # Get the actual player name (with proper casing) from roster for progress message
        player_roster_data_temp = roster_lookup.get(player_name_lower, {})
        player_name_for_progress = player_roster_data_temp.get('name', player_name_lower.title()) if player_roster_data_temp else player_name_lower.title()
        
        if progress_callback:
            # Calculate progress based on players completed
            # For player 4 out of 15: (4/15) * 80 = 21.33%, plus 10% start = 31.33%
            players_completed = idx + 1  # 1-indexed for display
            player_progress = (players_completed / total_players) * player_progress_range
            progress_pct = int(player_progress_start + player_progress)
            progress_callback['progress'] = progress_pct
            progress_callback['message'] = f'Processing {player_name_for_progress} ({players_completed}/{total_players})...'
        
        # Get the actual player name (with proper casing) from roster
        player_roster_data = roster_lookup.get(player_name_lower, {})
        
        # Get cached player data if available
        cached_player = cached_roster_lookup.get(player_name_lower, {})
        
        # Get player name - prefer from roster, fallback to title case
        if player_roster_data:
            player_name = player_roster_data.get('name', player_name_lower.title())
        else:
            # Try to find the name from the original roster data
            player_name = None
            if roster_data and len(roster_data) > 0 and 'players' in roster_data[0]:
                for p in roster_data[0]['players']:
                    if p.get('name', '').lower() == player_name_lower:
                        player_name = p.get('name')
                        player_roster_data = p
                        break
            
            # If still not found, use title case
            if not player_name:
                player_name = player_name_lower.title()
        
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
        height_str = "N/A"
        height_inches = player_roster_data.get('height')
        if height_inches:
            feet = height_inches // 12
            inches = height_inches % 12
            height_str = f"{feet}-{inches}"
        
        # Extract hometown
        hometown_str = "N/A"
        hometown = player_roster_data.get('hometown', {})
        city = hometown.get('city', '')
        state = hometown.get('state', '')
        if city and state:
            hometown_str = f"{city}, {state}"
        
        # Class year - Priority: FoxSports cache (by jersey) → cached roster file → "N/A"
        # NO CALCULATION - only use cached data to avoid incorrect predictions
        class_year_str = "N/A"
        
        # Try FoxSports cache first (by normalized jersey number)
        if normalized_jersey and foxsports_team_id:
            cached_class = player_classes_by_jersey.get(normalized_jersey)
            if cached_class:
                class_year_str = cached_class
        
        # Fallback to cached roster file (only if FoxSports cache didn't have it)
        if class_year_str == "N/A":
            cached_year = cached_player.get('year')  # Already normalized to FR/SO/JR/SR/R-FR/etc.
            if cached_year:
                class_year_str = cached_year
        
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
        player_season_data = player_stats_lookup.get(player_name.lower())
        if player_season_data:
            player_record['seasonStatsWithRankings'] = player_season_data
        
        # Calculate player's conference rankings (using cached conference players)
        if conference_name:
            player_conference_rankings = calculate_player_conference_rankings_from_list(
                all_conference_players, conference_name, player_name
            )
            if player_conference_rankings:
                player_record['conferenceRankings'] = player_conference_rankings
        
        # Get player's historical season stats from previous schools
        # This can be slow as it makes multiple API calls per player (3 seasons × all players)
        if progress_callback:
            players_completed = idx + 1  # 1-indexed for display
            # Update progress message but keep same progress percentage (updated at start of loop)
            progress_callback['message'] = f'Fetching historical stats for {player_name} ({players_completed}/{total_players})...'
        historical_seasons = get_player_career_season_stats(api, player_name, team_slug)
        if historical_seasons:
            player_record['previousSeasons'] = historical_seasons
        
        team_data['players'].append(player_record)
    
    # Sort players by MPG (descending)
    team_data['players'].sort(key=lambda x: x['seasonTotals']['mpg'], reverse=True)
    
    # Add metadata
    team_data['metadata'] = {
        'totalPlayers': len(team_data['players']),
        'apiCalls': api.api_call_count if hasattr(api, 'api_call_count') else 0
    }
    
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
        progress_callback['message'] = 'Complete!'
        # Add game dates to progress callback for UI display
        progress_callback['gameDates'] = game_dates
    
    return relative_path

