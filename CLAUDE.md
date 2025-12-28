# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

College Basketball Data (CBB) project - A comprehensive system for fetching, processing, and displaying college basketball team and player statistics. Data is generated via Python scripts using the College Basketball Data API, stored as JSON files on GitHub Pages, and accessed via Google Apps Script functions in Google Sheets.

## Build and Development Commands

### Python Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# For web UI development
pip install -r web-ui/requirements.txt
```

### Data Generation
```bash
# Generate team data (run from project root)
python scripts/generate_ucla_data_json_2026.py

# Or run from scripts directory
cd scripts
python generate_ucla_data_json_2026.py
```

### Google Apps Script Deployment
```bash
# Deploy Apps Script updates (run from project root)
./apps-script/push-script.sh

# Manual deployment
cd apps-script
cp google-apps-script-cbbd.js Code.gs
clasp push
```

### Web UI (Flask Application)
```bash
# Run locally
cd web-ui
export CBB_API_KEY=your_api_key_here
python app.py
# Access at http://localhost:5001
```

### Production API (Regenerate Team Data)
The production web UI is hosted on Render at `https://cbb-data-generator.onrender.com`

To regenerate team data via API:
```bash
# Start generation job
curl -X POST https://cbb-data-generator.onrender.com/api/generate \
  -H "Content-Type: application/json" \
  -d '{"team_name": "Utah", "include_historical_stats": true}'

# Response: {"job_id": "utah_2026_1735123456"}

# Check job status
curl https://cbb-data-generator.onrender.com/api/status/<job_id>

# Cancel a job
curl -X POST https://cbb-data-generator.onrender.com/api/cancel/<job_id>
```

Optional: Add `"notify_email": "you@example.com"` to the request body for email notification on completion.

### Running Tests
```bash
# Run all end-to-end tests (Oregon, Western Kentucky, Arizona State)
pytest tests/test_generator_e2e.py -v

# Run tests for a specific team
pytest tests/test_generator_e2e.py -v -k "Oregon"

# Validate existing data files
pytest tests/test_schema_validation.py -v
```

### Testing Data Sources
```bash
# Test Wikipedia scraper
python misc_data_sources/wikipedia/scripts/test_wikipedia_teams.py

# Test Bart Torvik scraper
python misc_data_sources/barttorvik/scripts/test_barttorvik.py

# Test KenPom API
python misc_data_sources/kenpom/scripts/kenpom_api.py "UCLA"
```

## Architecture Overview

### Three-Tier System

1. **Data Generation Layer (Python)**
   - `scripts/cbb_api_wrapper.py` - Core API wrapper with rate limiting and retry logic
   - `scripts/generate_*_data_json_2026.py` - Team-specific data generators
   - `web-ui/generator.py` - Generic team data generator used by Flask web UI
   - Generates comprehensive JSON files with player stats, game data, roster info

2. **Data Storage Layer**
   - JSON files stored in `data/2025/` and `data/2026/` directories
   - Files tracked in git for GitHub Pages hosting
   - Accessed via raw GitHub URLs (e.g., `https://raw.githubusercontent.com/.../ucla_scouting_data_2026.json`)
   - Optional S3 storage for historical stats (web-ui only)

3. **Access Layer (Google Apps Script)**
   - `apps-script/google-apps-script-cbbd.js` - Main library with all functions
   - `apps-script/LibraryWrappers.gs` - Wrapper functions for spreadsheets
   - Deployed as a Google Apps Script library (Library ID: `1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW`)
   - Users add library to spreadsheets and call functions like `=GET_PLAYERS_FULL(A1)`

### Data Sources Integration

The system integrates multiple external data sources via scrapers in `misc_data_sources/`:

- **Wikipedia** (`misc_data_sources/wikipedia/`) - Team metadata, infobox data, championships, AP rankings
- **Bart Torvik** (`misc_data_sources/barttorvik/`) - Resume metrics (NET, KPI, SOR, WAB), quality metrics (BPI, KenPom, T-Rank), quadrant records
- **KenPom** (`misc_data_sources/kenpom/`) - Advanced metrics (Adj. Efficiency, Adj. Tempo, Four Factors, etc.)
- **Quadrants** (`misc_data_sources/quadrants/`) - NET ratings and quadrant win data
- **Coaching History** (`misc_data_sources/coaching_history/`) - Historical coach records
- **FoxSports Rosters** (`foxsports_rosters/`) - Cached roster data with player heights, weights, positions

Each scraper is optional and non-blocking - if unavailable or fails, data generation continues without that source.

## Key Implementation Details

### API Rate Limiting
- `cbb_api_wrapper.py` implements 500ms between requests to avoid rate limits
- Includes automatic retry with exponential backoff (max 3 retries)
- Tracks all API calls with timestamps and durations in `api_calls_log`

### Historical Player Data
- Searches previous seasons (2023-2025) for player career stats
- Uses S3 for caching historical data (web-ui only) to avoid repeated API calls
- Function: `get_player_career_season_stats()` in generator scripts

### Conference Rankings
- Calculated within generators using `calculate_player_conference_rankings_from_list()`
- Ranks players by PPG, RPG, APG, SPG, BPG, FG%, 3P%, FT% within conference
- Stored in each player's `conferenceRankings` field

### Google Apps Script Functions
Main categories (see `apps-script/google-apps-script-cbbd.js`):
1. **Team Meta Information** - `GET_TEAM_META()`, records, NET rating, AP rankings
2. **Player Roster Data** - `GET_PLAYERS_FULL()`, `GET_PLAYERS_FULL_NUMERIC()`
3. **Individual Player Stats** - `GET_PLAYER_GAMES()`, historical stats
4. **Team Game Log** - `GET_GAME_LOG()`, `GET_GAME_LOG_SIMPLIFIED()`
5. **Conference Analysis** - `GET_CONFERENCE_PLAYERS()`, advanced filters
6. **Historical Data** - `GET_PLAYER_HISTORICAL_STATS()`
7. **Coaching History** - `GET_SCHOOL_COACHING_HISTORY()`, `GET_CURRENT_COACH_SEASON_COUNT()`
8. **External Data** - KenPom functions, Wikipedia data

### Web UI Architecture
- **Flask app** (`web-ui/app.py`) - REST API for team data generation
- **Background jobs** - Long-running generation tasks stored in memory
- **Real-time updates** - WebSocket-style status updates via polling
- **GitHub integration** - Automatic push of generated JSON files
- **Email notifications** - Optional email alerts on completion

## File Organization

```
cbbd/
├── scripts/              # Python data generation scripts
│   ├── cbb_api_wrapper.py          # Core API wrapper
│   ├── generate_*_data_json_2026.py # Team-specific generators
│   ├── team_lookup.py              # Centralized team name lookup library
│   ├── generate_team_registry.py   # Registry generator script
│   └── config.py                    # Configuration helper
├── config/               # Configuration files
│   └── team_registry.json          # Centralized team registry (365+ teams)
├── tests/                # Automated tests
│   ├── test_generator_e2e.py       # End-to-end generator tests
│   └── test_schema_validation.py   # JSON schema validation
├── apps-script/          # Google Apps Script library
│   ├── google-apps-script-cbbd.js   # Main library code
│   ├── LibraryWrappers.gs           # Wrapper functions
│   ├── Code.gs                      # clasp-compatible version
│   └── push-script.sh               # Deployment script
├── web-ui/              # Flask web application
│   ├── app.py                       # Main Flask app
│   ├── generator.py                 # Generic team data generator
│   ├── github_handler.py            # GitHub push functionality
│   ├── s3_handler.py                # S3 storage for historical stats
│   └── email_notifier.py            # Email notifications
├── misc_data_sources/   # External data scrapers
│   ├── wikipedia/                   # Wikipedia API scraper
│   ├── barttorvik/                  # Bart Torvik teamsheets scraper
│   ├── kenpom/                      # KenPom advanced metrics
│   ├── quadrants/                   # NET ratings and quadrant data
│   └── coaching_history/            # Coach history scraper
├── foxsports_rosters/   # Cached roster data
│   └── rosters_cache/               # 700+ team roster JSON files
├── data/                # Generated JSON files
│   ├── 2025/                        # 2024-25 season
│   └── 2026/                        # 2025-26 season
└── docs/                # Documentation
```

## Working with Data Generators

### Creating a New Team Generator
1. Copy an existing generator: `cp scripts/generate_ucla_data_json_2026.py scripts/generate_[team]_data_json_2026.py`
2. Update team configuration at top of file (team name, API team ID)
3. Run to generate data: `python scripts/generate_[team]_data_json_2026.py`
4. Output saved to: `data/2026/[team]_scouting_data_2026.json`

### Modifying the Generic Generator
- Web UI uses `web-ui/generator.py` which works for any team
- Imports scrapers dynamically with availability checks
- All scrapers are optional and non-blocking
- Add new data sources by following the import pattern at top of file

## Important Conventions

### Season Naming
- Season "2026" refers to 2025-26 academic year
- JSON files use `_2026` suffix for current season
- Previous season files have no suffix or `_2025` suffix

### Centralized Team Lookup
The project uses a centralized team registry for resolving team names across all external services:

- **Registry**: `config/team_registry.json` - Single source of truth with 365+ teams
- **Lookup Library**: `scripts/team_lookup.py` - O(1) lookups from any team name variation
- **Generator**: `scripts/generate_team_registry.py` - Rebuilds registry from source mappings

Usage in code:
```python
from scripts.team_lookup import get_team_lookup

lookup = get_team_lookup()
bballnet_slug = lookup.lookup("Western Kentucky", "bballnet")  # → "western-kentucky"
wiki_page = lookup.lookup("UCLA", "wikipedia_page")  # → "UCLA Bruins men's basketball"
team_id = lookup.get_team_id("Arizona St.")  # → 221
```

Supported services: `bballnet`, `sports_reference`, `wikipedia_page`, `barttorvik`, `kenpom`

### Team ID Mapping (Legacy)
- College Basketball API uses numeric team IDs
- FoxSports cache uses team names (e.g., "UCLA", "Oregon")
- Mapping file: `foxsports_rosters/cbb_to_foxsports_team_mapping.json`
- **Note**: Prefer using centralized `TeamLookup` for new code

### JSON Data Structure
Each team JSON file contains:
- `team`, `season`, `seasonType` - Basic metadata
- `dataGenerated` - ISO timestamp of generation
- `metadata` - API call count, total players, AP rankings
- `roster` - Array of player objects with season totals and game logs
- `totalRecord`, `conferenceRecord` - Win-loss records
- `netRating` - NET rating data
- `coachHistory` - Historical coaching records (last 6 seasons)
- `kenpomData` - Advanced metrics (if available)
- `barttorvikData` - Resume and quality metrics (if available)
- `wikipediaData` - Team metadata and championships (if available)

### Credentials and Environment Variables

**Python/Web UI:**
- `CBB_API_KEY` - College Basketball Data API key (required)
- `KENPOM_USERNAME`, `KENPOM_PASSWORD` - KenPom subscription (optional)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME` - S3 storage (optional, web-ui only)
- `GIT_USER_NAME`, `GIT_USER_EMAIL` - GitHub push (web-ui only)

**Google Apps Script:**
- No credentials needed - fetches JSON from GitHub raw URLs
- Library ID: `1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW`

## Development Workflow

### Modifying Apps Script Functions
1. Edit `apps-script/google-apps-script-cbbd.js`
2. Run `./apps-script/push-script.sh` from project root
3. All spreadsheets using Development mode get updates automatically
4. Test in a spreadsheet with `=GET_TEAM_META(url)` or other functions

### Adding External Data Sources
1. Create new directory in `misc_data_sources/[source_name]/`
2. Add scraper in `misc_data_sources/[source_name]/scripts/`
3. Add README.md with usage instructions
4. Import in `web-ui/generator.py` with try/except for optional loading
5. Add corresponding Apps Script function in `google-apps-script-cbbd.js`

### Testing Changes
- **API Wrapper:** Modify `scripts/cbb_api_wrapper.py`, test with any generator
- **Data Sources:** Each has test scripts in their `scripts/` directory
- **Web UI:** Run locally with `python web-ui/app.py`, test with team search
- **Apps Script:** Test in Google Sheets with Development mode enabled

## Deployment

### Production Web UI (Render.com)
- Deploy from GitHub repository
- Configure environment variables in Render dashboard
- Build command: `cd web-ui && pip install -r requirements.txt`
- Start command: `cd web-ui && gunicorn app:app --bind 0.0.0.0:$PORT`
- See `web-ui/DEPLOYMENT.md` and `PRODUCTION_DEPLOYMENT_CHECKLIST.md`

### Google Apps Script
- Library deployed at: https://script.google.com/d/1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW/edit
- Use Development mode for automatic updates during development
- Switch to versioned releases for production stability
- See `docs/DEVELOPMENT_MODE_SETUP.md` and `docs/LIBRARY_INFO.md`

## Session Continuity

**IMPORTANT:** When suggesting that the user restart Claude Code (e.g., after MCP server changes, token refresh, or config updates), ALWAYS provide a ready-to-paste prompt that will seamlessly continue the current task. Include:
1. What was just changed/fixed
2. What to test or verify
3. Any cleanup needed from the previous session
4. The next step in the workflow

This ensures the user doesn't lose context between sessions.

## Google Sheets MCP Server

The project includes a custom MCP server for Google Sheets integration at `mcp-google-sheets/`.

### Available Tools
- `drive_list_spreadsheets` - List accessible spreadsheets
- `drive_copy_file` - Duplicate entire spreadsheet (preserves all formulas/references)
- `sheets_read_range` / `sheets_write_range` - Read/write cell values
- `sheets_get_formulas` - Get formulas (not computed values)
- `sheets_list_sheets` - List tabs in a spreadsheet
- `sheets_copy_sheet` - Copy individual sheets (cross-sheet references may break)
- `sheets_batch_update` - Execute multiple updates
- `sheets_set_format` - Apply formatting
- And more (see `mcp-google-sheets/server.py`)

### Re-authentication
If MCP server scopes change, re-authenticate:
```bash
cd mcp-google-sheets
rm token.json
python auth.py
```
Then restart Claude Code.

### Key Spreadsheets
- UCLA mbb Dec4 `<master>`: `1Aj43ImLkcDDNkKmktgiTFBv6sgMiHObdI9lOLbearzA` - Template/master scouting sheet
