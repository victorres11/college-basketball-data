# Project Structure

This document describes the organized structure of the CBB Data project.

## Directory Layout

```
cbbd/
├── apps-script/          # Google Apps Script files
│   ├── google-apps-script-cbbd.js  # Main library code
│   ├── LibraryWrappers.gs         # Wrapper functions for spreadsheets
│   ├── Code.gs                    # clasp-compatible version
│   ├── appsscript.json            # Apps Script manifest
│   └── push-script.sh             # Script to push updates
│
├── config/               # Configuration files
│   ├── api_config.txt             # API credentials
│   └── api_test_results.json      # Test results
│
├── data/                 # Generated JSON data files
│   ├── 2025/                      # 2024-25 season data
│   │   ├── ucla_scouting_data.json
│   │   ├── msu_scouting_data.json
│   │   └── eastern_washington_scouting_data.json
│   └── 2026/                      # 2025-26 season data
│       ├── ucla_scouting_data_2026.json
│       ├── msu_scouting_data_2026.json
│       └── eastern_washington_scouting_data_2026.json
│
├── docs/                 # Documentation
│   ├── CLASP_SETUP.md
│   ├── DATA_ORGANIZATION.md
│   ├── DEVELOPMENT_MODE_SETUP.md
│   ├── GITHUB_PAGES_SETUP.md
│   ├── LIBRARY_INFO.md
│   ├── TROUBLESHOOTING.md
│   └── WRAPPER_FUNCTIONS_SETUP.md
│
├── output/               # Generated HTML reports and outputs
│   ├── *.html                     # HTML reports
│   └── *.pdf                      # PDF exports
│
├── scripts/              # Python scripts
│   ├── cbb_api_wrapper.py         # API wrapper class
│   ├── config.py                  # Configuration helper
│   ├── generate_*_data_json*.py   # Data generators
│   └── *.py                        # Other utility scripts
│
├── .clasp.json           # clasp configuration
├── .claspignore          # clasp ignore patterns
├── .gitignore            # Git ignore patterns
├── README.md             # Main project README
├── requirements.txt      # Python dependencies
└── setup.py              # Python package setup
```

## File Organization Principles

### Scripts (`scripts/`)
- All Python scripts for data generation and processing
- Scripts can import from each other (same directory)
- Run from project root: `python scripts/generate_ucla_data_json_2026.py`
- Or from scripts directory: `cd scripts && python generate_ucla_data_json_2026.py`

### Apps Script (`apps-script/`)
- All Google Apps Script related files
- `clasp` is configured to use this as root directory
- Push updates: `./apps-script/push-script.sh`

### Data (`data/`)
- Organized by season (2025/, 2026/, etc.)
- JSON files follow naming: `[team]_scouting_data_[season].json`
- Tracked in git for GitHub Pages hosting

### Documentation (`docs/`)
- All markdown documentation files
- Setup guides, troubleshooting, and reference docs

### Output (`output/`)
- Generated HTML reports and PDFs
- Not tracked in git (add to .gitignore if needed)

### Config (`config/`)
- Configuration files and API credentials
- Sensitive files should be in .gitignore

## Running Scripts

All scripts are designed to work from the project root:

```bash
# From project root
python scripts/generate_ucla_data_json_2026.py

# Or from scripts directory
cd scripts
python generate_ucla_data_json_2026.py
```

## Updating Apps Script

```bash
# From project root
./apps-script/push-script.sh

# Or manually
cd apps-script
cp google-apps-script-cbbd.js Code.gs
clasp push
```

## Adding New Files

- **New Python scripts**: Add to `scripts/`
- **New documentation**: Add to `docs/`
- **New data files**: Add to `data/[season]/`
- **New HTML reports**: Add to `output/`
- **New Apps Script code**: Add to `apps-script/`

