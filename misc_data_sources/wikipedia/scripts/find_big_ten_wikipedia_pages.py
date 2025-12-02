#!/usr/bin/env python3
"""
Script to find Wikipedia pages for all 18 Big Ten teams.
Tests that we can locate each team's primary Wikipedia page.
"""
import sys
import os
import requests
import json
from pathlib import Path

# Add parent directory to path to import wikipedia_data
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wikipedia_data import get_wikitext, extract_infobox_template

# Big Ten teams - mapping team names to potential Wikipedia page titles
BIG_TEN_TEAMS = {
    'Illinois': ['Illinois_Fighting_Illini_men\'s_basketball', 'Illinois_Fighting_Illini'],
    'Indiana': ['Indiana_Hoosiers_men\'s_basketball', 'Indiana_Hoosiers'],
    'Iowa': ['Iowa_Hawkeyes_men\'s_basketball', 'Iowa_Hawkeyes'],
    'Maryland': ['Maryland_Terrapins_men\'s_basketball', 'Maryland_Terrapins'],
    'Michigan State': ['Michigan_State_Spartans_men\'s_basketball', 'Michigan_State_Spartans'],
    'Michigan': ['Michigan_Wolverines_men\'s_basketball', 'Michigan_Wolverines'],
    'Minnesota': ['Minnesota_Golden_Gophers_men\'s_basketball', 'Minnesota_Golden_Gophers'],
    'Nebraska': ['Nebraska_Cornhuskers_men\'s_basketball', 'Nebraska_Cornhuskers'],
    'Northwestern': ['Northwestern_Wildcats_men\'s_basketball', 'Northwestern_Wildcats'],
    'Ohio State': ['Ohio_State_Buckeyes_men\'s_basketball', 'Ohio_State_Buckeyes'],
    'Oregon': ['Oregon_Ducks_men\'s_basketball', 'Oregon_Ducks'],
    'Penn State': ['Penn_State_Nittany_Lions_men\'s_basketball', 'Penn_State_Nittany_Lions'],
    'Purdue': ['Purdue_Boilermakers_men\'s_basketball', 'Purdue_Boilermakers'],
    'Rutgers': ['Rutgers_Scarlet_Knights_men\'s_basketball', 'Rutgers_Scarlet_Knights'],
    'UCLA': ['UCLA_Bruins_men\'s_basketball', 'UCLA_Bruins'],
    'USC': ['USC_Trojans_men\'s_basketball', 'USC_Trojans'],
    'Washington': ['Washington_Huskies_men\'s_basketball', 'Washington_Huskies'],
    'Wisconsin': ['Wisconsin_Badgers_men\'s_basketball', 'Wisconsin_Badgers']
}

# MediaWiki API endpoint
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

# Wikipedia requires a User-Agent header
HEADERS = {
    'User-Agent': 'CollegeBasketballDataBot/1.0 (https://github.com/yourusername/cbbd; contact@example.com)'
}


def search_wikipedia_page(team_name: str, potential_titles: list) -> dict:
    """
    Search for a team's Wikipedia page by trying potential titles.
    
    Args:
        team_name: The team name
        potential_titles: List of potential Wikipedia page titles to try
    
    Returns:
        Dictionary with search results
    """
    result = {
        'team_name': team_name,
        'found': False,
        'page_title': None,
        'url': None,
        'has_infobox': False,
        'tried_titles': []
    }
    
    for title in potential_titles:
        result['tried_titles'].append(title)
        
        # Try to get the page
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'titles': title,
                'prop': 'info',
                'formatversion': '2'
            }
            
            response = requests.get(WIKIPEDIA_API_URL, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', [])
            if pages and 'missing' not in pages[0]:
                # Page exists!
                page_id = pages[0].get('pageid')
                normalized_title = pages[0].get('title', title)
                
                # Check if it has an infobox
                wikitext = get_wikitext(normalized_title)
                has_infobox = extract_infobox_template(wikitext) is not None if wikitext else False
                
                result['found'] = True
                result['page_title'] = normalized_title
                result['url'] = f"https://en.wikipedia.org/wiki/{normalized_title.replace(' ', '_')}"
                result['has_infobox'] = has_infobox
                break
        
        except Exception as e:
            # Try next title
            continue
    
    return result


def main():
    """Find Wikipedia pages for all 18 Big Ten teams."""
    print("Finding Wikipedia Pages for All 18 Big Ten Teams")
    print("=" * 70)
    
    results = []
    
    for team_name, potential_titles in BIG_TEN_TEAMS.items():
        print(f"\nSearching for: {team_name}")
        result = search_wikipedia_page(team_name, potential_titles)
        results.append(result)
        
        if result['found']:
            status = "✓" if result['has_infobox'] else "⚠"
            print(f"  {status} Found: {result['page_title']}")
            print(f"    URL: {result['url']}")
            print(f"    Has infobox: {result['has_infobox']}")
        else:
            print(f"  ✗ Not found")
            print(f"    Tried: {', '.join(result['tried_titles'])}")
    
    # Summary
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    
    found = [r for r in results if r['found']]
    with_infobox = [r for r in results if r['found'] and r['has_infobox']]
    
    print(f"Teams found: {len(found)}/18")
    print(f"Teams with infobox: {len(with_infobox)}/18")
    print(f"Teams not found: {18 - len(found)}/18")
    
    if len(found) < 18:
        print(f"\nTeams not found:")
        for r in results:
            if not r['found']:
                print(f"  - {r['team_name']}")
    
    if len(with_infobox) < 18:
        print(f"\nTeams found but without infobox:")
        for r in results:
            if r['found'] and not r['has_infobox']:
                print(f"  - {r['team_name']}: {r['page_title']}")
    
    # Save results
    output_dir = Path(__file__).parent.parent / 'test_data'
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'big_ten_wikipedia_pages.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total': 18,
                'found': len(found),
                'with_infobox': len(with_infobox),
                'not_found': 18 - len(found)
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # Print all found pages
    print(f"\n{'='*70}")
    print("ALL FOUND WIKIPEDIA PAGES")
    print('='*70)
    for r in sorted(results, key=lambda x: x['team_name']):
        if r['found']:
            print(f"{r['team_name']:20} -> {r['page_title']}")
            print(f"{'':20}    {r['url']}")


if __name__ == '__main__':
    main()

