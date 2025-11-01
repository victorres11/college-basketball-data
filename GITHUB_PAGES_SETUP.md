# Setting Up GitHub Pages for JSON Files

## Quick Setup

1. **Create a new repository on GitHub**
   - Go to https://github.com/new
   - Name it something like `college-basketball-data` or `msu-ucla-scouting`
   - Make it PUBLIC (required for GitHub Pages)
   - Don't initialize with README

2. **Push your code to GitHub**
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

3. **Enable GitHub Pages**
   - Go to your repository on GitHub
   - Click Settings → Pages
   - Under "Source", select "Deploy from a branch"
   - Select branch: `main`
   - Select folder: `/ (root)`
   - Click Save

4. **Your JSON files will be accessible at:**
   - `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/msu_scouting_data.json`
   - `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/ucla_scouting_data.json`

## Using in Google Sheets

In Google Sheets, use the `IMPORTDATA` function:

```excel
=IMPORTDATA("https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/msu_scouting_data.json")
```

This will fetch the JSON data. You can then parse it using `SPLIT`, `REGEXEXTRACT`, or other functions.

## Alternative: Direct File Access

If you just want to host the JSON files without the whole repo:

1. Create a repository named `YOUR_USERNAME.github.io` (this enables user pages)
2. Upload just the JSON files to the root
3. Access them at:
   - `https://YOUR_USERNAME.github.io/msu_scouting_data.json`
   - `https://YOUR_USERNAME.github.io/ucla_scouting_data.json`

## JSON Structure

The JSON files contain:
- Team information
- All players with:
  - Basic info (name, jersey, position, height, class, hometown, high school)
  - Season totals (all stats with per-game averages)
  - Complete game-by-game data for the regular season

## Update Schedule

To refresh the data:
1. Run the generator scripts:
   ```bash
   python3 generate_msu_data_json.py
   python3 generate_ucla_data_json.py
   ```
2. Commit and push the updated JSON files:
   ```bash
   git add *_scouting_data.json
   git commit -m "Update scouting data"
   git push
   ```
3. Changes will be live within 1-2 minutes


