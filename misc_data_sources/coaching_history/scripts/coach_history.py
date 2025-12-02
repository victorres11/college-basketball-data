#!/usr/bin/env python3
"""
Script to extract head coach and season data from Sports Reference
"""
import requests
from bs4 import BeautifulSoup
import re
import json

def get_coach_history(team_slug, years=6):
    """
    Fetch head coach history for a team from Sports Reference.
    
    Args:
        team_slug: Team identifier for Sports Reference URL (e.g., 'oregon')
        years: Number of recent years to fetch (default: 6)
    
    Returns:
        list: List of dictionaries with season data
    """
    # Sports Reference URL format
    url = f"https://www.sports-reference.com/cbb/schools/{team_slug}/men/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch data for {team_slug}: {e}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the seasons table - table ID is the team slug
    table = soup.find('table', id=team_slug)
    
    if not table:
        raise Exception(f"Could not find seasons table for {team_slug}")
    
    # Get all rows
    rows = table.find_all('tr')
    if len(rows) < 2:
        raise Exception("Table has no data rows")
    
    # Column structure is fixed:
    # 0: Rk, 1: Season, 2: Conf, 3: W (Overall), 4: L (Overall), 5: W-L% (Overall),
    # 6: W (Conf), 7: L (Conf), 8: W-L% (Conf), 9: SRS, 10: SOS, 11: PS/G, 12: PA/G,
    # 13: AP Pre, 14: AP High, 15: AP Final, 16: NCAA Tournament, 17: Seed, 18: Coach(es)
    season_idx = 1
    conf_idx = 2
    overall_w_idx = 3
    overall_l_idx = 4
    conf_w_idx = 6
    conf_l_idx = 7
    ncaa_idx = 16
    seed_idx = 17
    coach_idx = 18
    
    seasons_data = []
    
    # Process data rows
    # Row 0 appears to be a header row with column labels
    # Row 1 is the actual header with "Rk", "Season", etc.
    # Row 2 is the current/incomplete season (e.g., 2025-26)
    # Row 3+ are complete seasons
    # Skip current season and get last N complete seasons (starting from row 3)
    start_row = 3  # Skip current incomplete season
    end_row = start_row + years
    for row in rows[start_row:end_row]:
        cols = row.find_all(['td', 'th'])
        if len(cols) < 19:  # Need at least 19 columns
            continue
        
        # Extract data using fixed column indices
        season = cols[season_idx].get_text().strip() if season_idx < len(cols) else ""
        conference = cols[conf_idx].get_text().strip() if conf_idx < len(cols) else ""
        
        # Overall W/L
        overall_w = cols[overall_w_idx].get_text().strip() if overall_w_idx < len(cols) else "0"
        overall_l = cols[overall_l_idx].get_text().strip() if overall_l_idx < len(cols) else "0"
        overall_wl = f"{overall_w}-{overall_l}"
        
        # Conference W/L
        conf_w = cols[conf_w_idx].get_text().strip() if conf_w_idx < len(cols) else "0"
        conf_l = cols[conf_l_idx].get_text().strip() if conf_l_idx < len(cols) else "0"
        conf_wl = f"{conf_w}-{conf_l}"
        
        # NCAA Tournament
        ncaa_text = ""
        if ncaa_idx < len(cols):
            ncaa_cell = cols[ncaa_idx]
            ncaa_link = ncaa_cell.find('a')
            if ncaa_link:
                ncaa_text = ncaa_link.get_text().strip()
            else:
                ncaa_text = ncaa_cell.get_text().strip()
        
        # Seed
        seed = ""
        if seed_idx < len(cols):
            seed = cols[seed_idx].get_text().strip()
        
        # Coach
        coach = ""
        if coach_idx < len(cols):
            coach_cell = cols[coach_idx]
            coach_link = coach_cell.find('a')
            if coach_link:
                coach = coach_link.get_text().strip()
            else:
                coach = coach_cell.get_text().strip()
        
        seasons_data.append({
            'season': season,
            'conference': conference,
            'overallWL': overall_wl,
            'overallW': overall_w,
            'overallL': overall_l,
            'conferenceWL': conf_wl,
            'conferenceW': conf_w,
            'conferenceL': conf_l,
            'ncaaTournament': ncaa_text,
            'seed': seed,
            'coach': coach
        })
    
    return seasons_data

if __name__ == '__main__':
    # Test with Oregon
    print("Fetching Oregon coach history (last 6 years)...\n")
    try:
        data = get_coach_history('oregon', years=6)
        print(json.dumps(data, indent=2))
        print(f"\n✅ Successfully retrieved {len(data)} seasons")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

