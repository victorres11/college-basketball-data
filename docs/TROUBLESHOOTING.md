# Troubleshooting Library Functions

## #NAME? Error - Function Not Found

If you get a `#NAME?` error when trying to use library functions, try these steps:

### 1. Verify Library is Added Correctly

1. Open your Google Sheet
2. Go to **Extensions** → **Apps Script**
3. Click **Libraries** (📚 icon)
4. Verify the library is listed with:
   - Script ID: `1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW`
   - Version: **Development mode** (not a version number)
   - Identifier: `CBBData` (or whatever you set)

### 2. Check Library Status

In the Libraries panel, check:
- Status should show "Development mode" or be green/active
- If it shows an error, click on it to see details

### 3. Try Different Function Call Syntax

**Option A: With identifier (if you set `CBBData`):**
```excel
=CBBData.GET_PLAYERS_FULL(A1)
```

**Option B: Without identifier (if you left it blank):**
```excel
=GET_PLAYERS_FULL(A1)
```

**Option C: Try a simpler function first:**
```excel
=CBBData.GET_TEAM_META(A1)
```

### 4. Refresh/Recalculate

1. **Force recalculation**: In the cell with the formula, press `Ctrl+Shift+E` (or `Cmd+Shift+E` on Mac)
2. **Or**: Go to **File** → **Spreadsheet settings** → **Recalculate** → **On change and every minute**
3. **Or**: Delete and re-enter the formula

### 5. Wait for Library to Load

- Libraries can take 1-2 minutes to load initially
- Try waiting a minute and then recalculating

### 6. Check URL in A1

Make sure cell A1 contains a valid URL:
```
https://yourusername.github.io/repo/data/2026/ucla_scouting_data_2026.json
```

### 7. Verify Functions Exist in Library

Go to the Apps Script editor:
https://script.google.com/d/1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW/edit

Search for `GET_PLAYERS_FULL` to confirm it exists.

### 8. Re-add Library

If nothing works:
1. Remove the library from Libraries
2. Re-add it with the Script ID
3. Make sure to select **Development mode**
4. Set identifier to `CBBData`
5. Wait 1-2 minutes
6. Try the function again

### 9. Check for Script Errors

In the Apps Script editor for your **spreadsheet** (not the library):
1. Go to **Extensions** → **Apps Script**
2. Check the **Execution log** for any errors
3. Run a test: Tools → Execution log

### 10. Verify Library Sharing

1. Go to library script: https://script.google.com/d/1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW/edit
2. **Project Settings** (⚙️)
3. Make sure **"Share script with others"** is checked

## Common Issues

### Issue: Library shows but functions don't work
**Solution**: Make sure you're using Development mode, not a version number

### Issue: Functions work without identifier but not with identifier
**Solution**: Check the identifier name - it's case-sensitive. `CBBData` is different from `cbbdata`

### Issue: Some functions work but others don't
**Solution**: The library might not have loaded completely. Try removing and re-adding.

### Issue: Works in one spreadsheet but not another
**Solution**: Each spreadsheet needs to have the library added separately

## Available Functions

- `GET_TEAM_META(url)`
- `GET_TEAM_RANKINGS(url)`
- `GET_PLAYERS_FULL(url)`
- `GET_PLAYER_GAMES(url, playerName)`
- `GET_TEAM_GAMES(url)`
- `GET_TEAM_SEASON_STATS(url)`

