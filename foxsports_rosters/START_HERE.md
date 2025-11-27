# START HERE - Basketball Roster API

## For the Other App/Developer

This package gives you **instant access to player CLASS data** for all 365 college basketball teams.

**No API calls needed. Everything is cached locally.**

---

## What You Get

✅ **365 teams** cached  
✅ **Instant access** (1-5ms, no network)  
✅ **No API key needed**  
✅ **Works offline**  
✅ **Simple API**

---

## Quick Start (3 Steps)

### 1. Copy These Files

```
your-app/
├── roster_cache_reader.py    ← The library
├── rosters_cache/            ← All cached data
│   ├── 223_classes.json
│   ├── 51_classes.json
│   └── ... (365 files)
├── rosters_index.json        ← Index
└── team_ids_mapping.json     ← Team lookup
```

### 2. Use It

```python
from roster_cache_reader import RosterCache

cache = RosterCache()

# Get player classes for Oregon (team ID: 223)
players = cache.get_player_classes("223")

for player in players:
    print(f"{player['name']}: {player['class']}")
```

### 3. Find Team IDs

```python
import json

with open('team_ids_mapping.json', 'r') as f:
    teams = json.load(f)

# Search for team
for team_id, name in teams.items():
    if "texas a&m" in name.lower():
        print(f"Team ID: {team_id}")
        break
```

---

## Complete Example

```python
from roster_cache_reader import RosterCache
import json

# Initialize
cache = RosterCache()

# Find team ID
with open('team_ids_mapping.json', 'r') as f:
    teams = json.load(f)

team_id = "223"  # Oregon Ducks (or search for it)

# Get all player classes
players = cache.get_player_classes(team_id)

# Print results
print(f"Team: {teams[team_id]}")
print(f"Players: {len(players)}")
for player in sorted(players, key=lambda x: int(x['jersey']) if x['jersey'].isdigit() else 999):
    print(f"  #{player['jersey']} {player['name']:<30} {player['class']}")

# Get specific player's class
jersey = "12"
player_class = cache.get_class_by_jersey(team_id, jersey)
print(f"\nJersey #{jersey} class: {player_class}")
```

---

## API Methods

```python
cache = RosterCache()

# Get all players with classes
players = cache.get_player_classes(team_id)

# Get class by jersey number
class_value = cache.get_class_by_jersey(team_id, "12")

# Get class by player name
class_value = cache.get_class_by_name(team_id, "Drew Carter")

# Check if team is cached
is_cached = cache.is_cached(team_id)

# Get stats
stats = cache.get_cache_stats()
```

---

## Data Format

Each player object:
```python
{
    'name': 'Drew Carter',
    'jersey': '12',
    'class': 'SR'  # FR, SO, JR, SR, or GS
}
```

---

## Common Team IDs

- Oregon Ducks: `223`
- Texas A&M: `51`
- North Carolina: `27`
- Duke: `23`
- Kansas: `44`

See `team_ids_mapping.json` for all 365 teams.

---

## Requirements

- Python 3.6+
- No dependencies (standard library only)
- No API key needed

---

## Need More Info?

See `HANDOFF_PACKAGE.md` for complete documentation.

---

## That's It!

Just copy the files and use `RosterCache`. No setup, no API calls, instant results.

