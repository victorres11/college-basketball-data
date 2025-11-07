# Google Apps Script Library Information

This document contains the library information for the CBB Data Functions Library.

## Library Details

**Library Name**: CBB Data Functions Library

**Script ID**: `1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW`

**Deployment ID**: `AKfycbzj0i60lfwnrbtrkDLCgc7Z0MVOFrKaACib_Q78VZEPzUzl7LbPqbJqpkuyC9qaYZEe`

**Library URL**: https://script.google.com/macros/library/d/1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW/1

**Editor URL**: https://script.google.com/d/1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW/edit

**Current Version**: 1

## How to Add to a Spreadsheet

1. Open your Google Sheet
2. Go to **Extensions** → **Apps Script**
3. Click **Libraries** (📚 icon on the left sidebar)
4. Click **+** to add a library
5. Enter the Script ID: `1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW`
6. **IMPORTANT**: Select **"Development mode"** (or "HEAD") - NOT a specific version number
   - This ensures changes automatically propagate when you push updates
7. Give it an identifier (e.g., `CBBData` or leave as default)
8. Click **Add**

### Using Development Mode

**Development mode** means the spreadsheet uses the latest code from your Apps Script project. When you push changes with `clasp push`, all spreadsheets using development mode will automatically get the updates.

**Note**: If you see version numbers (1, 2, 3, etc.) instead of "Development mode", you may need to:
- Make sure the library is set to "Share script with others" in Project Settings
- Or use the version selector dropdown and look for "Development mode" or "HEAD"

## Available Functions

Once added, you can use these functions in your spreadsheet:

- `GET_TEAM_META(url)` - Get team metadata and records
- `GET_TEAM_RANKINGS(url)` - Get team conference and D1 rankings
- `GET_PLAYERS_FULL(url)` - Get complete player roster with all stats
- `GET_PLAYER_GAMES(url, playerName)` - Get game-by-game stats for a player
- `GET_TEAM_GAMES(url)` - Get all games with team stats
- `GET_TEAM_SEASON_STATS(url)` - Get aggregated team season statistics

## Updating the Library

### For Development Mode (Recommended)

When spreadsheets are using **Development mode**, updates are automatic:

1. Make changes to `google-apps-script-cbbd.js`
2. Run `./push-script.sh` or `clasp push`
3. **That's it!** All spreadsheets using development mode will automatically get the updates
4. No need to deploy new versions or manually update spreadsheets

### For Versioned Libraries

If spreadsheets are using a specific version number:

1. Make changes to `google-apps-script-cbbd.js`
2. Run `./push-script.sh` or `clasp push`
3. In the Apps Script editor, go to **Deploy** → **New deployment**
4. Choose **Library** as the type
5. Create a new version number
6. Spreadsheets will need to manually update to the new version

**Recommendation**: Use Development mode for active development and testing. Use versioned libraries for production stability when you want to control when updates are applied.

## Notes

- All functions require a URL pointing to a JSON file (typically hosted on GitHub Pages)
- The URL should be in cell A1 or passed as a parameter
- Example URL format: `https://yourusername.github.io/repo/data/2026/ucla_scouting_data_2026.json`

