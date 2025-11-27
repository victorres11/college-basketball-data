# Handoff Package - Basketball Roster API

## What to Give the Other App

### Essential Files (Copy These)

1. **`roster_cache_reader.py`** - The library to read cached rosters
2. **`rosters_cache/`** - Directory with all cached roster data
3. **`rosters_index.json`** - Index of all cached teams
4. **`team_ids_mapping.json`** - Team ID to name mapping (365 teams)

### Optional Files (For Reference)

- `cache_all_rosters.py` - Script to refresh cache (if they need to update)
- `CACHING_STRATEGY.md` - Detailed caching documentation

---

## Quick Start for Other App

### Step 1: Copy These Files

```
their-app/
├── roster_cache_reader.py
├── rosters_cache/
│   ├── 223_classes.json
│   ├── 51_classes.json
│   └── ... (all team class files)
├── rosters_index.json
└── team_ids_mapping.json
```

### Step 2: Use the Code

```python
from roster_cache_reader import RosterCache

# Initialize (no setup needed, just works)
cache = RosterCache()

# Get player classes for any team
team_id = "223"  # Oregon Ducks
players = cache.get_player_classes(team_id)

# Each player has: name, jersey, class
for player in players:
    print(f"{player['name']}: {player['class']}")
```

### Step 3: Find Team IDs

```python
import json

# Load team mapping
with open('team_ids_mapping.json', 'r') as f:
    teams = json.load(f)

# Search for team
team_name = "Texas A&M"
for team_id, name in teams.items():
    if team_name.lower() in name.lower():
        print(f"Team ID: {team_id}, Name: {name}")
        break
```

---

## API Reference

### RosterCache Class

```python
cache = RosterCache()

# Get all player classes for a team
players = cache.get_player_classes(team_id)
# Returns: [{'name': '...', 'jersey': '...', 'class': '...'}, ...]

# Get specific player's class by jersey
class_value = cache.get_class_by_jersey(team_id, "12")
# Returns: "SR" or None

# Get specific player's class by name
class_value = cache.get_class_by_name(team_id, "Drew Carter")
# Returns: "SR" or None

# Check if team is cached
is_cached = cache.is_cached(team_id)
# Returns: True/False

# Get cache statistics
stats = cache.get_cache_stats()
# Returns: {'total_teams': 365, 'total_players': 5000+, ...}
```

---

## Data Format

### Player Object

```python
{
    'name': 'Drew Carter',
    'jersey': '12',
    'class': 'SR'  # FR, SO, JR, SR, or GS
}
```

### Class Values

- `FR` - Freshman
- `SO` - Sophomore
- `JR` - Junior
- `SR` - Senior
- `GS` - Graduate Student

---

## Complete Example

```python
from roster_cache_reader import RosterCache
import json

# 1. Initialize cache
cache = RosterCache()

# 2. Find team ID
with open('team_ids_mapping.json', 'r') as f:
    teams = json.load(f)

team_name = "Oregon Ducks"
team_id = None
for tid, name in teams.items():
    if team_name.lower() in name.lower():
        team_id = tid
        break

# 3. Get player classes
if team_id:
    players = cache.get_player_classes(team_id)
    
    # Filter by class
    seniors = [p for p in players if p['class'] == 'SR']
    print(f"Seniors: {len(seniors)}")
    
    # Get specific player
    player_class = cache.get_class_by_jersey(team_id, "12")
    print(f"Jersey #12 class: {player_class}")
```

---

## File Structure

```
rosters_cache/
├── 223_classes.json      # Oregon Ducks classes
├── 51_classes.json       # Texas A&M classes
├── 27_classes.json       # North Carolina classes
└── ... (one file per team)

rosters_index.json        # Index of all cached teams
team_ids_mapping.json     # Team ID → Name mapping
roster_cache_reader.py    # The library to use
```

---

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)
- No API key needed (all data is cached locally)

---

## Updating the Cache (Optional)

If they need to refresh the cache:

```bash
python3 cache_all_rosters.py
```

This will:
- Fetch all rosters from API
- Update cache files
- Takes ~3-5 minutes

---

## That's It!

The other app just needs:
1. Copy the files
2. Import `RosterCache`
3. Call `get_player_classes(team_id)`

No API calls, no setup, instant results!

