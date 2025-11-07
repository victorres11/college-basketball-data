# Quick Start Guide

## What Was Created

A complete Flask web UI for generating college basketball team data with:

✅ **Searchable team dropdown** - All 1,500+ NCAA teams  
✅ **Simple interface** - Just select team and click generate  
✅ **Progress tracking** - Real-time status updates  
✅ **Auto-deploy** - Automatically pushes to GitHub  
✅ **Production-ready** - Configured for Render.com deployment  

## Files Created

```
web-ui/
├── app.py                 # Flask backend (main application)
├── generator.py           # Team data generation logic
├── github_handler.py      # GitHub push functionality
├── templates/
│   └── index.html        # Main UI page
├── static/
│   ├── css/style.css     # Styling
│   └── js/app.js         # Frontend logic
├── requirements.txt       # Python dependencies
├── render.yaml           # Render.com configuration
└── README.md             # Full documentation
```

## Test Locally (5 minutes)

1. **Set API key:**
   ```bash
   export CBB_API_KEY=your_api_key_here
   ```

2. **Install dependencies:**
   ```bash
   cd web-ui
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```

4. **Open browser:**
   - Go to http://localhost:5001
   - Search for "Oregon" (or any team)
   - Select the team
   - Click "Generate Data"
   - Wait 2-3 minutes
   - Get the GitHub Pages URL!

## Deploy to Render.com (10 minutes)

1. **Push to GitHub:**
   ```bash
   git add web-ui/
   git commit -m "Add web UI"
   git push
   ```

2. **Create Render service:**
   - Go to https://render.com
   - New → Web Service
   - Connect GitHub repo
   - Render will auto-detect `render.yaml`

3. **Set environment variables:**
   - `CBB_API_KEY`: Your API key
   - `GIT_USER_NAME`: Your GitHub username
   - `GIT_USER_EMAIL`: Your GitHub email

4. **Deploy!**
   - Click "Create Web Service"
   - Wait for build
   - Your app is live!

## How It Works

1. **User selects team** → Frontend sends team name to backend
2. **Backend starts job** → Creates background thread
3. **Generator runs** → Fetches all team data (2-3 min)
4. **Progress updates** → Frontend polls status every 2 seconds
5. **GitHub push** → Generated JSON pushed to repo
6. **User gets URL** → GitHub Pages URL displayed

## Next Steps

- ✅ Test locally first
- ✅ Deploy to Render
- ✅ Test with a few teams
- ✅ Share the URL!

## Troubleshooting

**"Module not found" errors:**
- Make sure you're in the `web-ui/` directory
- Or run: `cd web-ui && python app.py`

**"API key not found":**
- Set: `export CBB_API_KEY=your_key`
- Or create `.env` file with: `CBB_API_KEY=your_key`

**"GitHub push failed":**
- Check git is configured
- Verify you have push access to the repo

## Notes

- Generation takes 2-3 minutes per team
- Jobs stored in memory (lost on restart)
- Team list cached after first load
- Works best with 2026 season (other seasons have limited support)

