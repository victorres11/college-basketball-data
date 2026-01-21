# FoxSports Roster Cache

This directory contains cached roster data from FoxSports, including player heights, weights, positions, and class years.

## Directory Structure

```
foxsports_rosters/
├── rosters_cache/           # Cached roster files by FoxSports team ID
│   ├── {team_id}.json       # Full roster data
│   └── {team_id}_classes.json  # Player names, jerseys, and class years
├── team_ids_mapping.json    # FoxSports ID → team name mapping
├── roster_cache_reader.py   # Python library to read cache files
└── generate_team_id_mapping.py  # DEPRECATED - see note below
```

## Important: Service ID Architecture

**Each external service has its own ID system. Never assume IDs match between services.**

- FoxSports uses its own numeric team IDs (e.g., 90 = Northwestern)
- The CBB API uses different numeric team IDs
- While many IDs happen to match, this is coincidental and not guaranteed

## How to Look Up FoxSports IDs

FoxSports IDs are stored in the centralized team registry at `config/team_registry.json`:

```python
from scripts.team_lookup import get_team_lookup

lookup = get_team_lookup()
foxsports_id = lookup.lookup("Northwestern", "foxsports_id")  # → "90"
```

The generator uses this to load the correct cache file:
```python
cache_file = f"rosters_cache/{foxsports_id}_classes.json"
```

## Cache File Format

### `{team_id}_classes.json`
```json
[
  {"name": "Nick Martinelli", "jersey": "2", "class": "SR"},
  {"name": "Jayden Reid", "jersey": "4", "class": "JR"},
  ...
]
```

### `{team_id}.json`
Full roster data including heights, weights, positions, etc.

## Regenerating the Cache

To refresh roster data from FoxSports:
1. Run the FoxSports scraper for specific teams
2. Cache files are automatically created/updated

## Deprecated Files

- `cbb_to_foxsports_team_mapping.json` - **DELETED**: This mapping is now stored in the team registry
- `generate_team_id_mapping.py` - **DEPRECATED**: FoxSports IDs are now managed in `scripts/generate_team_registry.py`
