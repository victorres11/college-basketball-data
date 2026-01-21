#!/usr/bin/env python3
"""
Script to extract team sheets data from barttorvik.com
"""
import subprocess
import sys
import os

try:
    from playwright.sync_api import sync_playwright
    USE_PLAYWRIGHT = True
except ImportError as e:
    USE_PLAYWRIGHT = False
    try:
        import cloudscraper
        USE_CLOUDSCRAPER = True
        print(f"[BARTTORVIK] Warning: playwright not available ({e}), using cloudscraper as fallback")
    except ImportError:
        import requests
        USE_CLOUDSCRAPER = False
        print(f"[BARTTORVIK] Warning: playwright and cloudscraper not available, using requests (may not work with bot protection)")
        print(f"[BARTTORVIK] ImportError details: {e}")

from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# S3 cache configuration
S3_CACHE_URL = "https://cbb-data-files.s3.us-east-1.amazonaws.com/cache/barttorvik_teamsheets_{year}.json"
CACHE_MAX_AGE_HOURS = 24  # Consider cache stale after 24 hours


def get_cached_teamsheets_from_s3(year: int = 2026) -> Optional[List[Dict]]:
    """
    Fetch cached teamsheets data from S3 (uploaded by Raspberry Pi).

    Args:
        year: Season year

    Returns:
        List of team dictionaries if cache is valid, None otherwise
    """
    if not REQUESTS_AVAILABLE:
        print("[BARTTORVIK] requests not available, cannot fetch S3 cache")
        return None

    cache_url = S3_CACHE_URL.format(year=year)

    try:
        print(f"[BARTTORVIK] Checking S3 cache: {cache_url}")
        response = requests.get(cache_url, timeout=10)

        if response.status_code == 404:
            print("[BARTTORVIK] S3 cache not found (404)")
            return None

        response.raise_for_status()
        cache_data = response.json()

        # Check cache age
        fetched_at_str = cache_data.get('fetched_at')
        if fetched_at_str:
            try:
                fetched_at = datetime.fromisoformat(fetched_at_str.replace('Z', '+00:00'))
                age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600

                if age_hours > CACHE_MAX_AGE_HOURS:
                    print(f"[BARTTORVIK] S3 cache is stale ({age_hours:.1f} hours old)")
                    return None

                print(f"[BARTTORVIK] S3 cache is fresh ({age_hours:.1f} hours old)")
            except Exception as e:
                print(f"[BARTTORVIK] Could not parse cache timestamp: {e}")

        teams = cache_data.get('teams', [])
        if teams:
            print(f"[BARTTORVIK] Loaded {len(teams)} teams from S3 cache")
            return teams

        print("[BARTTORVIK] S3 cache has no teams data")
        return None

    except requests.exceptions.Timeout:
        print("[BARTTORVIK] S3 cache request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[BARTTORVIK] S3 cache request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[BARTTORVIK] S3 cache JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[BARTTORVIK] S3 cache error: {e}")
        return None


def ensure_playwright_browsers():
    """
    Ensure Playwright browsers are installed at runtime.
    This is necessary for Render.com where browsers may not persist from build.
    """
    if not USE_PLAYWRIGHT:
        return False
    
    # Check if browsers exist by checking the file system (more reliable than launching)
    browsers_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '/opt/render/project/playwright')
    
    # Check if any chromium browser exists
    import glob
    existing_browsers = glob.glob(os.path.join(browsers_path, 'chromium*', 'chrome-linux', 'headless_shell'))
    
    if existing_browsers:
        print(f"[BARTTORVIK] Playwright browsers found at {existing_browsers[0]}")
        return True
    
    # Browsers not found, install them (without --with-deps since system deps are in build)
    print("[BARTTORVIK] Playwright browsers not found, installing at runtime...")
    try:
        # Set browsers path to persistent location if on Render
        if os.path.exists('/opt/render'):
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path
            os.makedirs(browsers_path, exist_ok=True)
        
        # Install browsers WITHOUT --with-deps (system deps already installed in build)
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        print("[BARTTORVIK] Playwright browsers installed successfully")
        return True
    except subprocess.TimeoutExpired:
        print("[BARTTORVIK] Browser installation timed out")
        return False
    except subprocess.CalledProcessError as install_error:
        print(f"[BARTTORVIK] Failed to install browsers: {install_error.stderr}")
        return False
    except Exception as install_error:
        print(f"[BARTTORVIK] Error installing browsers: {install_error}")
        return False


# Team name mapping for special cases where fuzzy matching fails
# Keys must be lowercase
BARTTORVIK_TEAM_MAPPING = {
    # Ole Miss
    'ole miss': 'Mississippi',
    'mississippi rebels': 'Mississippi',
    # Miami schools (parentheses vs space)
    'miami(fl)': 'Miami FL',
    'miami fl': 'Miami FL',
    'miami (fl)': 'Miami FL',
    'miami(oh)': 'Miami OH',
    'miami oh': 'Miami OH',
    'miami (oh)': 'Miami OH',
    # UConn
    'uconn': 'Connecticut',
    'connecticut huskies': 'Connecticut',
    # Hawaii (apostrophe variations)
    "hawai'i": 'Hawaii',
    'hawai`i': 'Hawaii',
    # UIC
    'uic': 'Illinois Chicago',
    'illinois-chicago': 'Illinois Chicago',
    # FDU
    'fdu': 'Fairleigh Dickinson',
    # Gardner-Webb (hyphen variations)
    'gardner-webb': 'Gardner Webb',
    # Bethune-Cookman (hyphen variations)
    'bethune-cookman': 'Bethune Cookman',
    # St. Francis (parentheses variations) - barttorvik uses "Saint Francis"
    'st. francis(pa)': 'Saint Francis',
    'st francis(pa)': 'Saint Francis',
    'st. francis (pa)': 'Saint Francis',
    'saint francis(pa)': 'Saint Francis',
}


def normalize_team_name(team_name: str) -> str:
    """
    Normalize team name for matching (remove common suffixes, lowercase, etc.)
    
    Args:
        team_name: Team name to normalize
    
    Returns:
        Normalized team name
    """
    # Remove common suffixes and clean up
    name = team_name.strip()
    # Remove seed numbers if present (e.g., "UCLA8" -> "UCLA")
    name = re.sub(r'\d+$', '', name).strip()
    # Remove trailing periods
    name = name.rstrip('.')
    # Normalize abbreviations
    name = re.sub(r'\bSt\.?\b', 'State', name, flags=re.IGNORECASE)
    name = re.sub(r'\bUniv\.?\b', 'University', name, flags=re.IGNORECASE)
    # Only remove "University" suffix, not "State" (as it's part of team names like "Michigan State")
    name = re.sub(r'\s+University$', '', name, flags=re.IGNORECASE)
    # Normalize to lowercase for comparison
    return name.lower().strip()


def get_teamsheets_data(year: int = 2026, conference: Optional[str] = None, sort: int = 8) -> List[Dict]:
    """
    Fetch and parse teamsheets data from barttorvik.com
    
    Args:
        year: Season year (default: 2026)
        conference: Conference filter (e.g., 'B10' for Big Ten, 'All' for all teams, None for all)
        sort: Sort column (default: 8, which appears to be Avg)
    
    Returns:
        list: List of dictionaries with team data
    """
    # Build URL
    url = f"https://barttorvik.com/teamsheets.php?sort={sort}&year={year}"
    if conference:
        url += f"&conlimit={conference}"
    else:
        # Default to "All" if no conference specified
        url += "&conlimit=All"
    
    try:
        if USE_PLAYWRIGHT:
            # Ensure browsers are installed (runtime check for Render.com)
            ensure_playwright_browsers()

            # Use Playwright to handle JavaScript rendering
            # Barttorvik uses Cloudflare protection, so we need to wait for the challenge to complete
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                    ]
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    java_script_enabled=True,
                )
                page = context.new_page()

                # Navigate and wait for Cloudflare challenge to complete
                print(f"[BARTTORVIK] Navigating to {url}")
                page.goto(url, wait_until='domcontentloaded', timeout=60000)

                # Wait for Cloudflare challenge to complete (look for table or timeout)
                max_wait_time = 45000  # 45 seconds max for Cloudflare
                try:
                    # First, wait for any "Verifying" message to disappear
                    page.wait_for_function(
                        "document.body && !document.body.innerText.includes('Verifying')",
                        timeout=max_wait_time
                    )
                    print("[BARTTORVIK] Cloudflare verification completed")
                except Exception as cf_err:
                    print(f"[BARTTORVIK] Cloudflare wait note: {cf_err}")

                # Now wait for the actual table
                try:
                    page.wait_for_selector('table', timeout=15000)
                    # Small wait for any final rendering
                    page.wait_for_timeout(1000)
                    print("[BARTTORVIK] Table found on page")
                except Exception as table_err:
                    # Log page content for debugging
                    body_text = page.evaluate("document.body.innerText.substring(0, 500)")
                    print(f"[BARTTORVIK] Table not found. Page content preview: {body_text}")
                    print(f"[BARTTORVIK] Table wait error: {table_err}")

                html_content = page.content()
                browser.close()
            soup = BeautifulSoup(html_content, 'html.parser')
        else:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            if USE_CLOUDSCRAPER:
                scraper = cloudscraper.create_scraper()
                response = scraper.get(url, headers=headers, timeout=30)
            else:
                response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        raise Exception(f"Failed to fetch data from barttorvik.com: {e}")
    
    # Find the main table
    table = soup.find('table')
    if not table:
        # Try alternative selectors
        table = soup.find('table', class_=lambda x: x and 'table' in str(x).lower())
        if not table:
            raise Exception("Could not find data table on page")
    
    # Extract header row - may need to skip some rows if there are merged headers
    header_rows = table.find_all('tr')
    if not header_rows:
        raise Exception("Could not find header rows")
    
    # Find the actual header row (usually the last row with th elements before data)
    header_row = None
    for row in header_rows:
        ths = row.find_all('th')
        if len(ths) > 5:  # Should have multiple columns
            header_row = row
            break
    
    if not header_row:
        # Fallback to first row
        header_row = header_rows[0]
    
    headers = []
    for th in header_row.find_all(['th', 'td']):
        header_text = th.get_text(strip=True)
        # Clean up header text
        header_text = re.sub(r'\s+', ' ', header_text)
        headers.append(header_text)
    
    # Extract data rows (skip header rows)
    teams_data = []
    data_started = False
    for row in table.find_all('tr'):
        # Skip until we find the header row
        if row == header_row:
            data_started = True
            continue
        if not data_started:
            continue
        
        cols = row.find_all(['td', 'th'])
        if len(cols) < 10:  # Need at least 10 columns for valid data
            continue
        
        team_data = {}
        
        # Parse each column by position and header
        # Expected columns: Rk, Team, NET, KPI, SOR, WAB, Avg (Resume), BPI, KP, TRK, Avg (Quality), Q1A, Q1, Q2, Q1&2, Q3, Q4
        for i, col in enumerate(cols):
            if i >= len(headers):
                break
            
            header = headers[i] if i < len(headers) else ''
            value = col.get_text(strip=True)
            
            # Clean up value
            value = re.sub(r'\s+', ' ', value)
            
            # Parse by position (more reliable than header matching)
            if i == 0:  # Rk
                team_data['rank'] = int(value) if value.isdigit() else value
            elif i == 1:  # Team
                # Extract team name from <a> tag and seed from <span> tag
                team_link = col.find('a')
                if team_link:
                    team_name = team_link.get_text(strip=True)
                    team_data['team'] = team_name
                else:
                    # Fallback to all text if no link found
                    team_data['team'] = value
                
                # Extract seed from span with class containing "bub" or "tooltipstered"
                seed_span = col.find('span', class_=lambda x: x and ('bub' in str(x) or 'tooltipstered' in str(x)))
                if seed_span:
                    seed_text = seed_span.get_text(strip=True)
                    try:
                        team_data['seed'] = int(seed_text)
                    except:
                        team_data['seed'] = seed_text
                else:
                    # Try to extract seed from any span in the cell
                    all_spans = col.find_all('span')
                    for span in all_spans:
                        span_text = span.get_text(strip=True)
                        if span_text.isdigit():
                            team_data['seed'] = int(span_text)
                            break
            elif i == 2:  # NET
                team_data['net'] = int(value) if value.isdigit() else value
            elif i == 3:  # KPI
                team_data['kpi'] = int(value) if value.isdigit() else value
            elif i == 4:  # SOR
                team_data['sor'] = int(value) if value.isdigit() else value
            elif i == 5:  # WAB
                team_data['wab'] = int(value) if value.isdigit() else value
            elif i == 6:  # Avg (Resume)
                try:
                    team_data['resume_avg'] = float(value)
                except:
                    team_data['resume_avg'] = value
            elif i == 7:  # BPI
                team_data['bpi'] = int(value) if value.isdigit() else value
            elif i == 8:  # KP (KenPom)
                team_data['kenpom'] = int(value) if value.isdigit() else value
            elif i == 9:  # TRK
                team_data['trk'] = int(value) if value.isdigit() else value
            elif i == 10:  # Avg (Quality)
                try:
                    team_data['quality_avg'] = float(value)
                except:
                    team_data['quality_avg'] = value
            elif i == 11:  # Q1A
                team_data['q1a'] = value
            elif i == 12:  # Q1
                team_data['q1'] = value
            elif i == 13:  # Q2
                team_data['q2'] = value
            elif i == 14:  # Q1&2
                team_data['q1_and_q2'] = value
            elif i == 15:  # Q3
                team_data['q3'] = value
            elif i == 16:  # Q4
                team_data['q4'] = value
            else:
                # Store unknown columns
                field_name = header.lower().replace(' ', '_').replace('&', 'and') if header else f'col_{i}'
                team_data[field_name] = value
        
        if team_data and 'team' in team_data:
            teams_data.append(team_data)
    
    return teams_data


def parse_quadrant_record(record_str: str) -> Dict[str, int]:
    """
    Parse a quadrant record string like "1-0" or "0-2" into wins and losses
    
    Args:
        record_str: Record string in W-L format
    
    Returns:
        dict: {'wins': int, 'losses': int}
    """
    if not record_str or '-' not in record_str:
        return {'wins': 0, 'losses': 0}
    
    try:
        parts = record_str.split('-')
        wins = int(parts[0].strip())
        losses = int(parts[1].strip())
        return {'wins': wins, 'losses': losses}
    except:
        return {'wins': 0, 'losses': 0}


def get_teamsheets_data_structured(year: int = 2026, conference: Optional[str] = None, sort: int = 8) -> List[Dict]:
    """
    Fetch and parse teamsheets data with structured quadrant records
    
    Args:
        year: Season year (default: 2026)
        conference: Conference filter (e.g., 'B10' for Big Ten, None for all)
        sort: Sort column (default: 8)
    
    Returns:
        list: List of dictionaries with structured team data
    """
    raw_data = get_teamsheets_data(year, conference, sort)
    
    structured_data = []
    for team in raw_data:
        structured_team = {
            'rank': team.get('rank'),
            'team': team.get('team'),
            'seed': team.get('seed'),
            'resume': {
                'net': team.get('net'),
                'kpi': team.get('kpi'),
                'sor': team.get('sor'),
                'wab': team.get('wab'),
                'avg': team.get('resume_avg')
            },
            'quality': {
                'bpi': team.get('bpi'),
                'kenpom': team.get('kenpom'),
                'trk': team.get('trk'),
                'avg': team.get('quality_avg')
            },
            'quadrants': {}
        }
        
        # Parse quadrant records
        for quad_key in ['q1a', 'q1', 'q2', 'q1_and_q2', 'q3', 'q4']:
            if quad_key in team:
                record_str = team[quad_key]
                parsed = parse_quadrant_record(record_str)
                structured_team['quadrants'][quad_key] = {
                    'record': record_str,
                    **parsed
                }
        
        structured_data.append(structured_team)
    
    return structured_data


def get_team_teamsheet_data(team_name: str, year: int = 2026, sort: int = 8, use_cache: bool = True) -> Optional[Dict]:
    """
    Fetch teamsheet data for a specific team from barttorvik.com.

    First checks S3 cache (populated by Raspberry Pi), then falls back to
    direct scraping if cache is unavailable or stale.

    Args:
        team_name: Team name to fetch (e.g., "UCLA", "Oregon", "Michigan State")
        year: Season year (default: 2026)
        sort: Sort column (default: 8)
        use_cache: Whether to try S3 cache first (default: True)

    Returns:
        Dictionary with structured team data, or None if team not found
    """
    all_teams = None

    # Try S3 cache first (from Raspberry Pi)
    if use_cache:
        all_teams = get_cached_teamsheets_from_s3(year=year)

    # Fall back to direct scraping if cache unavailable
    if all_teams is None:
        print("[BARTTORVIK] Falling back to direct scraping...")
        all_teams = get_teamsheets_data_structured(year=year, conference='All', sort=sort)

    # Check if team name has a direct mapping
    team_name_lower = team_name.lower()
    if team_name_lower in BARTTORVIK_TEAM_MAPPING:
        team_name = BARTTORVIK_TEAM_MAPPING[team_name_lower]

    # Normalize the search team name
    normalized_search = normalize_team_name(team_name)
    
    # Track potential matches with scores
    matches = []
    
    for team in all_teams:
        team_name_from_data = team.get('team', '')
        normalized_team = normalize_team_name(team_name_from_data)
        score = 0
        
        # Exact match gets highest score
        if normalized_search == normalized_team:
            return team
        
        # Check if search name is contained in team name (prefer longer matches)
        if normalized_search in normalized_team:
            # Prefer matches where lengths are closer
            length_ratio = len(normalized_search) / len(normalized_team) if normalized_team else 0
            score = 100 + length_ratio * 50
            matches.append((score, team))
        # Check if team name is contained in search name
        elif normalized_team in normalized_search:
            # Prefer matches where lengths are closer
            length_ratio = len(normalized_team) / len(normalized_search) if normalized_search else 0
            score = 80 + length_ratio * 50
            matches.append((score, team))
        else:
            # Try word-based matching
            search_words = set(normalized_search.split())
            team_words = set(normalized_team.split())
            
            if search_words and team_words:
                common_words = search_words.intersection(team_words)
                if common_words:
                    # Calculate match ratio
                    match_ratio = len(common_words) / max(len(search_words), len(team_words))
                    # Prefer matches where all words match
                    if len(common_words) == len(search_words) == len(team_words):
                        score = 90
                    else:
                        score = match_ratio * 70
                    matches.append((score, team))
    
    # Return the best match if any found
    if matches:
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1]
    
    return None


if __name__ == '__main__':
    # Test with Big Ten data
    print("Fetching Big Ten teamsheets data for 2026...\n")
    try:
        data = get_teamsheets_data_structured(year=2026, conference='B10', sort=8)
        print(json.dumps(data, indent=2))
        print(f"\n✅ Successfully retrieved {len(data)} teams")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

