# Google Apps Script Push-to-Deploy Setup

This guide explains how to push changes from your local repository directly to Google Apps Script.

## Prerequisites

1. **Install clasp** (if not already installed):
   ```bash
   npm install -g @google/clasp
   ```

2. **Enable Apps Script API**:
   - Go to https://script.google.com/home/usersettings
   - Turn ON "Google Apps Script API"

## Initial Setup (One-Time)

### Step 1: Create the Library Script in Google Apps Script

1. Go to https://script.google.com
2. Click "New Project"
3. Name it "CBB Data Functions Library"
4. Copy the entire contents of `google-apps-script-cbbd.js` into the script editor
5. Save the project (Ctrl+S or Cmd+S)
6. Go to Project Settings (gear icon) → Copy the **Script ID**

### Step 2: Link Local Repo to Google Apps Script

**Option A: If you already created the script manually (recommended):**

1. Create `.clasp.json` file with your Script ID:
   ```bash
   echo '{"scriptId": "YOUR_SCRIPT_ID_HERE", "rootDir": "."}' > .clasp.json
   ```
   Replace `YOUR_SCRIPT_ID_HERE` with the Script ID from Step 1.

2. Login to clasp:
   ```bash
   clasp login
   ```
   This will open a browser window for authentication.

**Option B: Create new script from command line:**

```bash
clasp login
clasp create --type standalone --title "CBB Data Functions Library" --rootDir .
```

This will:
- Create a new Google Apps Script project
- Create `.clasp.json` with the Script ID
- Link it to your local directory

## Library Information

**Library URL**: https://script.google.com/macros/library/d/1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW/1

**Script ID**: `1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW`

**Deployment ID**: `AKfycbzj0i60lfwnrbtrkDLCgc7Z0MVOFrKaACib_Q78VZEPzUzl7LbPqbJqpkuyC9qaYZEe`

**Version**: 1

### Adding the Library to a Spreadsheet

1. Open your Google Sheet
2. Go to **Extensions** → **Apps Script**
3. Click **Libraries** (📚 icon on the left sidebar)
4. Click **+** to add a library
5. Enter the Script ID: `1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW`
6. Select the version (or "Latest" for automatic updates)
7. Click **Add**

After adding, you can use all the functions in your spreadsheet (e.g., `=GET_TEAM_META(A1)`, `=GET_PLAYERS_FULL(A1)`, etc.)

## Daily Workflow

### Push Changes to Google Apps Script

After making changes to `google-apps-script-cbbd.js`:

**Option 1: Use the helper script (recommended):**
```bash
./push-script.sh
```

**Option 2: Manual push:**
```bash
# Copy script to Code.gs (clasp expects Code.gs)
cp google-apps-script-cbbd.js Code.gs

# Push to Google Apps Script
clasp push

# Or push and create a new version
clasp push && clasp version "Updated description"
```

**Note:** The script automatically copies `google-apps-script-cbbd.js` to `Code.gs` before pushing, since clasp expects the file to be named `Code.gs`.

### View Status

```bash
# Check what files would be pushed
clasp status

# Open the script in browser
clasp open

# Pull latest from Google Apps Script (if edited in browser)
clasp pull
```

## Making the Script Available as a Library

### Step 1: Enable Library Sharing

1. Go to the Apps Script editor: https://script.google.com/d/1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW/edit
2. Click **Project Settings** (gear icon ⚙️)
3. Check **"Share script with others"** (or "Share script" depending on your UI)
4. Save the settings

### Step 2: Add Library to Spreadsheets (Development Mode)

1. Open each Google Sheet that needs the functions
2. Go to **Extensions** → **Apps Script**
3. Click **Libraries** (📚 icon on the left sidebar)
4. Click **+** to add a library
5. Enter the Script ID: `1lxJFaRphbCH3wQP68Z2G82c0kYkCqjVzK2DXu29VchNLS5bMVNg3EvdW`
6. **CRITICAL**: In the version dropdown, select **"Development mode"** (or "HEAD")
   - This is NOT a version number - it's the HEAD/latest version
   - If you only see version numbers, make sure "Share script with others" is enabled
7. Give it an identifier (e.g., `CBBData` or leave as default)
8. Click **Add**

### Step 3: Using Functions in Spreadsheets

**Option A: If you gave it an identifier (e.g., `CBBData`):**
```excel
=CBBData.GET_TEAM_META(A1)
=CBBData.GET_PLAYERS_FULL(A1)
```

**Option B: If you didn't set an identifier (default):**
```excel
=GET_TEAM_META(A1)
=GET_PLAYERS_FULL(A1)
```

## Development Mode vs Versioned

- **Development Mode** (Recommended):
  - ✅ Changes push immediately to all spreadsheets
  - ✅ No need to deploy new versions
  - ✅ Perfect for active development
  - ✅ Just run `./push-script.sh` and all spreadsheets update automatically
  
- **Versioned**:
  - ❌ Requires deploying new version for each change
  - ❌ Each spreadsheet must manually update to new version
  - ✅ Better for production when you want to control update timing

## Automated Push (Optional)

You can create a git hook to auto-push on commit:

```bash
# Create post-commit hook
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
if git diff --name-only HEAD~1 | grep -q "google-apps-script-cbbd.js"; then
  echo "Google Apps Script file changed, pushing..."
  clasp push
fi
EOF
chmod +x .git/hooks/post-commit
```

## Troubleshooting

- **"clasp: command not found"**: Make sure clasp is installed globally: `npm install -g @google/clasp`
- **"Permission denied"**: Run `clasp login` again
- **"Script not found"**: Check that `.clasp.json` has the correct Script ID
- **"File not found"**: Ensure `google-apps-script-cbbd.js` exists in the root directory

## Files Created

- `.clasp.json` - Script ID configuration (DO NOT commit to git - contains your Script ID)
- `.appsscript.json` - Project settings
- `.claspignore` - Files to exclude from push

