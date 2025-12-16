# College Basketball Data (CBB) Project

A comprehensive system for fetching, processing, and displaying college basketball team and player statistics using the College Basketball Data API.

## 📁 Project Structure

```
cbbd/
├── scripts/              # Python data generation scripts
│   ├── cbb_api_wrapper.py         # Core API wrapper
│   ├── team_lookup.py             # Centralized team name lookup
│   ├── generate_team_registry.py  # Registry generator
│   └── generate_*_data_json*.py   # Team-specific generators
├── config/               # Configuration files
│   ├── api_config.txt             # API credentials
│   └── team_registry.json         # Centralized team registry (365+ teams)
├── tests/                # Automated tests
│   ├── test_generator_e2e.py      # End-to-end generator tests
│   └── test_schema_validation.py  # JSON schema validation
├── web-ui/               # Flask web application
│   ├── app.py                     # Main Flask app
│   └── generator.py               # Generic team data generator
├── apps-script/          # Google Apps Script library
│   ├── google-apps-script-cbbd.js # Main library code
│   ├── LibraryWrappers.gs         # Wrapper functions
│   └── push-script.sh             # Deployment script
├── misc_data_sources/    # External data scrapers
│   ├── wikipedia/                 # Wikipedia API scraper
│   ├── barttorvik/                # Bart Torvik metrics
│   ├── kenpom/                    # KenPom advanced stats
│   ├── quadrants/                 # NET ratings and quadrant data
│   └── coaching_history/          # Historical coach records
├── data/                 # Generated JSON data files
│   ├── 2025/                      # 2024-25 season data
│   └── 2026/                      # 2025-26 season data
├── docs/                 # Documentation
└── requirements.txt      # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js (for clasp)
- Google account with Apps Script API enabled

### Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API credentials:**
   - Copy `config/api_config.txt` and add your API key
   - Or set environment variable: `CBB_API_KEY=your_key`

3. **Generate data for a team:**
   ```bash
   cd scripts
   python generate_ucla_data_json_2026.py
   ```

4. **Push Google Apps Script updates:**
   ```bash
   ./apps-script/push-script.sh
   ```

## 📚 Documentation

All documentation is in the `docs/` directory:

- **CLASP_SETUP.md** - Setting up clasp for Apps Script deployment
- **DATA_ORGANIZATION.md** - Data structure and organization
- **DEVELOPMENT_MODE_SETUP.md** - Using Apps Script in development mode
- **WRAPPER_FUNCTIONS_SETUP.md** - Setting up wrapper functions in spreadsheets
- **LIBRARY_INFO.md** - Library ID and deployment information
- **TROUBLESHOOTING.md** - Common issues and solutions

## 🔧 Usage

### Generating Team Data

Generate JSON data for a team (example: UCLA 2026 season):

```bash
cd scripts
python generate_ucla_data_json_2026.py
```

This creates: `data/2026/ucla_scouting_data_2026.json`

### Using Google Apps Script Functions

1. Add the library to your spreadsheet (see `docs/DEVELOPMENT_MODE_SETUP.md`)
2. Copy `apps-script/LibraryWrappers.gs` to your spreadsheet's Apps Script
3. Use functions in cells:
   ```
   =GET_PLAYERS_FULL(A1)
   =GET_TEAM_META(A1)
   =GET_PLAYER_GAMES(A1, "Player Name")
   ```

### Updating the Apps Script Library

```bash
./apps-script/push-script.sh
```

All spreadsheets using Development mode will automatically get updates.

## 📊 Data Sources

The generator integrates multiple external data sources:

| Source | Data Provided |
|--------|--------------|
| **CBB API** | Core stats, rosters, game logs |
| **Wikipedia** | Team metadata, championships, AP rankings |
| **Bart Torvik** | Resume metrics (NET, KPI, SOR), quadrant records |
| **KenPom** | Advanced metrics (efficiency, tempo, four factors) |
| **bballnet.com** | NET ratings, quadrant win data |
| **Sports Reference** | Historical coaching records |

All scrapers are optional - if one fails, generation continues with available data.

## 📊 Data Structure

JSON files contain:
- Team metadata and records
- Player roster with season totals
- Game-by-game statistics
- Conference and D1 rankings
- Historical player data (previous seasons)
- External metrics (KenPom, Bart Torvik, Wikipedia)

See `docs/DATA_ORGANIZATION.md` for detailed structure.

## 🧪 Testing

```bash
# Run all end-to-end tests
pytest tests/test_generator_e2e.py -v

# Run tests for a specific team
pytest tests/test_generator_e2e.py -v -k "Oregon"

# Validate existing data files
pytest tests/test_schema_validation.py -v
```

## 🔑 Key Files

- **scripts/cbb_api_wrapper.py** - API wrapper with rate limiting
- **scripts/team_lookup.py** - Centralized team name resolution
- **config/team_registry.json** - Team registry with service-specific slugs
- **apps-script/google-apps-script-cbbd.js** - Main Apps Script library
- **web-ui/generator.py** - Generic team data generator
- **data/2026/** - Current season data files

## 🛠️ Development

### Adding a New Team

1. Create a new generator script: `scripts/generate_[team]_data_json_2026.py`
2. Copy from an existing generator and update team ID
3. Run the script to generate data
4. Push to GitHub for GitHub Pages hosting

### Updating Apps Script Functions

1. Edit `apps-script/google-apps-script-cbbd.js`
2. Run `./apps-script/push-script.sh`
3. Updates propagate automatically to Development mode spreadsheets

## 📝 Notes

- All JSON data is tracked in git for GitHub Pages hosting
- The Apps Script library is deployed separately from data files
- Use Development mode for automatic updates during active development
- Switch to versioned libraries for production stability

## 🔗 Links

- **Apps Script Library**: https://script.google.com/d/1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW/edit
- **Library ID**: `1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW`

## 📄 License

[Add your license here]

