#!/usr/bin/env python3
"""
Helper function to map team names to Wikipedia page titles.
"""
import json
import os
from pathlib import Path

# Load the Big Ten mapping
def load_big_ten_mapping():
    """Load the Big Ten team name to Wikipedia page title mapping."""
    script_dir = Path(__file__).parent
    mapping_file = script_dir.parent / 'test_data' / 'big_ten_wikipedia_pages.json'
    
    if mapping_file.exists():
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            mapping = {}
            for result in data.get('results', []):
                if result.get('found') and result.get('has_infobox'):
                    team_name = result['team_name']
                    page_title = result['page_title']
                    mapping[team_name.lower()] = page_title
            return mapping
    return {}


def get_wikipedia_page_title(team_name):
    """
    Get Wikipedia page title for a team name.
    
    Args:
        team_name: Team name (e.g., "UCLA", "Michigan State", "Oregon")
    
    Returns:
        Wikipedia page title, or None if not found
    """
    # Load Big Ten mapping
    big_ten_mapping = load_big_ten_mapping()
    
    # Try exact match (case-insensitive)
    team_key = team_name.lower()
    if team_key in big_ten_mapping:
        return big_ten_mapping[team_key]
    
    # Try common variations
    variations = [
        team_name,
        team_name + " men's basketball",
        team_name.replace("State", "State Spartans") + " men's basketball",
        team_name.replace("State", "State Boilermakers") + " men's basketball",
        # Add more variations as needed
    ]
    
    # For now, return a constructed title based on common pattern
    # Most teams follow: "{Team Name} {Mascot} men's basketball"
    # This is a fallback - ideally we'd have a comprehensive mapping
    return None


# Common team name to Wikipedia page title mappings
# Based on teams from bballnet.com and common searches
TEAM_WIKIPEDIA_MAPPING = {
    # Big Ten
    'ucla': "UCLA Bruins men's basketball",
    'michigan state': "Michigan State Spartans men's basketball",
    'michigan': "Michigan Wolverines men's basketball",
    'indiana': "Indiana Hoosiers men's basketball",
    'ohio state': "Ohio State Buckeyes men's basketball",
    'purdue': "Purdue Boilermakers men's basketball",
    'wisconsin': "Wisconsin Badgers men's basketball",
    'illinois': "Illinois Fighting Illini men's basketball",
    'iowa': "Iowa Hawkeyes men's basketball",
    'maryland': "Maryland Terrapins men's basketball",
    'minnesota': "Minnesota Golden Gophers men's basketball",
    'nebraska': "Nebraska Cornhuskers men's basketball",
    'northwestern': "Northwestern Wildcats men's basketball",
    'oregon': "Oregon Ducks men's basketball",
    'penn state': "Penn State Nittany Lions men's basketball",
    'rutgers': "Rutgers Scarlet Knights men's basketball",
    'usc': "USC Trojans men's basketball",
    'southern california': "USC Trojans men's basketball",
    'washington': "Washington Huskies men's basketball",
    'eastern washington': "Eastern Washington Eagles men's basketball",
    'msu': "Michigan State Spartans men's basketball",
    
    # ACC
    'duke': "Duke Blue Devils men's basketball",
    'north carolina': "North Carolina Tar Heels men's basketball",
    'unc': "North Carolina Tar Heels men's basketball",
    'louisville': "Louisville Cardinals men's basketball",
    'virginia': "Virginia Cavaliers men's basketball",
    'clemson': "Clemson Tigers men's basketball",
    'miami': "Miami Hurricanes men's basketball",
    'miami (fl)': "Miami Hurricanes men's basketball",
    'miami fl': "Miami Hurricanes men's basketball",
    
    # SEC
    'alabama': "Alabama Crimson Tide men's basketball",
    'georgia': "Georgia Bulldogs men's basketball",
    'lsu': "LSU Tigers men's basketball",
    'louisiana state': "LSU Tigers men's basketball",
    'kentucky': "Kentucky Wildcats men's basketball",
    'tennessee': "Tennessee Volunteers men's basketball",
    'vanderbilt': "Vanderbilt Commodores men's basketball",
    'auburn': "Auburn Tigers men's basketball",
    'arkansas': "Arkansas Razorbacks men's basketball",
    'florida': "Florida Gators men's basketball",
    
    # Big 12
    'kansas': "Kansas Jayhawks men's basketball",
    'texas tech': "Texas Tech Red Raiders men's basketball",
    'iowa state': "Iowa State Cyclones men's basketball",
    'iowa st.': "Iowa State Cyclones men's basketball",
    'iowa st': "Iowa State Cyclones men's basketball",
    'arizona': "Arizona Wildcats men's basketball",
    'byu': "BYU Cougars men's basketball",
    'brigham young': "BYU Cougars men's basketball",
    'houston': "Houston Cougars men's basketball",
    
    # Big East
    'uconn': "UConn Huskies men's basketball",
    'connecticut': "UConn Huskies men's basketball",
    "st. john's": "St. John's Red Storm men's basketball",
    "st john's": "St. John's Red Storm men's basketball",
    "st. john's (ny)": "St. John's Red Storm men's basketball",
    'butler': "Butler Bulldogs men's basketball",
    
    # WCC
    'gonzaga': "Gonzaga Bulldogs men's basketball",
    "saint mary's": "Saint Mary's Gaels men's basketball",
    "saint mary's (ca)": "Saint Mary's Gaels men's basketball",
    "st. mary's": "Saint Mary's Gaels men's basketball",
    "st mary's": "Saint Mary's Gaels men's basketball",
    'santa clara': "Santa Clara Broncos men's basketball",
    'san francisco': "San Francisco Dons men's basketball",
    'pacific': "Pacific Tigers men's basketball",
    'seattle': "Seattle Redhawks men's basketball",
    'seattle u': "Seattle Redhawks men's basketball",
    'lmu': "Loyola Marymount Lions men's basketball",
    "lmu (ca)": "Loyola Marymount Lions men's basketball",
    'loyola marymount': "Loyola Marymount Lions men's basketball",
    'washington state': "Washington State Cougars men's basketball",
    'washington st.': "Washington State Cougars men's basketball",
    'washington st': "Washington State Cougars men's basketball",
    'oregon state': "Oregon State Beavers men's basketball",
    'oregon st.': "Oregon State Beavers men's basketball",
    'oregon st': "Oregon State Beavers men's basketball",
    'portland': "Portland Pilots men's basketball",
    'san diego': "San Diego Toreros men's basketball",
    'pepperdine': "Pepperdine Waves men's basketball",
    
    # Mountain West
    'utah state': "Utah State Aggies men's basketball",
    'utah st.': "Utah State Aggies men's basketball",
    'utah st': "Utah State Aggies men's basketball",
    
    # Atlantic 10
    'saint louis': "Saint Louis Billikens men's basketball",
    "st. louis": "Saint Louis Billikens men's basketball",
    "st louis": "Saint Louis Billikens men's basketball",
    
    # Ivy League
    'yale': "Yale Bulldogs men's basketball",
    
    # Other conferences
    'utsa': "UTSA Roadrunners men's basketball",
    'texas-san antonio': "UTSA Roadrunners men's basketball",
    'university of texas at san antonio': "UTSA Roadrunners men's basketball",
    
    # Additional common teams
    'north dakota state': "North Dakota State Bison men's basketball",
    'north dakota st.': "North Dakota State Bison men's basketball",
    'north dakota st': "North Dakota State Bison men's basketball",
    'south dakota state': "South Dakota State Jackrabbits men's basketball",
    'south dakota st.': "South Dakota State Jackrabbits men's basketball",
    'south dakota st': "South Dakota State Jackrabbits men's basketball",
    "st. thomas": "St. Thomas Tommies men's basketball",
    "st. thomas (mn)": "St. Thomas Tommies men's basketball",
    "st thomas": "St. Thomas Tommies men's basketball",
    'denver': "Denver Pioneers men's basketball",
    'south dakota': "South Dakota Coyotes men's basketball",
    'oral roberts': "Oral Roberts Golden Eagles men's basketball",
    'omaha': "Omaha Mavericks men's basketball",
    'nebraska omaha': "Omaha Mavericks men's basketball",
    'north dakota': "North Dakota Fighting Hawks men's basketball",
    'kansas city': "Kansas City Roos men's basketball",
    'missouri kansas city': "Kansas City Roos men's basketball",
    'south alabama': "South Alabama Jaguars men's basketball",
    'marshall': "Marshall Thundering Herd men's basketball",
    'southern mississippi': "Southern Miss Golden Eagles men's basketball",
    'southern miss.': "Southern Miss Golden Eagles men's basketball",
    'southern miss': "Southern Miss Golden Eagles men's basketball",
    'troy': "Troy Trojans men's basketball",
    'arkansas state': "Arkansas State Red Wolves men's basketball",
    'arkansas st.': "Arkansas State Red Wolves men's basketball",
    'arkansas st': "Arkansas State Red Wolves men's basketball",
    'james madison': "James Madison Dukes men's basketball",
    'coastal carolina': "Coastal Carolina Chanticleers men's basketball",
    'old dominion': "Old Dominion Monarchs men's basketball",
    'georgia southern': "Georgia Southern Eagles men's basketball",
    'ga. southern': "Georgia Southern Eagles men's basketball",
    'texas state': "Texas State Bobcats men's basketball",
    'texas st.': "Texas State Bobcats men's basketball",
    'texas st': "Texas State Bobcats men's basketball",
    'appalachian state': "Appalachian State Mountaineers men's basketball",
    'app state': "Appalachian State Mountaineers men's basketball",
    'georgia state': "Georgia State Panthers men's basketball",
    'georgia st.': "Georgia State Panthers men's basketball",
    'georgia st': "Georgia State Panthers men's basketball",
    'louisiana': "Louisiana Ragin' Cajuns men's basketball",
    'louisiana lafayette': "Louisiana Ragin' Cajuns men's basketball",
    'ulm': "Louisiana–Monroe Warhawks men's basketball",
    'louisiana monroe': "Louisiana–Monroe Warhawks men's basketball",
    'utah valley': "Utah Valley Wolverines men's basketball",
    'california baptist': "California Baptist Lancers men's basketball",
    'ut arlington': "UT Arlington Mavericks men's basketball",
    'texas arlington': "UT Arlington Mavericks men's basketball",
    'tarleton state': "Tarleton State Texans men's basketball",
    'tarleton st.': "Tarleton State Texans men's basketball",
    'tarleton st': "Tarleton State Texans men's basketball",
    'utah tech': "Utah Tech Trailblazers men's basketball",
    'dixie state': "Utah Tech Trailblazers men's basketball",
    'abilene christian': "Abilene Christian Wildcats men's basketball",
    'southern utah': "Southern Utah Thunderbirds men's basketball",
    'houston christian': "Houston Christian Huskies men's basketball",
    'houston baptist': "Houston Christian Huskies men's basketball",
    'northwestern state': "Northwestern State Demons men's basketball",
    'northwestern st.': "Northwestern State Demons men's basketball",
    'northwestern st': "Northwestern State Demons men's basketball",
}


def get_wikipedia_page_title_safe(team_name):
    """
    Get Wikipedia page title for a team name with fallback logic.
    
    Args:
        team_name: Team name (e.g., "UCLA", "Michigan State", "Oregon")
    
    Returns:
        Wikipedia page title, or None if not found
    """
    # Normalize team name
    team_key = team_name.lower().strip()
    
    # Remove common suffixes/abbreviations for matching
    normalized = team_key
    # Remove trailing periods and common abbreviations
    normalized = normalized.rstrip('.')
    # Normalize "st." to "state" for matching
    normalized = normalized.replace(' st.', ' state').replace(' st ', ' state ')
    
    # Try direct mapping with original key
    if team_key in TEAM_WIKIPEDIA_MAPPING:
        return TEAM_WIKIPEDIA_MAPPING[team_key]
    
    # Try normalized key
    if normalized in TEAM_WIKIPEDIA_MAPPING:
        return TEAM_WIKIPEDIA_MAPPING[normalized]
    
    # Try Big Ten mapping
    big_ten_mapping = load_big_ten_mapping()
    if team_key in big_ten_mapping:
        return big_ten_mapping[team_key]
    if normalized in big_ten_mapping:
        return big_ten_mapping[normalized]
    
    # Return None if no mapping found
    # Explicit mappings are required for accuracy
    return None

