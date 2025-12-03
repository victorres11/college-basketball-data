#!/usr/bin/env python3
"""
Test script for Bart Torvik teamsheets scraper
"""
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from barttorvik_teamsheets import get_teamsheets_data_structured


def test_big_ten_2026():
    """Test fetching Big Ten data for 2026"""
    print("=" * 60)
    print("Testing Bart Torvik Teamsheets Scraper")
    print("=" * 60)
    print("\nFetching Big Ten teamsheets data for 2026...\n")
    
    try:
        data = get_teamsheets_data_structured(year=2026, conference='B10', sort=8)
        
        print(f"✅ Successfully retrieved {len(data)} teams\n")
        
        # Display first few teams
        print("Sample data (first 3 teams):")
        print("-" * 60)
        for i, team in enumerate(data[:3]):
            print(f"\n{i+1}. {team.get('team')} (Rank: {team.get('rank')})")
            print(f"   Resume: NET={team.get('resume', {}).get('net')}, "
                  f"KPI={team.get('resume', {}).get('kpi')}, "
                  f"Avg={team.get('resume', {}).get('avg')}")
            print(f"   Quality: BPI={team.get('quality', {}).get('bpi')}, "
                  f"KenPom={team.get('quality', {}).get('kenpom')}, "
                  f"Avg={team.get('quality', {}).get('avg')}")
            print(f"   Quadrants: Q1={team.get('quadrants', {}).get('q1', {}).get('record')}, "
                  f"Q2={team.get('quadrants', {}).get('q2', {}).get('record')}, "
                  f"Q3={team.get('quadrants', {}).get('q3', {}).get('record')}, "
                  f"Q4={team.get('quadrants', {}).get('q4', {}).get('record')}")
        
        # Save full data to test_data directory
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'test_data')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'barttorvik_test_results.json')
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✅ Full data saved to: {output_file}")
        print(f"   Total teams: {len(data)}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    test_big_ten_2026()

