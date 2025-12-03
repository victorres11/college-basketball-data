# KenPom API Setup Guide

## Overview

The KenPom integration now uses the official KenPom API instead of web scraping. This is more reliable, faster, and doesn't require cookies or proxy services.

## Setup

### Local Development

1. **Create API credentials file:**
   ```bash
   cd misc_data_sources/kenpom
   # Create kp_api_creds.txt with your API key
   ```

2. **Add your API key:**
   ```
   api_key=your_api_key_here
   ```

3. **The file is gitignored** - it won't be committed to the repository.

### Production (Render.com)

1. **Go to Render Dashboard** → Your Service → Environment

2. **Add environment variable:**
   - **Key**: `KENPOM_API_KEY`
   - **Value**: Your KenPom API key
   - **Mark as Secret**: ✓ (recommended)

3. **Save and redeploy**

## How It Works

The `kenpom_api.py` script:
1. Loads API key from environment variable (production) or file (local)
2. Looks up team ID from team name using the `teams` endpoint
3. Fetches data from multiple API endpoints:
   - `ratings` - Adj Efficiency, Adj Tempo, SOS, Avg Poss Length
   - `four-factors` - Four Factors statistics
   - `misc-stats` - Miscellaneous stats (3P%, 2P%, FT%, etc.)
   - `pointdist` - Point distribution
   - `height` - Personnel stats (height, experience, continuity, bench)
4. Transforms API responses to match the original scraping format
5. Calculates D-1 averages where needed

## API Endpoints Used

- **ratings**: Team ratings, efficiency, tempo, strength of schedule
- **four-factors**: Effective FG%, Turnover %, Off. Reb. %, FTA/FGA
- **misc-stats**: Shooting percentages, block%, steal%, assist rates
- **pointdist**: Point distribution (3-pointers, 2-pointers, free throws)
- **height**: Team height, experience, continuity, bench strength
- **teams**: Team lookup (name to ID mapping)

## Data Retrieved

All data from the original scraping is available via the API:

✅ **Adj. Efficiency** - Offense and Defense with rankings
✅ **Adj. Tempo** - Combined tempo with ranking
✅ **Avg. Poss. Length** - Offense and Defense
✅ **Four Factors** - Effective FG%, Turnover %, Off. Reb. %, FTA/FGA
✅ **Miscellaneous Stats** - 3P%, 2P%, FT%, Block%, Steal%, Non-Stl TO%
✅ **Style Components** - 3PA/FGA, A/FGM
✅ **Point Distribution** - 3-Pointers, 2-Pointers, Free Throws
✅ **Strength of Schedule** - Overall, Non-conference, Offense, Defense
✅ **Personnel** - Bench Minutes, D-1 Experience, Minutes Continuity, Average Height

❌ **2-Foul Participation** - Not available in API (this stat is not provided by KenPom API)

## Troubleshooting

### API Key Not Found

- **Error**: "KenPom API key not found"
- **Solution**: Set `KENPOM_API_KEY` environment variable or create `kp_api_creds.txt` file

### Team Not Found

- **Error**: "Team 'X' not found in KenPom API"
- **Solution**: Check team name spelling. The API uses exact team names. Common variations are handled automatically.

### Authentication Failed

- **Error**: "KenPom API authentication failed"
- **Solution**: Verify your API key is correct and has not expired

## Advantages Over Scraping

- ✅ No IP blocking issues
- ✅ No cookie management needed
- ✅ Faster and more reliable
- ✅ Official API support
- ✅ Structured JSON responses
- ✅ No HTML parsing required

