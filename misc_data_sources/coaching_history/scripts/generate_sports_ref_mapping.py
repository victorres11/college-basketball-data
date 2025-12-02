#!/usr/bin/env python3
"""
Scrape Sports Reference to generate a comprehensive team slug mapping.

This script fetches the schools index page and extracts all team URLs to create
a mapping from various team name formats to the correct Sports Reference slug.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from collections import defaultdict

def normalize_team_name(name):
    """Normalize team name for matching (lowercase, remove punctuation, etc.)"""
    # Remove common suffixes and punctuation
    name = name.lower().strip()
    name = re.sub(r'\s*\(.*?\)', '', name)  # Remove parentheticals like "(NY)", "(CA)"
    name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
    return name

def extract_team_slug_from_url(url):
    """Extract team slug from Sports Reference URL"""
    # URL format: /cbb/schools/michigan-state/men/
    match = re.search(r'/cbb/schools/([^/]+)/', url)
    if match:
        return match.group(1)
    return None

def scrape_sports_ref_teams():
    """Scrape all team URLs from Sports Reference schools page"""
    url = "https://www.sports-reference.com/cbb/schools/"
    
    print(f"Fetching {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all team links - they're in <a> tags with href="/cbb/schools/.../men/"
    team_mappings = {}
    team_links = soup.find_all('a', href=re.compile(r'/cbb/schools/[^/]+/men/'))
    
    print(f"Found {len(team_links)} team links")
    
    for link in team_links:
        href = link.get('href', '')
        team_name = link.get_text().strip()
        slug = extract_team_slug_from_url(href)
        
        if slug and team_name:
            # Store the primary mapping (team name -> slug)
            team_mappings[team_name] = slug
            
            # Also create variations:
            # 1. Lowercase with spaces
            team_mappings[team_name.lower()] = slug
            
            # 2. Lowercase with underscores
            team_mappings[team_name.lower().replace(' ', '_')] = slug
            
            # 3. Lowercase with hyphens
            team_mappings[team_name.lower().replace(' ', '-')] = slug
            
            # 4. Normalized name (for fuzzy matching)
            normalized = normalize_team_name(team_name)
            if normalized and normalized != team_name.lower():
                team_mappings[normalized] = slug
            
            # 5. Common abbreviations and variations
            if 'Michigan St.' in team_name or 'Michigan State' in team_name:
                team_mappings['michigan_state'] = slug
                team_mappings['michigan-state'] = slug
                team_mappings['michigan state'] = slug
                team_mappings['michigan st'] = slug
                team_mappings['michigan st.'] = slug
            if 'Ohio St.' in team_name or 'Ohio State' in team_name:
                team_mappings['ohio_state'] = slug
                team_mappings['ohio-state'] = slug
                team_mappings['ohio state'] = slug
                team_mappings['ohio st'] = slug
                team_mappings['ohio st.'] = slug
            if 'Penn St.' in team_name or 'Penn State' in team_name:
                team_mappings['penn_state'] = slug
                team_mappings['penn-state'] = slug
                team_mappings['penn state'] = slug
                team_mappings['penn st'] = slug
                team_mappings['penn st.'] = slug
            if 'Iowa St.' in team_name or 'Iowa State' in team_name:
                team_mappings['iowa_state'] = slug
                team_mappings['iowa-state'] = slug
                team_mappings['iowa state'] = slug
                team_mappings['iowa st'] = slug
                team_mappings['iowa st.'] = slug
            if 'Southern California' in team_name or 'USC' in team_name:
                team_mappings['usc'] = slug
                team_mappings['southern california'] = slug
                team_mappings['southern-california'] = slug
                team_mappings['southern_california'] = slug
            if 'UConn' in team_name or 'Connecticut' in team_name:
                team_mappings['uconn'] = slug
                team_mappings['connecticut'] = slug
            if 'LSU' in team_name or 'Louisiana State' in team_name:
                team_mappings['lsu'] = slug
                team_mappings['louisiana state'] = slug
                team_mappings['louisiana-state'] = slug
                team_mappings['louisiana_state'] = slug
            if 'BYU' in team_name or 'Brigham Young' in team_name:
                team_mappings['byu'] = slug
                team_mappings['brigham young'] = slug
                team_mappings['brigham-young'] = slug
                team_mappings['brigham_young'] = slug
            if 'North Carolina' in team_name and 'State' not in team_name:
                team_mappings['unc'] = slug
                team_mappings['north carolina'] = slug
                team_mappings['north-carolina'] = slug
                team_mappings['north_carolina'] = slug
            if 'NC State' in team_name or 'North Carolina State' in team_name:
                team_mappings['nc state'] = slug
                team_mappings['nc-state'] = slug
                team_mappings['nc_state'] = slug
                team_mappings['north carolina state'] = slug
                team_mappings['north-carolina-state'] = slug
                team_mappings['north_carolina_state'] = slug
    
    # Remove duplicates and sort
    unique_mappings = {}
    for key in sorted(team_mappings.keys()):
        unique_mappings[key] = team_mappings[key]
    
    print(f"Generated {len(unique_mappings)} mapping entries")
    return unique_mappings

def main():
    """Main function to generate and save the mapping"""
    print("=" * 60)
    print("Sports Reference Team Slug Mapping Generator")
    print("=" * 60)
    
    mappings = scrape_sports_ref_teams()
    
    if not mappings:
        print("Failed to generate mappings")
        return
    
    # Create the output structure
    output = {
        "team_slug_mapping": mappings,
        "notes": "Auto-generated mapping from Sports Reference. Maps various team name formats to the correct Sports Reference slug. Generated by scraping the schools index page.",
        "generated_count": len(mappings),
        "source": "https://www.sports-reference.com/cbb/schools/"
    }
    
    # Save to file
    import os
    output_file = os.path.join(os.path.dirname(__file__), '..', 'mappings', 'sports_ref_team_mapping.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Mapping saved to {output_file}")
    print(f"   Total mappings: {len(mappings)}")
    
    # Show some examples
    print("\nExample mappings:")
    example_keys = list(mappings.keys())[:10]
    for key in example_keys:
        print(f"   '{key}' -> '{mappings[key]}'")
    
    # Check for common teams
    print("\nCommon team checks:")
    common_teams = {
        'michigan-state': 'Michigan State',
        'michigan_state': 'Michigan State (underscore)',
        'michigan state': 'Michigan State (space)',
        'oregon': 'Oregon',
        'ucla': 'UCLA',
        'usc': 'USC',
        'southern-california': 'Southern California',
        'ohio-state': 'Ohio State',
        'ohio_state': 'Ohio State (underscore)',
        'uconn': 'UConn',
        'connecticut': 'Connecticut',
        'nc-state': 'NC State',
        'north-carolina': 'North Carolina'
    }
    
    for slug, description in common_teams.items():
        if slug in mappings:
            print(f"   ✅ {description}: {slug} -> {mappings[slug]}")
        else:
            print(f"   ❌ {description}: {slug} not found")

if __name__ == "__main__":
    main()

