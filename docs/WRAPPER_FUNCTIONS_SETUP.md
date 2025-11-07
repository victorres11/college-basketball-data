# Library Wrapper Functions Setup

## Overview

The `LibraryWrappers.gs` file contains wrapper functions that allow you to call library functions directly from Google Sheets cells without needing the library identifier prefix.

Instead of: `=CBBData.GET_PLAYERS_FULL(A1)`  
You can use: `=GET_PLAYERS_FULL(A1)`

## How to Use

### Step 1: Add the Library to Your Spreadsheet

1. Open your Google Sheet
2. Go to **Extensions** → **Apps Script**
3. Click **Libraries** (📚 icon)
4. Add library with Script ID: `1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW`
5. Set identifier to: `CBBData`
6. Select **Development mode**

### Step 2: Add Wrapper Functions to Your Spreadsheet

1. In the same Apps Script editor (for your spreadsheet), click **+** to add a new file
2. Name it `LibraryWrappers` (or copy the contents from `LibraryWrappers.gs`)
3. Copy and paste the entire contents of `LibraryWrappers.gs` into the new file
4. Save the project

### Step 3: Use Functions in Cells

Now you can use functions directly in cells:

```
=GET_TEAM_META(A1)
=GET_PLAYERS_FULL(A1)
=GET_PLAYER_GAMES(A1, "Player Name")
=GET_TEAM_RANKINGS(A1)
```

## Available Functions

### Team Functions
- `GET_TEAM_META(url)` - Team metadata and records
- `GET_TEAM_RANKINGS(url)` - Conference and D1 rankings
- `GET_TEAM_SEASON_STATS(url)` - Aggregated season statistics
- `GET_TEAM_GAMES(url)` - Game-by-game team stats

### Player Functions
- `GET_PLAYERS_FULL(url)` - Complete player roster with all stats
- `GET_PLAYER_GAMES(url, playerName)` - Game-by-game stats for a player
- `GET_PLAYER_LAST_GAME(url, playerName)` - Most recent game
- `GET_PLAYER_LAST_GAME_SUMMARY(url, playerName)` - Last game as summary string
- `GET_PLAYER_PREVIOUS_SEASON_SUMMARY(url, playerName)` - Previous season summary
- `GET_PLAYER_LAST_N_GAMES(url, playerName, n)` - Last N games
- `GET_PLAYER_CAREER(url, playerName)` - Previous seasons only
- `GET_PLAYER_FULL_CAREER(url, playerName)` - All seasons (previous + current)
- `GET_ALL_PLAYERS_CAREERS(url)` - All players' careers in one table

### Utility Functions
- `GET_DATA(url, path)` - Generic JSON data getter
- `GET_PLAYER_STAT(url, playerName, statPath)` - Get specific player stat
- `GET_PLAYERS(url)` - List of all player names
- `DEBUG_JSON(url)` - Debug JSON structure

## Benefits

✅ **Simpler syntax** - No library prefix needed  
✅ **Auto-complete** - Functions appear in Sheets autocomplete  
✅ **Better UX** - Cleaner formulas in cells  
✅ **Easy updates** - Library updates automatically (Development mode)  
✅ **Customizable** - You can modify wrappers in your spreadsheet if needed  

## Notes

- The wrapper functions must be in the **spreadsheet's Apps Script** (not the library)
- Each spreadsheet needs its own copy of `LibraryWrappers.gs`
- The library identifier (`CBBData`) must match exactly in both the library settings and the wrapper file
- If you update the library, you may need to wait a minute for changes to propagate

## Troubleshooting

**Error: "CBBData is not defined"**
- Make sure the library is added with identifier `CBBData`
- Check that the library is in Development mode
- Wait 1-2 minutes for the library to load

**Error: "Function not found"**
- Make sure `LibraryWrappers.gs` is saved in your spreadsheet's Apps Script
- Check for syntax errors in the wrapper file
- Try refreshing the spreadsheet

**Functions work but show old behavior**
- Library might not be in Development mode
- Try removing and re-adding the library
- Check that the wrapper file calls `CBBData.FUNCTION_NAME` correctly

