#!/usr/bin/env python3
"""
Script to extract quadrant wins data from bballnet.com HTML
"""
import requests
from bs4 import BeautifulSoup
import json
import os

# Load team slug mapping (prefer comprehensive auto-generated mapping)
COMPREHENSIVE_MAPPING_FILE = os.path.join(os.path.dirname(__file__), 'bballnet_team_mapping.json')
LEGACY_MAPPING_FILE = os.path.join(os.path.dirname(__file__), 'team_slug_mapping.json')

TEAM_SLUG_MAPPING = {}

# First try comprehensive auto-generated mapping
if os.path.exists(COMPREHENSIVE_MAPPING_FILE):
    with open(COMPREHENSIVE_MAPPING_FILE, 'r') as f:
        mapping_data = json.load(f)
        TEAM_SLUG_MAPPING = mapping_data.get('team_slug_mapping', {})
# Fallback to legacy mapping if comprehensive doesn't exist
elif os.path.exists(LEGACY_MAPPING_FILE):
    with open(LEGACY_MAPPING_FILE, 'r') as f:
        mapping_data = json.load(f)
        TEAM_SLUG_MAPPING = mapping_data.get('team_slug_mapping', {})

def get_bballnet_slug(team_slug):
    """Get the bballnet.com slug for a team, using mapping if available."""
    return TEAM_SLUG_MAPPING.get(team_slug, team_slug)

def get_quadrant_data(team_slug):
    """
    Fetch and parse quadrant data for a team
    
    Args:
        team_slug: Team identifier (e.g., 'oregon')
    
    Returns:
        dict: Quadrant data including wins/losses and opponent names
    """
    # Use mapped slug if available
    bballnet_slug = get_bballnet_slug(team_slug)
    url = f"https://bballnet.com/teams/{bballnet_slug}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch data for {team_slug} (slug: {bballnet_slug}): {e}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract team info
    team_name_elem = soup.find('h1', class_='team-name')
    team_name = team_name_elem.text.strip() if team_name_elem else team_slug
    
    data = {
        'team': team_slug,
        'team_name': team_name,
        'url': url,
        'quadrants': {}
    }
    
    # Find all quad sections - try multiple selectors
    quads = soup.find_all('div', class_=lambda x: x and 'q' in str(x).lower())
    
    if not quads:
        # Try alternative selector
        quads = soup.find_all('div', {'class': lambda x: x and any('quad' in str(c).lower() for c in (x if isinstance(x, list) else [x]))})
    
    for quad in quads:
        # Get quad number from class
        quad_classes = quad.get('class', [])
        if not isinstance(quad_classes, list):
            quad_classes = [quad_classes]
        
        quad_num = None
        for cls in quad_classes:
            cls_str = str(cls).lower()
            # Look for patterns like 'q1', 'quad1', 'quad-1', etc.
            if 'q1' in cls_str or 'quad1' in cls_str or 'quad-1' in cls_str:
                quad_num = '1'
                break
            elif 'q2' in cls_str or 'quad2' in cls_str or 'quad-2' in cls_str:
                quad_num = '2'
                break
            elif 'q3' in cls_str or 'quad3' in cls_str or 'quad-3' in cls_str:
                quad_num = '3'
                break
            elif 'q4' in cls_str or 'quad4' in cls_str or 'quad-4' in cls_str:
                quad_num = '4'
                break
        
        if not quad_num:
            continue
        
        # Get record - try multiple selectors
        record = 'N/A'
        record_div = quad.find('div', class_='quad-record')
        if not record_div:
            record_div = quad.find('div', class_=lambda x: x and 'record' in str(x).lower())
        if not record_div:
            # Try finding text that contains "Record:"
            record_text = quad.get_text()
            if 'Record:' in record_text:
                record = record_text.split('Record:')[1].split('\n')[0].strip()
        else:
            record = record_div.text.strip().replace('Record: ', '').replace('Record:', '').strip()
        
        # Parse wins and losses from record (e.g., "2-0" or "0-2")
        wins = 0
        losses = 0
        if record and record != 'N/A' and '-' in record:
            try:
                parts = record.split('-')
                wins = int(parts[0].strip())
                losses = int(parts[1].strip())
            except:
                pass
        
        # Get games/opponents - opponent name is in the 6th column (index 5)
        opponents = []
        games = []
        table = quad.find('table')
        if table:
            rows = table.find_all('tr')
            # Check if first row is a header (has th tags) or data (has td tags)
            start_idx = 0
            if rows:
                first_row_th = rows[0].find_all('th')
                if len(first_row_th) > 0:
                    start_idx = 1  # Skip header row
            
            for row in rows[start_idx:]:  # Process all data rows
                cols = row.find_all('td')
                if len(cols) >= 6:
                    result = cols[0].text.strip()
                    score = cols[1].text.strip()
                    location = cols[2].text.strip()
                    # NET ranking is in cols[3], skip cols[4] (icon), opponent name is in cols[5]
                    opponent_cell = cols[5]
                    opponent_link = opponent_cell.find('a')
                    opponent = opponent_link.text.strip() if opponent_link else opponent_cell.text.strip()
                    
                    # Clean up opponent name (remove extra whitespace and leading numbers)
                    opponent = ' '.join(opponent.split())
                    # Remove leading numbers (e.g., "21Auburn" -> "Auburn")
                    import re
                    opponent = re.sub(r'^\d+', '', opponent).strip()
                    
                    # Add to opponents list (normalized for matching)
                    opponent_normalized = opponent.lower().replace(' ', '_').replace('.', '')
                    if opponent_normalized and opponent_normalized not in opponents:
                        opponents.append(opponent_normalized)
                    
                    games.append({
                        'result': result,
                        'score': score,
                        'location': location,
                        'opponent': opponent
                    })
        
        data['quadrants'][f'quad{quad_num}'] = {
            'record': record,
            'wins': wins,
            'losses': losses,
            'opponents': opponents,
            'games': games
        }
    
    return data

if __name__ == '__main__':
    # Example usage
    team_data = get_quadrant_data('oregon')
    print(json.dumps(team_data, indent=2))