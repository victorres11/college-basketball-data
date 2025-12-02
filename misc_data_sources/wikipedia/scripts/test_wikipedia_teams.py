#!/usr/bin/env python3
"""
Test script to extract Wikipedia infobox data for college basketball teams.
Tests with UCLA and several Big Ten teams.
"""
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import wikipedia_data
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wikipedia_data import get_wikipedia_team_data


# Test teams - Wikipedia page titles
TEST_TEAMS = [
    "UCLA_Bruins_men's_basketball",
    "Michigan_State_Spartans_men's_basketball",
    "Michigan_Wolverines_men's_basketball",
    "Indiana_Hoosiers_men's_basketball",
    "Ohio_State_Buckeyes_men's_basketball",
    "Purdue_Boilermakers_men's_basketball",
    "Wisconsin_Badgers_men's_basketball",
    "Illinois_Fighting_Illini_men's_basketball"
]


def test_team(page_title: str) -> dict:
    """
    Test extracting data for a single team.
    
    Args:
        page_title: Wikipedia page title
    
    Returns:
        Dictionary with test results
    """
    print(f"\n{'='*60}")
    print(f"Testing: {page_title}")
    print('='*60)
    
    try:
        data = get_wikipedia_team_data(page_title)
        
        print(f"✓ Successfully extracted data")
        print(f"\nKey Information:")
        print(f"  University: {data.get('university_name', 'N/A')}")
        print(f"  Head Coach: {data.get('head_coach', 'N/A')}")
        print(f"  Conference: {data.get('conference', 'N/A')}")
        print(f"  Arena: {data.get('arena', 'N/A')}")
        print(f"  Capacity: {data.get('capacity', 'N/A')}")
        print(f"  All-time Record: {data.get('all_time_record', 'N/A')}")
        
        if data.get('championships'):
            print(f"\nChampionships:")
            for key, value in data['championships'].items():
                if value:
                    print(f"  {key}: {value}")
        
        if data.get('tournament_appearances'):
            print(f"\nTournament Appearances:")
            for key, value in data['tournament_appearances'].items():
                if value:
                    print(f"  {key}: {value}")
        
        return {
            'page_title': page_title,
            'success': True,
            'data': data
        }
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return {
            'page_title': page_title,
            'success': False,
            'error': str(e)
        }


def main():
    """Run tests for all teams and save results."""
    print("Wikipedia Infobox Data Extraction Test")
    print("=" * 60)
    
    results = []
    
    for team in TEST_TEAMS:
        result = test_team(team)
        results.append(result)
    
    # Summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    successful = sum(1 for r in results if r['success'])
    print(f"Successful: {successful}/{len(results)}")
    print(f"Failed: {len(results) - successful}/{len(results)}")
    
    # Save results to JSON
    output_dir = Path(__file__).parent.parent / 'test_data'
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'wikipedia_test_results.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total': len(results),
                'successful': successful,
                'failed': len(results) - successful
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # Print failed teams
    failed = [r for r in results if not r['success']]
    if failed:
        print(f"\nFailed teams:")
        for r in failed:
            print(f"  - {r['page_title']}: {r.get('error', 'Unknown error')}")


if __name__ == '__main__':
    main()

