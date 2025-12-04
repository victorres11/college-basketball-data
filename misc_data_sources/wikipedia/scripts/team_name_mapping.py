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
TEAM_WIKIPEDIA_MAPPING = {
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
    'washington': "Washington Huskies men's basketball",
    'eastern washington': "Eastern Washington Eagles men's basketball",
    'msu': "Michigan State Spartans men's basketball",
    'utsa': "UTSA Roadrunners men's basketball",
    'texas-san antonio': "UTSA Roadrunners men's basketball",
    'university of texas at san antonio': "UTSA Roadrunners men's basketball",
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
    
    # Try direct mapping
    if team_key in TEAM_WIKIPEDIA_MAPPING:
        return TEAM_WIKIPEDIA_MAPPING[team_key]
    
    # Try Big Ten mapping
    big_ten_mapping = load_big_ten_mapping()
    if team_key in big_ten_mapping:
        return big_ten_mapping[team_key]
    
    # Return None if not found
    return None

