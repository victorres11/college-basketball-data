#!/usr/bin/env python3
"""
Test script to extract quadrant wins data from bballnet.com for all Big Ten teams
"""
import requests
from bs4 import BeautifulSoup
import json
import time

# Big Ten teams with their bballnet.com slugs
# Note: These slugs may need adjustment based on actual bballnet.com URLs
BIG_TEN_TEAMS = {
    'illinois': 'illinois',
    'indiana': 'indiana',
    'iowa': 'iowa',
    'maryland': 'maryland',
    'michigan-state': 'michigan-state',
    'michigan': 'michigan',
    'minnesota': 'minnesota',
    'nebraska': 'nebraska',
    'northwestern': 'northwestern',
    'ohio-state': 'ohio-state',
    'oregon': 'oregon',
    'penn-state': 'penn-state',
    'purdue': 'purdue',
    'rutgers': 'rutgers',
    'ucla': 'ucla',
    'usc': 'usc',
    'washington': 'washington',
    'wisconsin': 'wisconsin'
}

def get_quadrant_data(team_slug):
    """
    Fetch and parse quadrant data for a team
    
    Args:
        team_slug: Team identifier (e.g., 'oregon')
    
    Returns:
        dict: Quadrant data including wins/losses, or None if error
    """
    url = f"https://bballnet.com/teams/{team_slug}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
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
        
        # Find all quad sections - try multiple possible selectors
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
            
            # Get games/opponents
            opponents = []
            games = []
            table = quad.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header row
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        result = cols[0].text.strip()
                        score = cols[1].text.strip()
                        location = cols[2].text.strip()
                        opponent_cell = cols[3]
                        opponent_link = opponent_cell.find('a')
                        opponent = opponent_link.text.strip() if opponent_link else opponent_cell.text.strip()
                        
                        opponents.append(opponent.lower().replace(' ', '_'))
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
        
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Request failed for {team_slug}: {e}")
        return None
    except Exception as e:
        print(f"  ERROR: Parsing failed for {team_slug}: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_all_big_ten():
    """Test quadrant scraping for all Big Ten teams"""
    results = {
        'success': [],
        'failed': [],
        'partial': [],
        'detailed': {}
    }
    
    print("Testing quadrant data extraction for all Big Ten teams...")
    print("=" * 60)
    
    for team_name, team_slug in BIG_TEN_TEAMS.items():
        print(f"\nTesting {team_name} ({team_slug})...")
        data = get_quadrant_data(team_slug)
        
        if data is None:
            results['failed'].append(team_slug)
            continue
        
        results['detailed'][team_slug] = data
        
        # Check if we got quadrant data
        if data['quadrants']:
            quad_count = len(data['quadrants'])
            if quad_count == 4:
                results['success'].append(team_slug)
                print(f"  ✓ Success: Found {quad_count} quadrants")
                for quad_num in ['1', '2', '3', '4']:
                    quad_key = f'quad{quad_num}'
                    if quad_key in data['quadrants']:
                        quad_data = data['quadrants'][quad_key]
                        print(f"    Quad {quad_num}: {quad_data['record']} ({len(quad_data['opponents'])} opponents)")
            else:
                results['partial'].append((team_slug, quad_count))
                print(f"  ⚠ Partial: Found only {quad_count}/4 quadrants")
        else:
            results['failed'].append(team_slug)
            print(f"  ✗ Failed: No quadrant data found")
        
        # Be nice to the server
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Success: {len(results['success'])}/{len(BIG_TEN_TEAMS)}")
    print(f"Partial: {len(results['partial'])}/{len(BIG_TEN_TEAMS)}")
    print(f"Failed: {len(results['failed'])}/{len(BIG_TEN_TEAMS)}")
    
    if results['success']:
        print(f"\n✓ Successful teams: {', '.join(results['success'])}")
    if results['partial']:
        print(f"\n⚠ Partial teams: {', '.join([f'{t[0]} ({t[1]} quads)' for t in results['partial']])}")
    if results['failed']:
        print(f"\n✗ Failed teams: {', '.join(results['failed'])}")
    
    return results

if __name__ == '__main__':
    results = test_all_big_ten()
    
    # Save results to JSON
    import os
    output_file = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'quadrant_test_results.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_file}")

