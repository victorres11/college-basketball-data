# CBB Data Generator Web UI

A simple Flask web application for generating college basketball team data.

## Features

- Searchable dropdown of all NCAA basketball teams
- Generate comprehensive team statistics and player data
- Automatic push to GitHub for hosting
- Real-time progress updates

## Setup

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export CBB_API_KEY=your_api_key_here
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the UI:**
   Open http://localhost:5001 in your browser

## Deployment to Render.com

1. **Push code to GitHub:**
   ```bash
   git add web-ui/
   git commit -m "Add web UI"
   git push
   ```

2. **Create new Web Service on Render:**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Use the `render.yaml` file (auto-detected) OR manually set:
     - **Build Command**: `cd web-ui && pip install -r requirements.txt`
     - **Start Command**: `cd web-ui && gunicorn app:app --bind 0.0.0.0:$PORT`
   - Add environment variables:
     - `CBB_API_KEY`: Your API key
     - `GIT_USER_NAME`: Your git username (for GitHub pushes)
     - `GIT_USER_EMAIL`: Your git email (for GitHub pushes)
     - `FLASK_ENV`: `production`

3. **Git Configuration:**
   - The app needs git configured to push to GitHub
   - Render will use the git config from your repository
   - Make sure your repository has proper git credentials set up
   - Alternatively, you can set git config in the build command

## Project Structure

```
web-ui/
├── app.py              # Flask application
├── generator.py        # Team data generation logic
├── github_handler.py   # GitHub push functionality
├── templates/
│   └── index.html     # Main UI
├── static/
│   ├── css/
│   │   └── style.css  # Styling
│   └── js/
│       └── app.js      # Frontend logic
└── requirements.txt     # Python dependencies
```

## Usage

1. Search for a team in the dropdown
2. Select the team
3. Choose the season
4. Click "Generate Data"
5. Wait for generation to complete (2-3 minutes)
6. Get the GitHub Pages URL for the generated JSON file

## Notes

- Generation takes 2-3 minutes per team
- Requires valid API key
- Requires git credentials for GitHub push
- Jobs are stored in memory (lost on restart)

