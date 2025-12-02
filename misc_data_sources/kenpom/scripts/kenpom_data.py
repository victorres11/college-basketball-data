#!/usr/bin/env python3
"""
Script to extract data from kenpom.com team pages (requires subscription/authentication)
"""
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time

# Credentials file for kenpom.com authentication
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'kenpom_credentials.json')

def load_credentials():
    """
    Load kenpom.com credentials from environment variables (production) or JSON file (local).
    
    Priority:
    1. Environment variables (KENPOM_USERNAME, KENPOM_PASSWORD) - for production
    2. JSON file (kenpom_credentials.json) - for local development
    
    Expected format in kenpom_credentials.json:
    {
        "username": "your_email@example.com",
        "password": "your_password"
    }
    
    OR (legacy format, still supported):
    {
        "cookies": {
            "PHPSESSID": "your_session_id"
        }
    }
    """
    # First, try environment variables (for production)
    username = os.environ.get('KENPOM_USERNAME')
    password = os.environ.get('KENPOM_PASSWORD')
    
    if username and password:
        # Strip whitespace in case there are accidental spaces
        username = username.strip()
        password = password.strip()
        
        if not username or not password:
            print("[KENPOM] WARNING: Environment variables found but are empty after stripping whitespace")
        else:
            print(f"[KENPOM] Using credentials from environment variables (username: {username[:3]}***)")
            return {
                'username': username,
                'password': password
            }
    elif username or password:
        # One is set but not both
        print("[KENPOM] WARNING: Only one environment variable is set (both KENPOM_USERNAME and KENPOM_PASSWORD required)")
    
    # Fallback to JSON file (for local development)
    if os.path.exists(CREDENTIALS_FILE):
        print("[KENPOM] Using credentials from file")
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    
    return {}

def login_to_kenpom(session, username, password):
    """
    Log in to kenpom.com and establish a session.
    
    Args:
        session: requests.Session object
        username: KenPom username (email)
        password: KenPom password
    
    Returns:
        bool: True if login successful, False otherwise
    """
    login_submit_url = "https://kenpom.com/handlers/login_handler.php"
    
    try:
        # First, visit the main page to establish session and get cookies
        # This helps avoid 403 errors by making us look like a real browser
        main_page_url = "https://kenpom.com/"
        response = session.get(main_page_url, timeout=10)
        response.raise_for_status()
        
        # Small delay to mimic human behavior
        time.sleep(0.5)
        
        # Try to get the login page to see if there are any hidden form fields or CSRF tokens
        # Some sites protect index.php but allow login handler
        login_page_html = None
        try:
            login_page_url = "https://kenpom.com/index.php"
            login_page_response = session.get(login_page_url, timeout=10)
            if login_page_response.status_code == 200:
                login_page_html = login_page_response.text
                print(f"[KENPOM] Successfully loaded login page (index.php)")
                # Parse for any hidden form fields or CSRF tokens
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(login_page_html, 'html.parser')
                login_form = soup.find('form', {'action': lambda x: x and 'login' in x.lower()})
                if login_form:
                    print(f"[KENPOM] Found login form on page")
                    # Check for hidden fields
                    hidden_inputs = login_form.find_all('input', {'type': 'hidden'})
                    if hidden_inputs:
                        print(f"[KENPOM] Found {len(hidden_inputs)} hidden form fields")
            time.sleep(0.5)
        except requests.exceptions.HTTPError as e:
            # If index.php returns 403 or other error, that's okay - we'll try login handler directly
            if e.response.status_code == 403:
                print("[KENPOM] Note: index.php is protected (403), proceeding with login handler")
            pass
        except Exception as e:
            # Other errors are also okay - we'll try login handler directly
            print(f"[KENPOM] Note: Could not load login page: {e}")
            pass
        
        # Prepare login data - KenPom uses 'email', 'password', and 'submit' fields
        login_data = {
            'email': username,
            'password': password,
            'submit': 'Login!',  # Submit button value
            'remember': ''  # Optional remember checkbox
        }
        
        # Update headers for the POST request to be more browser-like
        # Don't override all headers, just update the ones needed for POST
        post_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://kenpom.com',
            'Referer': 'https://kenpom.com/index.php',  # More realistic - coming from login page
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Submit login form
        print(f"[KENPOM] Attempting login with username: {username[:3]}*** (hidden for security)")
        print(f"[KENPOM] Login URL: {login_submit_url}")
        print(f"[KENPOM] Session cookies before POST: {list(session.cookies.keys())}")
        
        login_response = session.post(
            login_submit_url, 
            data=login_data, 
            timeout=15,  # Increased timeout
            allow_redirects=False,  # Don't auto-follow redirects, handle manually
            headers=post_headers
        )
        
        # Handle redirects manually if needed
        if login_response.status_code in [301, 302, 303, 307, 308]:
            redirect_url = login_response.headers.get('Location', '')
            print(f"[KENPOM] Login returned redirect {login_response.status_code} to: {redirect_url}")
            if redirect_url:
                # Follow redirect manually
                if redirect_url.startswith('/'):
                    redirect_url = 'https://kenpom.com' + redirect_url
                login_response = session.get(redirect_url, timeout=15, allow_redirects=True)
        
        print(f"[KENPOM] Login response status: {login_response.status_code}")
        print(f"[KENPOM] Login response URL: {login_response.url}")
        print(f"[KENPOM] Cookies after login: {list(session.cookies.keys())}")
        print(f"[KENPOM] Response headers: {dict(login_response.headers)}")
        
        # If we got 403, the site is likely blocking us
        if login_response.status_code == 403:
            print(f"[KENPOM] ERROR: Received 403 Forbidden from login handler")
            print(f"[KENPOM] This typically means:")
            print(f"[KENPOM]   1. IP address is blocked/rate-limited by KenPom")
            print(f"[KENPOM]   2. Site is detecting automated requests")
            print(f"[KENPOM]   3. Login endpoint requires additional authentication")
            print(f"[KENPOM] Response text preview: {login_response.text[:500]}")
            return False
        
        # Check if login was successful
        # Successful login usually redirects or returns 200 with different content
        if login_response.status_code in [200, 302, 303]:
            # Check for error messages in response
            response_text = login_response.text.lower()
            print(f"[KENPOM] Response text length: {len(response_text)}")
            print(f"[KENPOM] Response preview (first 500 chars): {response_text[:500]}")
            
            if 'invalid' in response_text or 'incorrect' in response_text or 'error' in response_text:
                # Check if it's actually an error or just the word appearing elsewhere
                if 'invalid email' in response_text or 'invalid password' in response_text or 'login error' in response_text:
                    print(f"[KENPOM] Login failed: Invalid credentials detected in response")
                    return False
            
            # If we have cookies and we're not seeing error messages, verify by accessing a protected page
            if session.cookies:
                print(f"[KENPOM] Verifying login by accessing protected page...")
                # Try accessing a protected page to verify login worked
                test_response = session.get('https://kenpom.com/team.php?team=UCLA', timeout=10)
                print(f"[KENPOM] Test page status: {test_response.status_code}")
                print(f"[KENPOM] Test page URL: {test_response.url}")
                print(f"[KENPOM] Test page content length: {len(test_response.text)}")
                
                if test_response.status_code == 200:
                    # Check if we got actual content (not login page or error page)
                    if len(test_response.text) > 1000:  # Real pages are longer
                        # Check if we're not on a login/error page
                        test_text_lower = test_response.text.lower()
                        if 'login' not in test_response.url.lower() and 'sign-in' not in test_text_lower:
                            print(f"[KENPOM] Login successful!")
                            return True
                        else:
                            print(f"[KENPOM] Login failed: Redirected to login page")
                    else:
                        print(f"[KENPOM] Login failed: Response too short ({len(test_response.text)} chars)")
                else:
                    print(f"[KENPOM] Login failed: Test page returned status {test_response.status_code}")
            else:
                print(f"[KENPOM] Login failed: No cookies received")
        else:
            print(f"[KENPOM] Login failed: Unexpected status code {login_response.status_code}")
        
        return False
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"[KENPOM] Warning: Login attempt failed: 403 Forbidden")
            print(f"[KENPOM]   This may indicate:")
            print(f"[KENPOM]   - IP address is blocked by KenPom")
            print(f"[KENPOM]   - Site is detecting automated requests")
            print(f"[KENPOM]   - Login endpoint may have changed")
            print(f"[KENPOM]   Response URL: {e.response.url}")
            print(f"[KENPOM]   Response headers: {dict(e.response.headers)}")
        else:
            print(f"[KENPOM] Warning: Login attempt failed: HTTP {e.response.status_code}")
            print(f"[KENPOM]   Response URL: {e.response.url}")
        return False
    except Exception as e:
        print(f"[KENPOM] Warning: Login attempt failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_authenticated_session(credentials=None):
    """
    Create a requests session with kenpom.com authentication.
    Supports both username/password login and cookie-based auth.
    
    Args:
        credentials: Optional credentials dict (if None, loads from file)
    
    Returns:
        requests.Session: Authenticated session
    """
    if credentials is None:
        credentials = load_credentials()
    
    session = requests.Session()
    
    # Set headers to mimic a modern browser (updated User-Agent)
    # Note: requests automatically handles gzip/deflate decompression
    # Use a more recent Chrome user agent
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',  # requests handles decompression automatically
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'DNT': '1',  # Do Not Track
        'Referer': 'https://kenpom.com/'
    })
    
    # Try username/password login first (preferred method)
    if 'username' in credentials and 'password' in credentials:
        username = credentials['username']
        password = credentials['password']
        
        # Validate credentials are not empty
        if not username or not password:
            raise Exception("KenPom credentials are empty. Please set KENPOM_USERNAME and KENPOM_PASSWORD environment variables.")
        
        if login_to_kenpom(session, username, password):
            return session
        else:
            raise Exception("Login failed. Check your username and password. Verify KENPOM_USERNAME and KENPOM_PASSWORD are set correctly in Render.com environment variables.")
    # Fallback to cookie-based auth (legacy support)
    elif 'cookies' in credentials:
        session.cookies.update(credentials['cookies'])
        return session
    else:
        raise Exception("No credentials found. Provide either username/password or cookies in kenpom_credentials.json")
    
    return session

def extract_javascript_data(html):
    """
    Extract data from JavaScript code that populates the report-table.
    Many cells are populated via JavaScript with values and rankings.
    
    Args:
        html: HTML content as string
    
    Returns:
        dict: Extracted JavaScript data with keys for all cell IDs
    """
    import re
    js_data = {}
    
    # Extract simple text assignments (like effText, tempoText)
    text_pattern = r'\$\(["\']td#([A-Za-z0-9]+)["\']\)\.html\(["\']([^"\']+)["\']'
    text_matches = list(re.finditer(text_pattern, html))
    
    for match in text_matches:
        cell_id = match.group(1)
        value = match.group(2)
        # Store all matches, we'll use the last one (final value)
        if cell_id not in js_data:
            js_data[cell_id] = []
        js_data[cell_id].append(value)
    
    # Extract cells with links and rankings (format: <a>value</a> <span>ranking</span>)
    # Handle both simple format and span-wrapped format (like Tempo)
    # Pattern 1: Simple: <a>value</a> <span>ranking</span>
    ranking_pattern1 = r'\$\(["\']td#([A-Za-z0-9]+)["\']\)\.html\(["\'][^"\']*<a[^>]*>([\d.]+)</a>\s*<span[^>]*>(\d+)</span>'
    ranking_matches1 = list(re.finditer(ranking_pattern1, html))
    
    # Pattern 2: With span wrapper: <span...><a>value</a> <span>ranking</span></span>
    ranking_pattern2 = r'\$\(["\']td#([A-Za-z0-9]+)["\']\)\.html\(["\'][^"\']*<span[^>]*><a[^>]*>([\d.]+)</a>\s*<span[^>]*>(\d+)</span></span>'
    ranking_matches2 = list(re.finditer(ranking_pattern2, html))
    
    # Combine all matches - pattern2 takes precedence (more specific)
    all_ranking_matches = {}
    for match in ranking_matches1:
        cell_id = match.group(1)
        if cell_id not in all_ranking_matches:
            all_ranking_matches[cell_id] = []
        all_ranking_matches[cell_id].append((match.group(2), match.group(3)))
    
    # Overwrite with pattern2 matches (more specific, takes precedence)
    for match in ranking_matches2:
        cell_id = match.group(1)
        all_ranking_matches[cell_id] = [(match.group(2), match.group(3))]
    
    # Convert to the format we need
    ranking_matches = []
    for cell_id, values in all_ranking_matches.items():
        # Use the last value (final assignment)
        final_value, final_ranking = values[-1]
        ranking_matches.append((cell_id, final_value, final_ranking))
    
    for cell_id, value, ranking in ranking_matches:
        # Store all matches, we'll use the last one (final value)
        if cell_id not in js_data:
            js_data[cell_id] = []
        js_data[cell_id].append({'value': value, 'ranking': ranking})
    
    # For each cell ID, keep only the last assignment (final value)
    final_js_data = {}
    for cell_id, values in js_data.items():
        if values:
            final_js_data[cell_id] = values[-1]  # Last assignment is the final value
    
    return final_js_data

def normalize_team_slug(team_name_or_slug):
    """
    Normalize team name/slug for kenpom.com URL.
    
    KenPom uses team names in the URL, typically:
    - "UCLA" -> "UCLA"
    - "Michigan State" -> "Michigan St"
    - "Oregon" -> "Oregon"
    
    Args:
        team_name_or_slug: Team name or slug
    
    Returns:
        str: Normalized team name for URL
    """
    # KenPom typically uses the team name as-is, but with "State" -> "St"
    name = team_name_or_slug.strip()
    
    # Common mappings for KenPom
    kenpom_mappings = {
        'michigan state': 'Michigan St',
        'ohio state': 'Ohio St',
        'penn state': 'Penn St',
        'iowa state': 'Iowa St',
        'washington state': 'Washington St',
        'oregon state': 'Oregon St',
        'kansas state': 'Kansas St',
        'oklahoma state': 'Oklahoma St',
        'florida state': 'Florida St',
        'north carolina state': 'NC State',
        'nc state': 'NC State',
        'usc': 'Southern California',
        'southern california': 'Southern California',
    }
    
    name_lower = name.lower()
    if name_lower in kenpom_mappings:
        return kenpom_mappings[name_lower]
    
    # If it's already in a format like "UCLA", "Oregon", etc., use as-is
    # Capitalize first letter of each word
    return ' '.join(word.capitalize() for word in name.split())

def get_kenpom_team_data(team_slug):
    """
    Fetch and parse team data from kenpom.com.
    
    Args:
        team_slug: Team identifier (e.g., "UCLA", "Michigan State", "oregon")
    
    Returns:
        dict: Team data including:
            - team: Original team slug
            - team_name: Team name from page
            - url: URL accessed
            - data: Extracted data from page
            - html: Raw HTML (for debugging)
    """
    # Normalize team name for URL
    team_name = normalize_team_slug(team_slug)
    url = f"https://kenpom.com/team.php?team={team_name}"
    
    credentials = load_credentials()
    session = create_authenticated_session(credentials)
    
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        # Check if we got redirected to login or blocked
        if 'login' in response.url.lower() or 'sign-in' in response.url.lower():
            raise Exception(f"Authentication failed - redirected to login. Check credentials. Final URL: {response.url}")
        
        # Ensure response is properly decoded
        response_text = response.text
        if response.encoding is None:
            response.encoding = 'utf-8'
            response_text = response.text
        
        # Check for paywall indicators
        if 'subscription' in response_text.lower() and 'required' in response_text.lower():
            raise Exception("Page appears to be behind paywall. Verify your subscription is active and credentials are correct.")
        
        soup = BeautifulSoup(response_text, 'html.parser')
        
        # Extract team name from page
        # Team name is in the title-container div
        title_container = soup.find('div', id='title-container')
        team_name_found = team_name
        if title_container:
            # Look for the team name link (e.g., "Bruins")
            team_link = title_container.find('a', href=lambda x: x and 'roster.php' in x)
            if team_link:
                team_name_found = team_link.get_text(strip=True)
            else:
                # Fallback: extract from title
                title_elem = soup.find('title')
                if title_elem:
                    title_text = title_elem.get_text()
                    # Title format: "2026 scouting report for Ucla"
                    if 'for' in title_text:
                        team_name_found = title_text.split('for')[-1].strip()
        
        # Extract JavaScript-populated data first
        js_data = extract_javascript_data(response_text)
        
        # Extract data - KenPom pages have various tables and stats
        data = {
            'team_name': team_name_found,
            'url': url,
            'report_table': {},
            'schedule': [],
            'player_stats': []
        }
        
        # Find report-table (id='report-table')
        report_table = soup.find('table', id='report-table')
        
        if report_table:
            rows = report_table.find_all('tr')
            report_data = []
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                
                # Get cell IDs to check for JavaScript-populated cells
                cell_ids = [cell.get('id', '') for cell in cells]
                
                # Extract text from each cell
                cell_texts = []
                for i, cell in enumerate(cells):
                    cell_id = cell.get('id', '')
                    cell_text = cell.get_text(strip=True)
                    
                    # If cell is empty but has an ID, check JavaScript data
                    if not cell_text and cell_id in js_data:
                        js_value = js_data[cell_id]
                        if isinstance(js_value, dict):
                            # Has value and ranking
                            cell_text = f"{js_value['value']} {js_value['ranking']}"
                        elif isinstance(js_value, str):
                            # Simple text value
                            cell_text = js_value
                        else:
                            # List of values - use last one
                            if isinstance(js_value, list) and len(js_value) > 0:
                                last_val = js_value[-1]
                                if isinstance(last_val, dict):
                                    cell_text = f"{last_val['value']} {last_val['ranking']}"
                                else:
                                    cell_text = str(last_val)
                    
                    cell_texts.append(cell_text)
                
                # Pad to 4 columns
                while len(cell_texts) < 4:
                    cell_texts.append('')
                
                # Skip completely empty rows
                if any(cell_texts):
                    report_data.append({
                        'category': cell_texts[0],
                        'offense': cell_texts[1],
                        'defense': cell_texts[2],
                        'div_avg': cell_texts[3]
                    })
            
            data['report_table'] = report_data
            
            # Also create a structured format for easy access
            # Parse values that contain rankings (e.g., "115.7 60" or "1.5%342")
            def parse_value_with_ranking(value_str):
                """
                Parse a value string that may contain a ranking.
                Examples:
                  "115.7 60" -> {"value": "115.7", "ranking": 60}
                  "1.5%342" -> {"value": "1.5%", "ranking": 342}
                  "69.1" -> {"value": "69.1", "ranking": None}
                """
                if not value_str or not value_str.strip():
                    return {"value": "", "ranking": None}
                
                value_str = value_str.strip()
                
                # Try to find a number at the end (the ranking)
                # Pattern: value followed by space and number, or value%number
                import re
                
                # Pattern 1: "value number" (e.g., "115.7 60")
                match1 = re.match(r'^(.+?)\s+(\d+)$', value_str)
                if match1:
                    value = match1.group(1).strip()
                    ranking = int(match1.group(2))
                    return {"value": value, "ranking": ranking}
                
                # Pattern 2: "value%number" or "value\"number" (e.g., "1.5%342", "78.1\"66")
                match2 = re.match(r'^(.+?[%"])(\d+)$', value_str)
                if match2:
                    value = match2.group(1)
                    ranking = int(match2.group(2))
                    return {"value": value, "ranking": ranking}
                
                # Pattern 3: "value number" where value ends with a letter/unit (e.g., "2.47 yrs14")
                match3 = re.match(r'^(.+?[a-zA-Z])\s*(\d+)$', value_str)
                if match3:
                    value = match3.group(1).strip()
                    ranking = int(match3.group(2))
                    return {"value": value, "ranking": ranking}
                
                # No ranking found
                return {"value": value_str, "ranking": None}
            
            structured_report = {}
            for row_data in report_data:
                category = row_data['category']
                if category and category != 'Category':
                    # Clean up category name (remove colons)
                    clean_category = category.rstrip(':')
                    
                    # Special handling for Adj. Tempo - it's a combined stat, not offense/defense
                    if clean_category == 'Adj. Tempo':
                        # For Adj. Tempo:
                        # - offense column = combined tempo value with ranking
                        # - defense column = D-I avg
                        # - div_avg column = empty
                        combined_parsed = parse_value_with_ranking(row_data['offense'])
                        d1_avg_value = row_data['defense'].strip() if row_data['defense'] else ''
                        
                        structured_report[clean_category] = {
                            'combined': combined_parsed['value'],
                            'ranking': combined_parsed['ranking'],
                            'd1_avg': d1_avg_value
                        }
                    else:
                        # Standard parsing for other categories
                        # Parse offense
                        offense_parsed = parse_value_with_ranking(row_data['offense'])
                        # Parse defense
                        defense_parsed = parse_value_with_ranking(row_data['defense'])
                        # Parse d1_avg (usually doesn't have rankings)
                        d1_avg_parsed = parse_value_with_ranking(row_data['div_avg'])
                        
                        structured_report[clean_category] = {
                            'offense': offense_parsed['value'],
                            'offense_ranking': offense_parsed['ranking'],
                            'defense': defense_parsed['value'],
                            'defense_ranking': defense_parsed['ranking'],
                            'd1_avg': d1_avg_parsed['value'],
                            'd1_avg_ranking': d1_avg_parsed['ranking']
                        }
            
            data['report_table_structured'] = structured_report
        
        # Find schedule table (id='schedule-table')
        schedule_table = soup.find('table', id='schedule-table')
        if not schedule_table:
            # Fallback to second table
            all_tables = soup.find_all('table')
            if len(all_tables) > 1:
                schedule_table = all_tables[1]
        
        if schedule_table:
            rows = schedule_table.find_all('tr')
            # Skip header row
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 5:
                    date = cells[0].get_text(strip=True)
                    rk = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    opp_rk = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    opponent = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    result = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                    if date and opponent:
                        data['schedule'].append({
                            'date': date,
                            'rank': rk,
                            'opponent_rank': opp_rk,
                            'opponent': opponent,
                            'result': result
                        })
        
        # Find player table (id='player-table')
        player_table = soup.find('table', id='player-table')
        if not player_table:
            # Fallback to third table
            all_tables = soup.find_all('table')
            if len(all_tables) > 2:
                player_table = all_tables[2]
        
        if player_table:
            rows = player_table.find_all('tr')
            # Skip header rows
            for row in rows[2:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 5:
                    player_name = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    if player_name and player_name not in ['', 'Major Contributors']:
                        height = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        weight = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                        year = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                        data['player_stats'].append({
                            'name': player_name,
                            'height': height,
                            'weight': weight,
                            'year': year
                        })
        
        # Extract any other relevant data
        # Add more extraction logic here based on what you need from KenPom
        
        return {
            'team': team_slug,
            'team_name': team_name_found,
            'url': url,
            'data': data,
            'html': response_text  # Include for debugging
        }
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch kenpom.com data for {team_slug}: {e}")

def get_kenpom_raw_html(team_slug):
    """
    Fetch raw HTML from kenpom.com (useful for inspection/debugging).
    
    Args:
        team_slug: Team identifier
    
    Returns:
        str: Raw HTML content
    """
    result = get_kenpom_team_data(team_slug)
    return result['html']

if __name__ == '__main__':
    # Test with UCLA
    print("Testing kenpom.com data fetcher...\n")
    
    test_team = "UCLA"
    
    # Check if credentials exist
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"⚠ Warning: Credentials file not found: {CREDENTIALS_FILE}")
        print("   Create this file with your kenpom.com username and password.")
        print("   See the script comments for format details.")
        print("\n   Example format:")
        print('   {')
        print('     "username": "your_email@example.com",')
        print('     "password": "your_password"')
        print('   }')
        print()
    
    try:
        print(f"Fetching data for: {test_team}")
        result = get_kenpom_team_data(test_team)
        
        print(f"✓ Successfully fetched page")
        print(f"  Team: {result['team_name']}")
        print(f"  URL: {result['url']}")
        print(f"  HTML length: {len(result['html'])} characters")
        
        # Print extracted data
        if 'data' in result:
            data = result['data']
            
            # Print report table data
            if 'report_table_structured' in data and data['report_table_structured']:
                print(f"\n  Report Table (first 10 rows):")
                print(f"    {'Category':<35} {'Offense':<25} {'Defense':<25} {'D-I Avg':<15}")
                print(f"    {'-'*100}")
                for i, (category, stats) in enumerate(list(data['report_table_structured'].items())[:10]):
                    offense = stats.get('offense', '')[:20]
                    defense = stats.get('defense', '')[:20]
                    d1_avg = stats.get('d1_avg', '')[:15]
                    print(f"    {category:<35} {offense:<25} {defense:<25} {d1_avg:<15}")
            
            if 'schedule' in data and data['schedule']:
                print(f"\n  Schedule (first 3 games):")
                for game in data['schedule'][:3]:
                    print(f"    {game.get('date')}: {game.get('opponent')} - {game.get('result')}")
            if 'player_stats' in data and data['player_stats']:
                print(f"\n  Players (first 5):")
                for player in data['player_stats'][:5]:
                    print(f"    {player.get('name')} ({player.get('height')}, {player.get('year')})")
        
        # Optionally save HTML for inspection
        output_file = f"kenpom_{test_team.lower().replace(' ', '_')}_output.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['html'])
        print(f"\n  Saved HTML to: {output_file} (for inspection)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Tips:")
        print("   1. Make sure your username and password are correct in kenpom_credentials.json")
        print("   2. Verify your subscription is active")
        print("   3. If login fails, check the actual login form on kenpom.com to see the field names")

