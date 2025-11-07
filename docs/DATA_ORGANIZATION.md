# Data Organization Guide

This document explains how the project organizes data files by season.

## Directory Structure

```
cbbd/
├── data/
│   ├── 2025/          # 2024-25 season data (2025 API season)
│   │   ├── msu_scouting_data_2025.json
│   │   ├── ucla_scouting_data_2025.json
│   │   └── eastern_washington_scouting_data_2025.json
│   └── 2026/          # 2025-26 season data (2026 API season)
│       ├── msu_scouting_data_2026.json
│       ├── ucla_scouting_data_2026.json
│       └── eastern_washington_scouting_data_2026.json
├── msu_scouting_data.json              # Legacy: 2025 season (backward compatibility)
├── ucla_scouting_data.json             # Legacy: 2025 season (backward compatibility)
├── eastern_washington_scouting_data.json # Legacy: 2025 season (backward compatibility)
└── generate_*_data_json.py            # Legacy generators for 2025 season
└── generate_*_data_json_2026.py       # New generators for 2026 season
```

## Season Organization

### 2025 Season (2024-25 Academic Year)
- **API Season**: 2025
- **Date Range**: November 4, 2024 - March 2025
- **Generator Scripts**: 
  - `generate_msu_data_json.py`
  - `generate_ucla_data_json.py`
  - `generate_eastern_washington_data_json.py`
- **Output Files**: 
  - Root: `*_scouting_data.json` (for backward compatibility with GitHub Pages)
  - Organized: `data/2025/*_scouting_data_2025.json` (optional, for organization)

### 2026 Season (2025-26 Academic Year)
- **API Season**: 2026
- **Date Range**: November 4, 2025 - March 2026
- **Generator Scripts**: 
  - `generate_msu_data_json_2026.py`
  - `generate_ucla_data_json_2026.py`
  - `generate_eastern_washington_data_json_2026.py`
- **Output Files**: 
  - Organized: `data/2026/*_scouting_data_2026.json`

## Generating Data

### Generate 2025 Season Data (Legacy)
```bash
python3 generate_msu_data_json.py
python3 generate_ucla_data_json.py
python3 generate_eastern_washington_data_json.py
```

### Generate 2026 Season Data (Current)
```bash
python3 generate_msu_data_json_2026.py
python3 generate_ucla_data_json_2026.py
python3 generate_eastern_washington_data_json_2026.py
```

## GitHub Pages Compatibility

### Backward Compatibility
The legacy files in the root directory (`msu_scouting_data.json`, etc.) remain for backward compatibility with existing GitHub Pages URLs and integrations.

**Existing URLs continue to work:**
- `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/msu_scouting_data.json`
- `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/ucla_scouting_data.json`
- `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/eastern_washington_scouting_data.json`

### New Season-Specific URLs
New season-specific files are accessible via:
- `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/data/2026/msu_scouting_data_2026.json`
- `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/data/2026/ucla_scouting_data_2026.json`
- `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/data/2026/eastern_washington_scouting_data_2026.json`

## File Naming Convention

- **Legacy files** (root): `{team}_scouting_data.json` (defaults to 2025 season)
- **Organized files**: `data/{season}/{team}_scouting_data_{season}.json`

## Migration Notes

When transitioning to a new season:
1. Create new generator scripts with `_2026` suffix
2. Update season parameter from 2025 to 2026
3. Update date ranges to new season dates
4. Output files to `data/{season}/` directory
5. Keep legacy files in root for backward compatibility (optional)

## Future Seasons

For future seasons (2027, 2028, etc.):
1. Copy the latest generator script and rename with new season suffix
2. Update all season references (2026 → 2027, etc.)
3. Update date ranges
4. Update output directory (`data/2027/`)
5. Update season label in JSON output (`'2026-27'` → `'2027-28'`)

