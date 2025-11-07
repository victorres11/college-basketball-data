# Development Mode Setup Guide

This guide explains how to set up your Google Apps Script library in **Development Mode** so changes automatically propagate to all spreadsheets.

## What is Development Mode?

Development Mode allows spreadsheets to use the **latest code** from your Apps Script project. When you push changes with `clasp push`, all spreadsheets using development mode automatically get the updates - no version deployment needed!

## Setup Steps

### 1. Enable Library Sharing

1. Go to your Apps Script editor:
   https://script.google.com/d/1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW/edit

2. Click **Project Settings** (gear icon ⚙️ in the left sidebar)

3. Check **"Share script with others"** (or "Share script")
   - This must be enabled for development mode to work

4. Save the settings

### 2. Add Library to Spreadsheet in Development Mode

1. Open your Google Sheet

2. Go to **Extensions** → **Apps Script**

3. Click **Libraries** (📚 icon on the left sidebar)

4. Click **+** (Add a library)

5. Enter the Script ID:
   ```
   1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW
   ```

6. **IMPORTANT**: In the version dropdown, select **"Development mode"**
   - This should appear as "Development mode" or "HEAD"
   - If you only see version numbers (1, 2, 3...), go back to Step 1 and ensure "Share script with others" is checked

7. (Optional) Set an identifier (e.g., `CBBData`)
   - If you set an identifier, you'll use functions like `=CBBData.GET_TEAM_META(A1)`
   - If you leave it blank, you can use functions directly like `=GET_TEAM_META(A1)`

8. Click **Add**

### 3. Verify Development Mode

After adding, you should see the library listed with:
- Status: **Development mode** (not a version number)
- Updates will apply automatically

## Workflow with Development Mode

Once set up, updating all spreadsheets is simple:

1. **Make changes** to `google-apps-script-cbbd.js`

2. **Push the changes**:
   ```bash
   ./push-script.sh
   ```
   Or manually:
   ```bash
   cp google-apps-script-cbbd.js Code.gs
   clasp push
   ```

3. **That's it!** All spreadsheets using development mode will automatically get the updates

4. **Test in a spreadsheet** - the functions should use the new code immediately

## Troubleshooting

### "Development mode" option not showing

- **Solution**: Make sure "Share script with others" is enabled in Project Settings
- Go back to the Apps Script editor → Project Settings → Enable sharing

### Changes not propagating

- **Check**: Verify the library shows "Development mode" (not a version number)
- **Wait**: Sometimes it takes 1-2 minutes for changes to propagate
- **Refresh**: Try refreshing the spreadsheet or recalculating the cells

### Still seeing old behavior

- **Clear cache**: In the spreadsheet, go to File → Spreadsheet settings → Recalculate
- **Recheck library**: Make sure it's still in Development mode (not accidentally changed to a version)

## Benefits of Development Mode

✅ **Automatic updates** - No manual version deployment needed  
✅ **Instant testing** - Changes appear immediately in spreadsheets  
✅ **Simplified workflow** - Just push and it's live  
✅ **Perfect for development** - Great during active development phase  

## When to Use Versioned Instead

Consider using versioned libraries when:
- You want to control when updates are applied
- You need production stability (don't want automatic updates)
- You want to test changes before rolling out to all users
- You're maintaining multiple versions for different use cases

## Summary

With Development Mode:
- Setup once per spreadsheet
- Push changes with `./push-script.sh`
- All spreadsheets update automatically
- No version management needed

