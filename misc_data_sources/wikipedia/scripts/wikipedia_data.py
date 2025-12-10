#!/usr/bin/env python3
"""
Script to extract infobox data from Wikipedia pages for college basketball teams.
Uses MediaWiki API to access template parameters from wikitext (not HTML parsing).
"""
import requests
import mwparserfromhell
import json
import re
from typing import Dict, Any, Optional, List


# MediaWiki API endpoint for English Wikipedia
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"


def get_wikitext(page_title: str) -> Optional[str]:
    """
    Fetch the wikitext content of a Wikipedia page using the MediaWiki API.
    
    Args:
        page_title: The title of the Wikipedia page (e.g., "UCLA_Bruins_men's_basketball")
    
    Returns:
        The wikitext content of the page, or None if the page doesn't exist
    """
    params = {
        'action': 'query',
        'format': 'json',
        'titles': page_title,
        'prop': 'revisions',
        'rvprop': 'content',
        'rvslots': 'main',
        'formatversion': '2'
    }
    
    # Wikipedia requires a User-Agent header
    headers = {
        'User-Agent': 'CollegeBasketballDataBot/1.0 (https://github.com/yourusername/cbbd; contact@example.com)'
    }
    
    try:
        response = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get('query', {}).get('pages', [])
        if not pages or 'missing' in pages[0]:
            return None
        
        revisions = pages[0].get('revisions', [])
        if not revisions:
            return None
        
        return revisions[0].get('slots', {}).get('main', {}).get('content', '')
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch Wikipedia page '{page_title}': {e}")


def extract_infobox_template(wikitext: str) -> Optional[mwparserfromhell.nodes.Template]:
    """
    Extract the infobox template from wikitext.
    Looks for templates like {{Infobox college basketball team}} or similar.
    
    Args:
        wikitext: The wikitext content of the page
    
    Returns:
        The infobox template node, or None if not found
    """
    wikicode = mwparserfromhell.parse(wikitext)
    
    # Look for infobox templates
    # Common names: "Infobox college basketball team", "Infobox CBB Team", etc.
    for template in wikicode.filter_templates():
        template_name = str(template.name).strip().lower()
        # Check for infobox with basketball or CBB (College Basketball)
        if 'infobox' in template_name and ('basketball' in template_name or 'cbb' in template_name):
            return template
        # Also check for infobox that might be at the start of the page (common pattern)
        # Some pages use "Infobox college basketball team season" or just "Infobox"
        if template_name.startswith('infobox') and len(template.params) > 5:
            # Likely an infobox if it has many parameters
            return template
    
    return None


def safe_get_template_param(template: mwparserfromhell.nodes.Template, param_name: str):
    """
    Safely get a template parameter, returning None if it doesn't exist.
    
    Args:
        template: The template node
        param_name: Name of the parameter to get
    
    Returns:
        The parameter node, or None if it doesn't exist
    """
    try:
        return template.get(param_name)
    except ValueError:
        return None


def clean_template_value(value: str) -> str:
    """
    Clean a template parameter value by removing wikitext markup.
    
    Args:
        value: Raw template parameter value
    
    Returns:
        Cleaned string value
    """
    if not value:
        return ""
    
    # Convert to string and strip
    value = str(value).strip()
    
    # Remove wikitext template calls like {{Winning percentage|...}}
    # This is a simple approach - just remove the template syntax
    value = re.sub(r'\{\{[^}]+\}\}', '', value)
    
    # Remove wikitext links: [[Link|Display]] -> Display, [[Link]] -> Link
    value = re.sub(r'\[\[([^\]]+)\]\]', lambda m: m.group(1).split('|')[-1], value)
    
    # Remove HTML tags
    value = re.sub(r'<[^>]+>', '', value)
    
    # Remove ref tags: <ref>...</ref>
    value = re.sub(r'<ref[^>]*>.*?</ref>', '', value, flags=re.DOTALL)
    
    # Remove extra whitespace
    value = re.sub(r'\s+', ' ', value).strip()
    
    return value


def extract_championships(template: mwparserfromhell.nodes.Template) -> Dict[str, Any]:
    """
    Extract championship information from the infobox template.
    
    Args:
        template: The infobox template node
    
    Returns:
        Dictionary with championship data
    """
    championships = {
        'ncaa_tournament': [],
        'ncaa_runner_up': [],
        'conference_tournament': [],
        'regular_season': [],
        'ncaa_final_four': [],
        'ncaa_elite_eight': [],
        'ncaa_sweet_sixteen': []
    }
    
    # Common parameter names for championships (including Wikipedia's actual parameter names)
    param_mappings = {
        'ncaa_tournament': ['NCAAchampion', 'ncaa', 'ncaa_championships', 'ncaa_tournament_championships'],
        'ncaa_runner_up': ['NCAArunnerup', 'ncaa_runner_up', 'ncaa_runnerup'],
        'conference_tournament': ['conference_tournament', 'conf_tournament', 'conference_tournament_championships'],
        'regular_season': ['conference_season', 'conference', 'conference_championships', 'regular_season_championships'],
        'ncaa_final_four': ['NCAAfinalfour', 'final_four', 'ncaa_final_four'],
        'ncaa_elite_eight': ['NCAAeliteeight', 'elite_eight', 'ncaa_elite_eight'],
        'ncaa_sweet_sixteen': ['NCAAsweetsixteen', 'sweet_sixteen', 'ncaa_sweet_sixteen']
    }
    
    for key, param_names in param_mappings.items():
        for param_name in param_names:
            param = safe_get_template_param(template, param_name)
            if param:
                value = clean_template_value(param.value)
                if value:
                    # Try to extract years from the value (full 4-digit years)
                    years = re.findall(r'\b(19\d{2}|20\d{2})\b', value)
                    if years:
                        championships[key] = sorted(set(years), reverse=True)
                    elif value.lower() not in ['none', 'n/a', '']:
                        championships[key] = value
                    break
    
    return championships


def extract_tournament_appearances(template: mwparserfromhell.nodes.Template, championships: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract tournament appearance information.
    Counts the number of years in comma-separated lists and extracts all appearance years.
    
    Args:
        template: The infobox template node
        championships: Dictionary with championship years (for extracting all years)
    
    Returns:
        Dictionary with tournament appearance data including all appearance years
    """
    appearances = {
        'ncaa_tournament': None,
        'ncaa_tournament_years': [],
        'final_four': None,
        'final_four_years': [],
        'elite_eight': None,
        'elite_eight_years': [],
        'sweet_sixteen': None,
        'sweet_sixteen_years': []
    }
    
    param_mappings = {
        'ncaa_tournament': ['NCAAtourneys', 'ncaa_tournament_appearances', 'ncaa_appearances', 'ncaa_tournament'],
        'final_four': ['NCAAfinalfour', 'final_four_appearances', 'final_four'],
        'elite_eight': ['NCAAeliteeight', 'elite_eight_appearances', 'elite_eight'],
        'sweet_sixteen': ['NCAAsweetsixteen', 'sweet_sixteen_appearances', 'sweet_sixteen']
    }
    
    for key, param_names in param_mappings.items():
        for param_name in param_names:
            param = safe_get_template_param(template, param_name)
            if param:
                value = clean_template_value(param.value)
                if value:
                    # Extract years in comma-separated list (full 4-digit years)
                    years = re.findall(r'\b(19\d{2}|20\d{2})\b', value)
                    if years:
                        # Convert to integers and sort (most recent first)
                        year_ints = sorted([int(y) for y in set(years)], reverse=True)
                        appearances[key] = len(year_ints)
                        
                        # Store all years (not just recent)
                        all_years = [str(y) for y in year_ints]
                        if key == 'ncaa_tournament':
                            appearances['ncaa_tournament_years'] = all_years
                        elif key == 'final_four':
                            appearances['final_four_years'] = all_years
                        elif key == 'elite_eight':
                            appearances['elite_eight_years'] = all_years
                        elif key == 'sweet_sixteen':
                            appearances['sweet_sixteen_years'] = all_years
                    else:
                        # Try to extract number if it's just a number
                        numbers = re.findall(r'^\d+$', value.strip())
                        if numbers:
                            appearances[key] = int(numbers[0])
                        else:
                            appearances[key] = value
                    break
    
    # Also extract all years from championships data if available
    # This ensures we get all years even if the count comes from a different source
    if championships.get('ncaa_final_four'):
        final_four_years = [int(y) for y in championships['ncaa_final_four'] if y.isdigit()]
        all_final_four = [str(y) for y in sorted(final_four_years, reverse=True)]
        if all_final_four and not appearances.get('final_four_years'):
            appearances['final_four_years'] = all_final_four
    
    if championships.get('ncaa_elite_eight'):
        elite_eight_years = [int(y) for y in championships['ncaa_elite_eight'] if y.isdigit()]
        all_elite_eight = [str(y) for y in sorted(elite_eight_years, reverse=True)]
        if all_elite_eight and not appearances.get('elite_eight_years'):
            appearances['elite_eight_years'] = all_elite_eight
    
    if championships.get('ncaa_sweet_sixteen'):
        sweet_sixteen_years = [int(y) for y in championships['ncaa_sweet_sixteen'] if y.isdigit()]
        all_sweet_sixteen = [str(y) for y in sorted(sweet_sixteen_years, reverse=True)]
        if all_sweet_sixteen and not appearances.get('sweet_sixteen_years'):
            appearances['sweet_sixteen_years'] = all_sweet_sixteen
    
    return appearances


def extract_arena_info(template: mwparserfromhell.nodes.Template) -> Dict[str, Any]:
    """
    Extract arena and capacity information.
    
    Args:
        template: The infobox template node
    
    Returns:
        Dictionary with arena data
    """
    arena_info = {
        'arena': None,
        'capacity': None
    }
    
    # Try different parameter names for arena
    arena_params = ['arena', 'stadium', 'venue']
    for param_name in arena_params:
        param = safe_get_template_param(template, param_name)
        if param:
            value = clean_template_value(param.value)
            if value:
                arena_info['arena'] = value
                break
    
    # Try different parameter names for capacity
    capacity_params = ['capacity', 'seating_capacity', 'attendance']
    for param_name in capacity_params:
        param = safe_get_template_param(template, param_name)
        if param:
            value = clean_template_value(param.value)
            if value:
                # Extract number - handle comma-separated numbers like "13,800"
                # Remove commas and extract all digits
                numbers = re.findall(r'\d+', value.replace(',', ''))
                if numbers:
                    # Take the largest number (in case there are multiple)
                    arena_info['capacity'] = max(int(n) for n in numbers)
                else:
                    arena_info['capacity'] = value
                break
    
    return arena_info


def extract_all_time_record(template: mwparserfromhell.nodes.Template) -> Optional[str]:
    """
    Extract all-time record information.
    Tries to parse wikitext templates like {{Winning percentage|wins|losses}}.
    
    Args:
        template: The infobox template node
    
    Returns:
        All-time record string (W-L format), or None
    """
    record_params = ['all_time_record', 'overall_record', 'record', 'all_time']
    for param_name in record_params:
        param = safe_get_template_param(template, param_name)
        if param:
            # Get raw value to parse template syntax
            raw_value = str(param.value).strip()
            if raw_value:
                # Try to extract from {{Winning percentage|wins|losses|record=y}} template
                wp_match = re.search(r'\{\{Winning percentage\|(\d+(?:,\d+)?)\|(\d+(?:,\d+)?)', raw_value)
                if wp_match:
                    wins = wp_match.group(1).replace(',', '')
                    losses = wp_match.group(2).replace(',', '')
                    return f"{wins}-{losses}"
                
                # Try simple W-L format
                wl_match = re.search(r'(\d+(?:,\d+)?)\s*[-–]\s*(\d+(?:,\d+)?)', raw_value)
                if wl_match:
                    wins = wl_match.group(1).replace(',', '')
                    losses = wl_match.group(2).replace(',', '')
                    return f"{wins}-{losses}"
                
                # Try pipe-separated format
                pipe_match = re.search(r'(\d+(?:,\d+)?)\s*[|/]\s*(\d+(?:,\d+)?)', raw_value)
                if pipe_match:
                    wins = pipe_match.group(1).replace(',', '')
                    losses = pipe_match.group(2).replace(',', '')
                    return f"{wins}-{losses}"
                
                # Return cleaned value if no pattern matches
                cleaned = clean_template_value(raw_value)
                if cleaned:
                    return cleaned
    
    return None


def get_wikipedia_team_data(page_title: str) -> Dict[str, Any]:
    """
    Extract infobox data from a Wikipedia page for a college basketball team.
    
    Args:
        page_title: The title of the Wikipedia page (e.g., "UCLA_Bruins_men's_basketball")
                    Can also be a URL - will extract title automatically
    
    Returns:
        Dictionary containing extracted team data:
        - university_name: Name of the university
        - mascot: Team mascot/nickname (e.g., "Bruins", "Wildcats")
        - head_coach: Current head coach
        - head_coach_seasons: Number of seasons for current head coach
        - conference: Conference name
        - arena: Arena name
        - capacity: Arena capacity
        - all_time_record: All-time win-loss record
        - championships: Dictionary of championship years
        - tournament_appearances: Dictionary of tournament appearance counts
        - raw_template_data: All raw template parameters (for debugging)
    """
    # Handle URL input
    if page_title.startswith('http'):
        # Extract page title from URL
        match = re.search(r'/wiki/([^?#]+)', page_title)
        if match:
            page_title = match.group(1).replace('_', ' ')
        else:
            raise ValueError(f"Could not extract page title from URL: {page_title}")
    
    # Replace spaces with underscores for API
    page_title = page_title.replace(' ', '_')
    
    # Fetch wikitext
    wikitext = get_wikitext(page_title)
    if not wikitext:
        raise Exception(f"Wikipedia page not found: {page_title}")
    
    # Extract infobox template
    template = extract_infobox_template(wikitext)
    if not template:
        raise Exception(f"No infobox template found on page: {page_title}")
    
    # Initialize result dictionary
    result = {
        'page_title': page_title.replace('_', ' '),
        'university_name': None,
        'mascot': None,
        'head_coach': None,
        'head_coach_seasons': None,
        'conference': None,
        'location': None,
        'arena': None,
        'capacity': None,
        'all_time_record': None,
        'championships': {},
        'tournament_appearances': {},
        'raw_template_data': {}
    }
    
    # Extract all template parameters for raw data
    for param in template.params:
        param_name = str(param.name).strip()
        param_value = clean_template_value(param.value)
        result['raw_template_data'][param_name] = param_value
    
    # Extract specific fields
    # University name
    university_params = ['university', 'school', 'name', 'team']
    for param_name in university_params:
        param = safe_get_template_param(template, param_name)
        if param:
            value = clean_template_value(param.value)
            if value:
                result['university_name'] = value
                break

    # Mascot / Nickname
    mascot_params = ['nickname', 'mascot', 'team_name']
    for param_name in mascot_params:
        param = safe_get_template_param(template, param_name)
        if param:
            value = clean_template_value(param.value)
            if value:
                result['mascot'] = value
                break

    # Head coach
    coach_params = ['coach', 'head_coach', 'headcoach']
    for param_name in coach_params:
        param = safe_get_template_param(template, param_name)
        if param:
            value = clean_template_value(param.value)
            if value:
                result['head_coach'] = value
                break
    
    # Head coach tenure (number of seasons)
    tenure_params = ['tenure', 'coach_tenure', 'years']
    for param_name in tenure_params:
        param = safe_get_template_param(template, param_name)
        if param:
            value = clean_template_value(param.value)
            if value:
                # Extract number from tenure (e.g., "16th" -> 16, "5" -> 5)
                numbers = re.findall(r'\d+', value)
                if numbers:
                    result['head_coach_seasons'] = int(numbers[0])
                break
    
    # Conference
    conference_params = ['conference', 'conf', 'league']
    for param_name in conference_params:
        param = safe_get_template_param(template, param_name)
        if param:
            value = clean_template_value(param.value)
            if value:
                result['conference'] = value
                break
    
    # Location (city)
    location_params = ['location', 'city', 'city_location']
    for param_name in location_params:
        param = safe_get_template_param(template, param_name)
        if param:
            value = clean_template_value(param.value)
            if value:
                result['location'] = value
                break
    
    # Arena info
    arena_info = extract_arena_info(template)
    result['arena'] = arena_info['arena']
    result['capacity'] = arena_info['capacity']
    
    # All-time record
    result['all_time_record'] = extract_all_time_record(template)
    
    # Championships
    result['championships'] = extract_championships(template)
    
    # Tournament appearances (pass championships to extract recent appearances)
    result['tournament_appearances'] = extract_tournament_appearances(template, result['championships'])
    
    return result


def get_season_rankings(team_name: str, season: int) -> Dict[str, Any]:
    """
    Extract current and highest AP rankings from a season-specific Wikipedia page.
    
    Args:
        team_name: Team name (e.g., "UCLA", "Michigan State")
        season: Season year (e.g., 2026)
    
    Returns:
        Dictionary with 'current_rank' and 'highest_rank' (both can be None or int)
    """
    # Construct season page title
    # Format: "2025–26 [Team Name] [Mascot] men's basketball team"
    # We need to map team names to their season page format
    # For now, try common patterns - this could be improved with a mapping
    
    # Try to construct the season page title
    # Season format: "2025–26" for season 2026
    season_str = f"{season-1}–{str(season)[2:]}"
    
    # Common team name to season page title mappings
    # This is a simplified version - ideally we'd have a comprehensive mapping
    team_season_mappings = {
        'ucla': f"{season_str} UCLA Bruins men's basketball team",
        'arizona': f"{season_str} Arizona Wildcats men's basketball team",
        'michigan': f"{season_str} Michigan Wolverines men's basketball team",
        'michigan state': f"{season_str} Michigan State Spartans men's basketball team",
        'msu': f"{season_str} Michigan State Spartans men's basketball team",
        'purdue': f"{season_str} Purdue Boilermakers men's basketball team",
        'ohio state': f"{season_str} Ohio State Buckeyes men's basketball team",
        'indiana': f"{season_str} Indiana Hoosiers men's basketball team",
        'wisconsin': f"{season_str} Wisconsin Badgers men's basketball team",
        'illinois': f"{season_str} Illinois Fighting Illini men's basketball team",
        'iowa': f"{season_str} Iowa Hawkeyes men's basketball team",
        'maryland': f"{season_str} Maryland Terrapins men's basketball team",
        'minnesota': f"{season_str} Minnesota Golden Gophers men's basketball team",
        'nebraska': f"{season_str} Nebraska Cornhuskers men's basketball team",
        'northwestern': f"{season_str} Northwestern Wildcats men's basketball team",
        'penn state': f"{season_str} Penn State Nittany Lions basketball team",
        'rutgers': f"{season_str} Rutgers Scarlet Knights men's basketball team",
        'usc': f"{season_str} USC Trojans men's basketball team",
        'southern california': f"{season_str} USC Trojans men's basketball team",
        'washington': f"{season_str} Washington Huskies men's basketball team",
        'oregon': f"{season_str} Oregon Ducks men's basketball team",
        'utsa': f"{season_str} UTSA Roadrunners men's basketball team",
        'texas-san antonio': f"{season_str} UTSA Roadrunners men's basketball team",
        'university of texas at san antonio': f"{season_str} UTSA Roadrunners men's basketball team",
    }
    
    team_key = team_name.lower().strip()
    page_title = team_season_mappings.get(team_key)
    
    if not page_title:
        # Try to construct from team name (fallback)
        # This won't work for all teams but might work for some
        return {'current_rank': None, 'highest_rank': None}
    
    try:
        wikitext = get_wikitext(page_title)
        if not wikitext:
            return {'current_rank': None, 'highest_rank': None}
        
        # Extract current ranking from infobox
        current_rank = None
        template = extract_infobox_template(wikitext)
        if template:
            ranking_params = ['APRank', 'aprank', 'ap_rank', 'CoachRank', 'coachrank']
            for param_name in ranking_params:
                param = safe_get_template_param(template, param_name)
                if param:
                    value = clean_template_value(param.value)
                    if value:
                        num_match = re.search(r'(\d+)', value)
                        if num_match:
                            current_rank = int(num_match.group(1))
                            break
        
        # Extract highest ranking from schedule entries
        highest_rank = None
        wikicode = mwparserfromhell.parse(wikitext)
        rankings = []
        
        for template in wikicode.filter_templates():
            template_name = str(template.name).strip().lower()
            if 'cbb schedule entry' in template_name:
                try:
                    rank_param = template.get('rank')
                    if rank_param:
                        rank_value = str(rank_param.value).strip()
                        rank_value = re.sub(r'\[\[[^\]]+\]\]', '', rank_value)
                        rank_value = re.sub(r'\{\{[^}]+\}\}', '', rank_value)
                        rank_value = rank_value.strip()
                        
                        if rank_value and rank_value.lower() not in ['', 'n/a', 'none', '—', '–', '-']:
                            num_match = re.search(r'(\d+)', rank_value)
                            if num_match:
                                rankings.append(int(num_match.group(1)))
                except ValueError:
                    pass
        
        if rankings:
            highest_rank = min(rankings)  # Lowest number = highest ranking
        
        return {
            'current_rank': current_rank,
            'highest_rank': highest_rank
        }
        
    except Exception as e:
        # Return None values on error
        return {'current_rank': None, 'highest_rank': None}


if __name__ == '__main__':
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        page_title = sys.argv[1]
    else:
        page_title = "UCLA_Bruins_men's_basketball"
    
    try:
        data = get_wikipedia_team_data(page_title)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

