#!/usr/bin/env python3
"""
KenPom API client for fetching team data using the official API.
Replaces the web scraping approach with API calls.
"""
import requests
import json
import os
from typing import Dict, List, Optional, Any

# API Configuration
API_BASE_URL = "https://kenpom.com/api.php"
API_KEY_FILE = os.path.join(os.path.dirname(__file__), '..', 'kp_api_creds.txt')


def load_api_key():
    """
    Load KenPom API key from environment variable or file.
    
    Priority:
    1. Environment variable (KENPOM_API_KEY) - for production
    2. API key file (kp_api_creds.txt) - for local development
    
    Returns:
        str: API key
    """
    # First, try environment variable (for production)
    api_key = os.environ.get('KENPOM_API_KEY')
    if api_key:
        api_key = api_key.strip()
        if api_key:
            print("[KENPOM API] Using API key from environment variable")
            return api_key
    
    # Fallback to file (for local development)
    if os.path.exists(API_KEY_FILE):
        try:
            with open(API_KEY_FILE, 'r') as f:
                for line in f:
                    if line.startswith('api_key='):
                        api_key = line.split('=', 1)[1].strip()
                        print("[KENPOM API] Using API key from file")
                        return api_key
        except Exception as e:
            print(f"[KENPOM API] Warning: Could not read API key file: {e}")
    
    raise Exception("KenPom API key not found. Set KENPOM_API_KEY environment variable or create kp_api_creds.txt file.")


def make_api_request(endpoint: str, params: Dict[str, Any] = None) -> Dict:
    """
    Make a request to the KenPom API.
    
    Args:
        endpoint: API endpoint name (e.g., 'ratings', 'four-factors')
        params: Query parameters
    
    Returns:
        dict: API response data
    """
    api_key = load_api_key()
    
    if params is None:
        params = {}
    
    params['endpoint'] = endpoint
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(API_BASE_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("KenPom API authentication failed. Check your API key.")
        elif e.response.status_code == 403:
            raise Exception("KenPom API access forbidden. Check your API key permissions.")
        else:
            raise Exception(f"KenPom API request failed: HTTP {e.response.status_code} - {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"KenPom API request failed: {e}")


def get_team_id(team_name: str, season: int = 2026) -> Optional[int]:
    """
    Look up team ID from team name.
    
    Args:
        team_name: Team name (e.g., "UCLA", "Michigan State")
        season: Season year (ending year, e.g., 2026 for 2025-26 season)
    
    Returns:
        int: Team ID, or None if not found
    """
    try:
        data = make_api_request('teams', {'y': season})
        
        if not isinstance(data, list):
            return None
        
        # Normalize team name for matching
        team_name_lower = team_name.lower().strip()
        
        # Try exact match first
        for team in data:
            if team.get('TeamName', '').lower() == team_name_lower:
                return team.get('TeamID')
        
        # Try partial match
        for team in data:
            team_name_api = team.get('TeamName', '').lower()
            if team_name_lower in team_name_api or team_name_api in team_name_lower:
                return team.get('TeamID')
        
        # Try common name variations
        name_variations = {
            'michigan state': 'Michigan St',
            'ohio state': 'Ohio St',
            'penn state': 'Penn St',
            'iowa state': 'Iowa St',
            'washington state': 'Washington St',
            'oregon state': 'Oregon St',
            'kansas state': 'Kansas St',
            'oklahoma state': 'Oklahoma St',
            'florida state': 'Florida St',
            'nc state': 'NC State',
            'north carolina state': 'NC State',
            'usc': 'Southern California',
            'southern california': 'Southern California',
        }
        
        if team_name_lower in name_variations:
            normalized = name_variations[team_name_lower]
            for team in data:
                if team.get('TeamName', '').lower() == normalized.lower():
                    return team.get('TeamID')
        
        return None
    except Exception as e:
        print(f"[KENPOM API] Warning: Failed to lookup team ID for {team_name}: {e}")
        return None


def calculate_d1_average(data_list: List[Dict], field_name: str) -> Optional[float]:
    """
    Calculate D-1 average for a given field from a list of team data.
    
    Args:
        data_list: List of team data dictionaries
        field_name: Field name to calculate average for
    
    Returns:
        float: Average value, or None if calculation fails
    """
    if not data_list:
        return None
    
    values = []
    for item in data_list:
        value = item.get(field_name)
        if value is not None and isinstance(value, (int, float)):
            values.append(value)
    
    if values:
        return sum(values) / len(values)
    return None


def get_kenpom_team_data(team_slug: str, season: int = 2026) -> Dict:
    """
    Fetch team data from KenPom API and transform it to match the original scraping format.
    
    Args:
        team_slug: Team identifier (e.g., "UCLA", "Michigan State", "oregon")
        season: Season year (ending year, e.g., 2026 for 2025-26 season)
    
    Returns:
        dict: Team data in the same format as the scraping version:
            - team: Original team slug
            - team_name: Team name from API
            - url: URL (for compatibility)
            - data: Extracted data including report_table_structured
    """
    print(f"[KENPOM API] Fetching data for {team_slug} (season {season})...")
    
    # Look up team ID
    team_id = get_team_id(team_slug, season)
    if not team_id:
        raise Exception(f"Team '{team_slug}' not found in KenPom API for season {season}")
    
    print(f"[KENPOM API] Found team ID: {team_id}")
    
    # Fetch data from all endpoints
    structured_report = {}
    
    # 1. Ratings endpoint (Adj Efficiency, Adj Tempo, SOS, Avg Poss Length)
    try:
        print("[KENPOM API] Fetching ratings data...")
        ratings_data = make_api_request('ratings', {'team_id': team_id, 'y': season})
        
        if isinstance(ratings_data, list) and len(ratings_data) > 0:
            ratings = ratings_data[0]
            team_name = ratings.get('TeamName', team_slug)
            
            # Adj. Efficiency
            structured_report['Adj. Efficiency'] = {
                'offense': str(ratings.get('AdjOE', '')),
                'offense_ranking': ratings.get('RankAdjOE'),
                'defense': str(ratings.get('AdjDE', '')),
                'defense_ranking': ratings.get('RankAdjDE'),
                'd1_avg': None  # Will calculate below
            }
            
            # Adj. Tempo
            structured_report['Adj. Tempo'] = {
                'combined': str(ratings.get('AdjTempo', '')),
                'ranking': ratings.get('RankAdjTempo'),
                'd1_avg': None  # Will calculate below
            }
            
            # Avg. Poss. Length
            structured_report['Avg. Poss. Length'] = {
                'offense': str(ratings.get('APL_Off', '')),
                'offense_ranking': ratings.get('RankAPL_Off'),
                'defense': str(ratings.get('APL_Def', '')),
                'defense_ranking': ratings.get('RankAPL_Def'),
                'd1_avg': None  # Will calculate below
            }
            
            # Strength of Schedule - store as separate categories to match original format
            structured_report['Strength of Schedule'] = {
                'overall': str(ratings.get('SOS', '')),
                'overall_ranking': ratings.get('RankSOS'),
                'non_conference': str(ratings.get('NCSOS', '')),
                'non_conference_ranking': ratings.get('RankNCSOS'),
            }
            
            # Strength of Schedule Components (separate offense/defense)
            structured_report['Strength of Schedule Components'] = {
                'overall': str(ratings.get('SOS', '')),
                'overall_ranking': ratings.get('RankSOS'),
                'offense': str(ratings.get('SOSO', '')),
                'offense_ranking': ratings.get('RankSOSO'),
                'defense': str(ratings.get('SOSD', '')),
                'defense_ranking': ratings.get('RankSOSD'),
            }
            
            print(f"[KENPOM API] Team: {team_name}")
        else:
            raise Exception("No ratings data returned")
    except Exception as e:
        print(f"[KENPOM API] Warning: Failed to fetch ratings: {e}")
        raise
    
    # 2. Four Factors endpoint
    try:
        print("[KENPOM API] Fetching four factors data...")
        four_factors_data = make_api_request('four-factors', {'team_id': team_id, 'y': season})
        
        if isinstance(four_factors_data, list) and len(four_factors_data) > 0:
            ff = four_factors_data[0]
            
            # Effective FG%
            structured_report['Effective FG%'] = {
                'offense': f"{ff.get('eFG_Pct', 0):.1f}%",
                'offense_ranking': ff.get('RankeFG_Pct'),
                'defense': f"{ff.get('DeFG_Pct', 0):.1f}%",
                'defense_ranking': ff.get('RankDeFG_Pct'),
                'd1_avg': None
            }
            
            # Turnover %
            structured_report['Turnover %'] = {
                'offense': f"{ff.get('TO_Pct', 0):.1f}%",
                'offense_ranking': ff.get('RankTO_Pct'),
                'defense': f"{ff.get('DTO_Pct', 0):.1f}%",
                'defense_ranking': ff.get('RankDTO_Pct'),
                'd1_avg': None
            }
            
            # Off. Reb. %
            structured_report['Off. Reb. %'] = {
                'offense': f"{ff.get('OR_Pct', 0):.1f}%",
                'offense_ranking': ff.get('RankOR_Pct'),
                'defense': f"{ff.get('DOR_Pct', 0):.1f}%",
                'defense_ranking': ff.get('RankDOR_Pct'),
                'd1_avg': None
            }
            
            # FTA/FGA
            structured_report['FTA/FGA'] = {
                'offense': f"{ff.get('FT_Rate', 0):.1f}",
                'offense_ranking': ff.get('RankFT_Rate'),
                'defense': f"{ff.get('DFT_Rate', 0):.1f}",
                'defense_ranking': ff.get('RankDFT_Rate'),
                'd1_avg': None
            }
    except Exception as e:
        print(f"[KENPOM API] Warning: Failed to fetch four factors: {e}")
    
    # 3. Miscellaneous Stats endpoint
    try:
        print("[KENPOM API] Fetching miscellaneous stats...")
        misc_data = make_api_request('misc-stats', {'team_id': team_id, 'y': season})
        
        if isinstance(misc_data, list) and len(misc_data) > 0:
            misc = misc_data[0]
            
            # 3P%
            structured_report['3P%'] = {
                'offense': f"{misc.get('FG3Pct', 0):.1f}%",
                'offense_ranking': misc.get('RankFG3Pct'),
                'defense': f"{misc.get('OppFG3Pct', 0):.1f}%",
                'defense_ranking': misc.get('RankOppFG3Pct'),
                'd1_avg': None
            }
            
            # 2P%
            structured_report['2P%'] = {
                'offense': f"{misc.get('FG2Pct', 0):.1f}%",
                'offense_ranking': misc.get('RankFG2Pct'),
                'defense': f"{misc.get('OppFG2Pct', 0):.1f}%",
                'defense_ranking': misc.get('RankOppFG2Pct'),
                'd1_avg': None
            }
            
            # FT%
            structured_report['FT%'] = {
                'offense': f"{misc.get('FTPct', 0):.1f}%",
                'offense_ranking': misc.get('RankFTPct'),
                'defense': f"{misc.get('OppFTPct', 0):.1f}%",
                'defense_ranking': misc.get('RankOppFTPct'),
                'd1_avg': None
            }
            
            # Block%
            structured_report['Block%'] = {
                'offense': f"{misc.get('BlockPct', 0):.1f}%",
                'offense_ranking': misc.get('RankBlockPct'),
                'defense': f"{misc.get('OppBlockPct', 0):.1f}%",
                'defense_ranking': misc.get('RankOppBlockPct'),
                'd1_avg': None
            }
            
            # Steal%
            structured_report['Steal%'] = {
                'offense': f"{misc.get('StlRate', 0):.1f}%",
                'offense_ranking': misc.get('RankStlRate'),
                'defense': f"{misc.get('OppStlRate', 0):.1f}%",
                'defense_ranking': misc.get('RankOppStlRate'),
                'd1_avg': None
            }
            
            # Non-Stl TO%
            structured_report['Non-Stl TO%'] = {
                'offense': f"{misc.get('NSTRate', 0):.1f}%",
                'offense_ranking': misc.get('RankNSTRate'),
                'defense': f"{misc.get('OppNSTRate', 0):.1f}%",
                'defense_ranking': misc.get('RankOppNSTRate'),
                'd1_avg': None
            }
            
            # 3PA/FGA (Style Component)
            structured_report['3PA/FGA'] = {
                'offense': f"{misc.get('F3GRate', 0):.1f}%",
                'offense_ranking': misc.get('RankF3GRate'),
                'defense': f"{misc.get('OppF3GRate', 0):.1f}%",
                'defense_ranking': misc.get('RankOppF3GRate'),
                'd1_avg': None
            }
            
            # A/FGM (Style Component)
            structured_report['A/FGM'] = {
                'offense': f"{misc.get('ARate', 0):.1f}%",
                'offense_ranking': misc.get('RankARate'),
                'defense': f"{misc.get('OppARate', 0):.1f}%",
                'defense_ranking': misc.get('RankOppARate'),
                'd1_avg': None
            }
    except Exception as e:
        print(f"[KENPOM API] Warning: Failed to fetch miscellaneous stats: {e}")
    
    # 4. Point Distribution endpoint
    try:
        print("[KENPOM API] Fetching point distribution data...")
        pointdist_data = make_api_request('pointdist', {'team_id': team_id, 'y': season})
        
        if isinstance(pointdist_data, list) and len(pointdist_data) > 0:
            pd = pointdist_data[0]
            
            # 3-Pointers
            structured_report['3-Pointers'] = {
                'offense': f"{pd.get('OffFg3', 0):.1f}%",
                'offense_ranking': pd.get('RankOffFg3'),
                'defense': f"{pd.get('DefFg3', 0):.1f}%",
                'defense_ranking': pd.get('RankDefFg3'),
                'd1_avg': None
            }
            
            # 2-Pointers
            structured_report['2-Pointers'] = {
                'offense': f"{pd.get('OffFg2', 0):.1f}%",
                'offense_ranking': pd.get('RankOffFg2'),
                'defense': f"{pd.get('DefFg2', 0):.1f}%",
                'defense_ranking': pd.get('RankDefFg2'),
                'd1_avg': None
            }
            
            # Free Throws
            structured_report['Free Throws'] = {
                'offense': f"{pd.get('OffFt', 0):.1f}%",
                'offense_ranking': pd.get('RankOffFt'),
                'defense': f"{pd.get('DefFt', 0):.1f}%",
                'defense_ranking': pd.get('RankDefFt'),
                'd1_avg': None
            }
    except Exception as e:
        print(f"[KENPOM API] Warning: Failed to fetch point distribution: {e}")
    
    # 5. Height endpoint (Personnel stats)
    try:
        print("[KENPOM API] Fetching height/personnel data...")
        height_data = make_api_request('height', {'team_id': team_id, 'y': season})
        
        if isinstance(height_data, list) and len(height_data) > 0:
            h = height_data[0]
            
            # Bench Minutes (already stored as percentage, e.g., 34.95 = 34.95%)
            bench = h.get('Bench', 0)
            if bench:
                structured_report['Bench Minutes'] = {
                    'value': f"{bench:.1f}%",
                    'ranking': h.get('BenchRank'),
                    'd1_avg': None
                }
            
            # D-1 Experience
            structured_report['D-1 Experience'] = {
                'value': f"{h.get('Exp', 0):.2f} yrs",
                'ranking': h.get('ExpRank'),
                'd1_avg': None
            }
            
            # Minutes Continuity (stored as decimal, e.g., 0.401 = 40.1%)
            continuity = h.get('Continuity', 0)
            if continuity:
                continuity_pct = continuity * 100  # Convert to percentage
                structured_report['Minutes Continuity'] = {
                    'value': f"{continuity_pct:.1f}%",
                    'ranking': h.get('RankContinuity'),
                    'd1_avg': None
                }
            
            # Average Height
            avg_height = h.get('AvgHgt', 0)
            if avg_height:
                # Convert inches to feet and inches
                feet = int(avg_height // 12)
                inches = int(avg_height % 12)
                structured_report['Average Height'] = {
                    'value': f'{feet}\'{inches}"',
                    'ranking': h.get('AvgHgtRank'),
                    'd1_avg': None
                }
    except Exception as e:
        print(f"[KENPOM API] Warning: Failed to fetch height/personnel data: {e}")
    
    # Calculate D-1 averages for key metrics (fetch all teams data)
    try:
        print("[KENPOM API] Calculating D-1 averages...")
        all_ratings = make_api_request('ratings', {'y': season})
        
        if isinstance(all_ratings, list) and len(all_ratings) > 0:
            # Calculate averages
            d1_adj_oe_avg = calculate_d1_average(all_ratings, 'AdjOE')
            d1_adj_de_avg = calculate_d1_average(all_ratings, 'AdjDE')
            d1_adj_tempo_avg = calculate_d1_average(all_ratings, 'AdjTempo')
            d1_apl_off_avg = calculate_d1_average(all_ratings, 'APL_Off')
            d1_apl_def_avg = calculate_d1_average(all_ratings, 'APL_Def')
            
            # Update structured report with D-1 averages
            if 'Adj. Efficiency' in structured_report:
                # For Adj Efficiency, D-1 avg is typically the average of all teams' AdjOE
                # But we can also show it as the midpoint between typical offense and defense
                if d1_adj_oe_avg:
                    # Use AdjOE average as the D-1 avg (this is what KenPom typically shows)
                    structured_report['Adj. Efficiency']['d1_avg'] = f"{d1_adj_oe_avg:.1f}"
            
            if 'Adj. Tempo' in structured_report and d1_adj_tempo_avg:
                structured_report['Adj. Tempo']['d1_avg'] = f"{d1_adj_tempo_avg:.1f}"
            
            if 'Avg. Poss. Length' in structured_report:
                if d1_apl_off_avg:
                    structured_report['Avg. Poss. Length']['d1_avg'] = f"{d1_apl_off_avg:.1f}"
    except Exception as e:
        print(f"[KENPOM API] Warning: Failed to calculate D-1 averages: {e}")
    
    # Build response in same format as scraping version
    return {
        'team': team_slug,
        'team_name': team_name if 'team_name' in locals() else team_slug,
        'url': f"https://kenpom.com/team.php?team={team_slug}",  # For compatibility
        'data': {
            'team_name': team_name if 'team_name' in locals() else team_slug,
            'url': f"https://kenpom.com/team.php?team={team_slug}",
            'report_table_structured': structured_report
        }
    }

