#!/usr/bin/env python3
"""
Barttorvik Teamsheets Fetcher for Raspberry Pi

This script fetches college basketball teamsheets data from barttorvik.com
and uploads it to S3 for the main Render app to consume.

Running from a residential IP (Pi) avoids Cloudflare blocking issues
that occur from cloud IPs like Render.

Usage:
    python barttorvik_fetcher.py              # Fetch and upload
    python barttorvik_fetcher.py --dry-run    # Fetch only, no upload
    python barttorvik_fetcher.py --year 2026  # Specify season year
"""

import os
import sys
import json
import re
import argparse
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

from bs4 import BeautifulSoup

try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    logger.warning("boto3 not installed. S3 upload will be disabled.")


# Team name mapping for special cases
BARTTORVIK_TEAM_MAPPING = {
    'ole miss': 'Mississippi',
    'mississippi rebels': 'Mississippi',
    'miami(fl)': 'Miami FL',
    'miami fl': 'Miami FL',
    'miami (fl)': 'Miami FL',
    'miami(oh)': 'Miami OH',
    'miami oh': 'Miami OH',
    'miami (oh)': 'Miami OH',
    'uconn': 'Connecticut',
    'connecticut huskies': 'Connecticut',
    "hawai'i": 'Hawaii',
    'hawai`i': 'Hawaii',
    'uic': 'Illinois Chicago',
    'illinois-chicago': 'Illinois Chicago',
    'fdu': 'Fairleigh Dickinson',
    'gardner-webb': 'Gardner Webb',
    'bethune-cookman': 'Bethune Cookman',
    'st. francis(pa)': 'Saint Francis',
    'st francis(pa)': 'Saint Francis',
    'st. francis (pa)': 'Saint Francis',
    'saint francis(pa)': 'Saint Francis',
}


def fetch_teamsheets_html(year: int = 2026, headless: bool = False, retries: int = 3) -> str:
    """
    Fetch the teamsheets HTML page using Playwright.

    Args:
        year: Season year
        headless: Run browser in headless mode (False recommended for Pi)
        retries: Number of retry attempts

    Returns:
        HTML content of the page
    """
    url = f"https://barttorvik.com/teamsheets.php?sort=8&year={year}&conlimit=All"

    for attempt in range(1, retries + 1):
        logger.info(f"Attempt {attempt}/{retries}: Fetching {url}")

        try:
            with sync_playwright() as p:
                # Use headed browser on Pi - more reliable with Cloudflare
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                    ]
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                )
                page = context.new_page()

                # Navigate to the page
                page.goto(url, wait_until='domcontentloaded', timeout=60000)

                # Wait for Cloudflare challenge to complete
                logger.info("Waiting for Cloudflare verification...")
                try:
                    page.wait_for_function(
                        "document.body && !document.body.innerText.includes('Verifying')",
                        timeout=45000
                    )
                    logger.info("Cloudflare verification completed")
                except Exception as cf_err:
                    logger.warning(f"Cloudflare wait: {cf_err}")

                # Wait for the table to appear
                try:
                    page.wait_for_selector('table', timeout=20000)
                    page.wait_for_timeout(2000)  # Extra time for rendering
                    logger.info("Table found on page")
                except Exception as table_err:
                    body_text = page.evaluate("document.body.innerText.substring(0, 300)")
                    logger.warning(f"Table wait timeout. Page preview: {body_text}")
                    if attempt < retries:
                        browser.close()
                        continue
                    raise Exception(f"Could not find table after {retries} attempts")

                html_content = page.content()
                browser.close()

                # Verify we got actual data
                if 'table' not in html_content.lower():
                    if attempt < retries:
                        continue
                    raise Exception("HTML content does not contain a table")

                return html_content

        except Exception as e:
            logger.error(f"Attempt {attempt} failed: {e}")
            if attempt == retries:
                raise

    raise Exception(f"Failed to fetch data after {retries} attempts")


def parse_teamsheets_html(html_content: str) -> List[Dict]:
    """
    Parse the teamsheets HTML and extract team data.

    Args:
        html_content: Raw HTML from barttorvik.com

    Returns:
        List of team dictionaries
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the main table
    table = soup.find('table')
    if not table:
        raise Exception("Could not find data table in HTML")

    # Find header row
    header_rows = table.find_all('tr')
    header_row = None
    for row in header_rows:
        ths = row.find_all('th')
        if len(ths) > 5:
            header_row = row
            break

    if not header_row:
        header_row = header_rows[0]

    headers = []
    for th in header_row.find_all(['th', 'td']):
        header_text = th.get_text(strip=True)
        header_text = re.sub(r'\s+', ' ', header_text)
        headers.append(header_text)

    # Extract data rows
    teams_data = []
    data_started = False

    for row in table.find_all('tr'):
        if row == header_row:
            data_started = True
            continue
        if not data_started:
            continue

        cols = row.find_all(['td', 'th'])
        if len(cols) < 10:
            continue

        team_data = {}

        for i, col in enumerate(cols):
            if i >= len(headers):
                break

            value = col.get_text(strip=True)
            value = re.sub(r'\s+', ' ', value)

            if i == 0:  # Rk
                team_data['rank'] = int(value) if value.isdigit() else value
            elif i == 1:  # Team
                team_link = col.find('a')
                if team_link:
                    team_data['team'] = team_link.get_text(strip=True)
                else:
                    team_data['team'] = value

                # Extract seed
                seed_span = col.find('span', class_=lambda x: x and ('bub' in str(x) or 'tooltipstered' in str(x)))
                if seed_span:
                    seed_text = seed_span.get_text(strip=True)
                    try:
                        team_data['seed'] = int(seed_text)
                    except:
                        team_data['seed'] = seed_text
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

        if team_data and 'team' in team_data:
            teams_data.append(team_data)

    return teams_data


def parse_quadrant_record(record_str: str) -> Dict[str, int]:
    """Parse a quadrant record string like '1-0' into wins and losses."""
    if not record_str or '-' not in record_str:
        return {'wins': 0, 'losses': 0}

    try:
        parts = record_str.split('-')
        return {'wins': int(parts[0].strip()), 'losses': int(parts[1].strip())}
    except:
        return {'wins': 0, 'losses': 0}


def structure_team_data(raw_data: List[Dict]) -> List[Dict]:
    """
    Convert raw parsed data into the structured format expected by the main app.
    """
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


def upload_to_s3(data: Dict, bucket: str, key: str) -> bool:
    """
    Upload JSON data to S3.

    Args:
        data: Dictionary to upload as JSON
        bucket: S3 bucket name
        key: S3 object key (path)

    Returns:
        True if successful, False otherwise
    """
    if not S3_AVAILABLE:
        logger.error("boto3 not installed, cannot upload to S3")
        return False

    try:
        s3_client = boto3.client('s3')
        json_data = json.dumps(data, indent=2)

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json_data,
            ContentType='application/json',
            ACL='public-read'  # Make publicly accessible for Render to read
        )

        logger.info(f"Successfully uploaded to s3://{bucket}/{key}")
        return True

    except ClientError as e:
        logger.error(f"S3 upload failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Fetch Barttorvik teamsheets and upload to S3')
    parser.add_argument('--year', type=int, default=2026, help='Season year (default: 2026)')
    parser.add_argument('--dry-run', action='store_true', help='Fetch only, do not upload to S3')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--output', type=str, help='Save JSON to local file')
    parser.add_argument('--bucket', type=str, default='cbb-data-files', help='S3 bucket name')
    args = parser.parse_args()

    logger.info(f"Starting Barttorvik fetch for {args.year} season")

    try:
        # Fetch HTML
        html_content = fetch_teamsheets_html(year=args.year, headless=args.headless)

        # Parse and structure data
        raw_data = parse_teamsheets_html(html_content)
        structured_data = structure_team_data(raw_data)

        logger.info(f"Successfully parsed {len(structured_data)} teams")

        # Create the cache object with metadata
        cache_object = {
            'fetched_at': datetime.now(timezone.utc).isoformat(),
            'year': args.year,
            'team_count': len(structured_data),
            'source': 'raspberry-pi-fetcher',
            'teams': structured_data
        }

        # Save to local file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(cache_object, f, indent=2)
            logger.info(f"Saved to {args.output}")

        # Upload to S3 unless dry-run
        if not args.dry_run:
            s3_key = f"cache/barttorvik_teamsheets_{args.year}.json"
            if upload_to_s3(cache_object, args.bucket, s3_key):
                logger.info("Upload complete!")
            else:
                logger.error("Upload failed")
                sys.exit(1)
        else:
            logger.info("Dry run - skipping S3 upload")
            # Print sample data
            if structured_data:
                logger.info(f"Sample team: {json.dumps(structured_data[0], indent=2)}")

        logger.info("Done!")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
