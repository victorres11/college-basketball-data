#!/usr/bin/env python3
"""
Script to extract NET rating from bballnet.com main rankings page
"""
import requests
from bs4 import BeautifulSoup
import re

def normalize_team_name_for_matching(name):
    """
    Normalize team name for matching against bballnet.com table.
    Removes common suffixes and normalizes formatting, but preserves "state"/"st".
    """
    if not name:
        return ""
    
    name = name.lower().strip()
    
    # Normalize "st." to "st" for consistency
    name = name.replace(' st.', ' st').replace(' st ', ' st ')
    
    # Remove common suffixes/abbreviations (but NOT "state" or "st")
    suffixes = [
        ' university', ' college',
        ' ucla', ' usc', ' unc', ' uconn', ' lsu', ' byu',
        ' bruins', ' trojans', ' tar heels', ' huskies', ' tigers',
        ' wildcats', ' bulldogs', ' eagles', ' spartans', ' wolverines'
    ]
    
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
            break
    
    # Remove extra spaces and punctuation (but keep spaces between words)
    name = re.sub(r'[^\w\s]', '', name)
    name = ' '.join(name.split())
    
    return name

# Team name mappings for bballnet.com
TEAM_NAME_MAPPING = {
    'usc': 'Southern California',
    'southern california': 'Southern California',
    'michigan state': 'Michigan St.',
    'ohio state': 'Ohio St.',
    'penn state': 'Penn St.',
    'iowa state': 'Iowa St.',
    'washington state': 'Washington St.',
    'oregon state': 'Oregon St.',
    'kansas state': 'Kansas St.',
    'oklahoma state': 'Oklahoma St.',
    'florida state': 'Florida St.',
    'north carolina state': 'NC State',
    'nc state': 'NC State',
}

def get_net_rating(team_name):
    """
    Fetch NET rating for a team from bballnet.com main page.
    
    Args:
        team_name: Team name (e.g., "UCLA", "Oregon", "Michigan State")
    
    Returns:
        dict: {
            'net_rating': int or None,
            'previous_rating': int or None,
            'team_name_found': str or None,
            'url': str
        }
    """
    url = "https://bballnet.com/"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch NET ratings page: {e}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the "All Conferences" table
    # Look for table with Rank, Prev, School columns
    tables = soup.find_all('table')
    
    rankings_table = None
    for table in tables:
        headers = table.find_all('th')
        if headers:
            header_text = ' '.join([h.get_text().strip().lower() for h in headers])
            # Check if this is the rankings table (has Rank, Prev, School)
            if 'rank' in header_text and 'prev' in header_text and 'school' in header_text:
                rankings_table = table
                break
    
    if not rankings_table:
        raise Exception("Could not find NET rankings table on page")
    
    # Apply team name mapping first
    team_name_lower = team_name.lower().strip()
    mapped_name = TEAM_NAME_MAPPING.get(team_name_lower, team_name)
    
    # Normalize the search team name
    search_name_normalized = normalize_team_name_for_matching(mapped_name)
    
    # Collect all potential matches first, then choose best
    potential_matches = []
    
    # Search through table rows
    rows = rankings_table.find_all('tr')
    
    # Skip header row
    for row in rows[1:]:
        cols = row.find_all('td')
        if len(cols) < 3:
            continue
        
        # Column structure: Rank (0), Prev (1), School (2), Conf (3), Record (4)
        rank_text = cols[0].get_text().strip()
        prev_text = cols[1].get_text().strip() if len(cols) > 1 else ""
        school_text = cols[2].get_text().strip() if len(cols) > 2 else ""
        conf_text = cols[3].get_text().strip() if len(cols) > 3 else ""
        
        # Check if this row matches our team
        school_normalized = normalize_team_name_for_matching(school_text)
        
        # Calculate match score
        match_score = 0
        is_exact_match = False
        
        # Normalize "state" vs "st" for better matching
        search_normalized_state = search_name_normalized.replace(' state', ' st').replace('state', 'st')
        school_normalized_state = school_normalized.replace(' state', ' st').replace('state', 'st')
        
        # Exact match gets highest priority
        if search_name_normalized == school_normalized or search_normalized_state == school_normalized_state:
            match_score = 100
            is_exact_match = True
        else:
            # Check word-by-word matching
            search_words = set(search_name_normalized.split())
            school_words = set(school_normalized.split())
            
            # Prevent substring matches (e.g., "iowa" matching "iowa st", "michigan" matching "michigan state")
            # If search has fewer words and all its words are in school, but school has more words,
            # it might be a substring issue - we want to avoid this
            if len(search_words) < len(school_words):
                # Check if this is a problematic substring match
                # e.g., "iowa" should not match "iowa st" if we're looking for just "iowa"
                # e.g., "michigan" should not match "michigan state" if we're looking for "michigan state"
                if search_words.issubset(school_words):
                    # This could be a substring match - check if school has "st" or "state"
                    school_has_state = any(word in ['st', 'state'] for word in school_words)
                    search_has_state = any(word in ['st', 'state'] for word in search_words)
                    if school_has_state and not search_has_state:
                        # This is likely a substring match we want to avoid
                        match_score = 0
                    else:
                        match_score = 70
                else:
                    overlap = search_words.intersection(school_words)
                    if len(overlap) > 0:
                        match_score = len(overlap) * 20
            elif len(search_words) > len(school_words):
                # Search has more words - check if school is subset
                # This is OK - e.g., "Michigan State" matching "Michigan St." is fine
                if school_words.issubset(search_words):
                    # Check if the difference is just "state" vs "st"
                    diff = search_words - school_words
                    if diff == {'state'} or diff == {'st'}:
                        match_score = 95  # Very high score for state/st variation
                    else:
                        match_score = 70
                else:
                    overlap = search_words.intersection(school_words)
                    if len(overlap) > 0:
                        # If most words match, it might still be a good match
                        if len(overlap) >= len(search_words) * 0.7:
                            match_score = 60
                        else:
                            match_score = len(overlap) * 20
            else:
                # Same number of words
                if search_words == school_words:
                    match_score = 90
                else:
                    overlap = search_words.intersection(school_words)
                    if len(overlap) > 0:
                        # If all words match (just different order), high score
                        if len(overlap) == len(search_words):
                            match_score = 85
                        else:
                            match_score = len(overlap) * 20
        
        if match_score > 0:
            try:
                net_rating = int(rank_text) if rank_text else None
                prev_rating = int(prev_text) if prev_text and prev_text != '-' else None
                
                potential_matches.append({
                    'net_rating': net_rating,
                    'previous_rating': prev_rating,
                    'team_name_found': school_text,
                    'conference': conf_text,
                    'match_score': match_score,
                    'is_exact_match': is_exact_match
                })
            except ValueError:
                continue
    
    # If we found matches, return the best one
    if potential_matches:
        # Prefer matches in Big Ten conference if available (for Big Ten teams)
        # But don't filter out other conferences - just prefer Big Ten
        big_ten_matches = [m for m in potential_matches if 'big ten' in m['conference'].lower()]
        other_matches = [m for m in potential_matches if 'big ten' not in m['conference'].lower()]
        
        # If we have Big Ten matches, use those; otherwise use all matches
        matches_to_consider = big_ten_matches if big_ten_matches else potential_matches
        
        # Sort by match score (highest first), then prefer exact matches
        matches_to_consider.sort(key=lambda x: (x['match_score'], x['is_exact_match']), reverse=True)
        best_match = matches_to_consider[0]
        
        return {
            'net_rating': best_match['net_rating'],
            'previous_rating': best_match['previous_rating'],
            'team_name_found': best_match['team_name_found'],
            'conference': best_match['conference'],
            'url': url
        }
    
    # Team not found
    return {
        'net_rating': None,
        'previous_rating': None,
        'team_name_found': None,
        'url': url,
        'error': f'Team "{team_name}" not found in NET rankings'
    }

if __name__ == '__main__':
    # Test with UCLA (should be rank 76)
    result = get_net_rating('UCLA')
    print(f"UCLA NET Rating: {result}")
    
    # Test with Oregon
    result = get_net_rating('Oregon')
    print(f"\nOregon NET Rating: {result}")

