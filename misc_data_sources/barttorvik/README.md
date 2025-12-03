# Bart Torvik Teamsheets Scraper

This module scrapes team sheets data from [barttorvik.com](https://barttorvik.com/teamsheets.php), including resume metrics, quality metrics, and quadrant records.

## Data Retrieved

### Resume Metrics
- **NET** - NCAA Evaluation Tool ranking
- **KPI** - Key Performance Indicator ranking
- **SOR** - Strength of Record ranking
- **WAB** - Wins Above Bubble ranking
- **Avg** - Average of resume metrics

### Quality Metrics
- **BPI** - ESPN Basketball Power Index ranking
- **KP** - KenPom ranking
- **TRK** - T-Rank ranking
- **Avg** - Average of quality metrics

### Quadrant Records
- **Q1A** - Quadrant 1A record (W-L format)
- **Q1** - Quadrant 1 record (W-L format)
- **Q2** - Quadrant 2 record (W-L format)
- **Q1&2** - Combined Quadrant 1 & 2 record (W-L format)
- **Q3** - Quadrant 3 record (W-L format)
- **Q4** - Quadrant 4 record (W-L format)

## Usage

```python
from barttorvik.scripts.barttorvik_teamsheets import get_teamsheets_data_structured, get_team_teamsheet_data

# Get data for a specific team (recommended - fetches all teams and filters)
team_data = get_team_teamsheet_data('UCLA', year=2026)

# Get Big Ten data for 2026
data = get_teamsheets_data_structured(year=2026, conference='B10', sort=8)

# Get all teams for 2026
data = get_teamsheets_data_structured(year=2026, conference='All', sort=8)
```

## Functions

### `get_team_teamsheet_data(team_name, year, sort)`
Fetches teamsheet data for a specific team. Fetches all teams from barttorvik.com and filters to the specified team.

**Parameters:**
- `team_name` (str): Team name to fetch (e.g., 'UCLA', 'Oregon', 'Michigan State')
- `year` (int): Season year (default: 2026)
- `sort` (int): Sort column (default: 8)

**Returns:**
- Dictionary with structured team data, or None if team not found

**Example:**
```python
ucla_data = get_team_teamsheet_data('UCLA', year=2026)
# Returns: {'rank': 22, 'team': 'UCLA', 'seed': 8, 'resume': {...}, ...}
```

### `get_teamsheets_data(year, conference, sort)`
Returns raw team data as a list of dictionaries.

**Parameters:**
- `year` (int): Season year (default: 2026)
- `conference` (str, optional): Conference filter (e.g., 'B10' for Big Ten)
- `sort` (int): Sort column index (default: 8)

**Returns:**
- List of dictionaries with team data

### `get_teamsheets_data_structured(year, conference, sort)`
Returns structured team data with nested resume/quality/quadrants.

**Parameters:**
- Same as `get_teamsheets_data`

**Returns:**
- List of dictionaries with structured data:
  ```python
  {
    'rank': int,
    'team': str,
    'seed': int,  # NCAA tournament seed (if available)
    'resume': {
      'net': int,
      'kpi': int,
      'sor': int,
      'wab': int,
      'avg': float
    },
    'quality': {
      'bpi': int,
      'kenpom': int,
      'trk': int,
      'avg': float
    },
    'quadrants': {
      'q1a': {'record': str, 'wins': int, 'losses': int},
      'q1': {'record': str, 'wins': int, 'losses': int},
      'q2': {'record': str, 'wins': int, 'losses': int},
      'q1_and_q2': {'record': str, 'wins': int, 'losses': int},
      'q3': {'record': str, 'wins': int, 'losses': int},
      'q4': {'record': str, 'wins': int, 'losses': int}
    }
  }
  ```

## Testing

Run the test script:

```bash
python3 misc_data_sources/barttorvik/scripts/test_barttorvik.py
```

This will fetch Big Ten data for 2026 and save results to `test_data/barttorvik_test_results.json`.

## Dependencies

- `playwright` - Browser automation (required for JavaScript rendering)
- `beautifulsoup4` - HTML parsing
- `requests` - HTTP library (fallback if playwright not available)

Install with:
```bash
pip install playwright beautifulsoup4 requests
playwright install chromium
```

**Note:** The site uses JavaScript verification, so Playwright is required for reliable scraping. The scraper will attempt to use Playwright first, then fall back to cloudscraper or requests if Playwright is not available (though these may not work due to bot protection).

