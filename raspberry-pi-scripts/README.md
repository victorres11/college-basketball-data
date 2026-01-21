# Raspberry Pi - Barttorvik Fetcher

This script fetches college basketball teamsheets data from barttorvik.com and uploads it to S3 for the main Render app to consume.

## Why Run on a Pi?

Barttorvik uses Cloudflare protection that frequently blocks requests from cloud IPs (like Render). Running from a residential IP (your home Pi) is much more reliable.

## Setup

### 1. Install Python dependencies

```bash
cd raspberry-pi-scripts
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install Playwright browser

```bash
playwright install chromium
```

Note: On Raspberry Pi, you may need system dependencies:
```bash
sudo apt-get install -y libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
```

### 3. Configure AWS credentials

Copy the example env file and fill in your credentials:
```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

Or set them directly:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### 4. Test the script

```bash
# Dry run (no S3 upload)
python barttorvik_fetcher.py --dry-run

# With local output file
python barttorvik_fetcher.py --dry-run --output test_output.json

# Full run with S3 upload
python barttorvik_fetcher.py
```

## Cron Setup

Run twice daily at 6 AM and 6 PM:

```bash
crontab -e
```

Add this line:
```
0 6,18 * * * cd /home/pi/raspberry-pi-scripts && /home/pi/raspberry-pi-scripts/venv/bin/python barttorvik_fetcher.py >> /home/pi/logs/barttorvik.log 2>&1
```

Create the logs directory:
```bash
mkdir -p /home/pi/logs
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--year YEAR` | Season year (default: 2026) |
| `--dry-run` | Fetch and parse only, skip S3 upload |
| `--headless` | Run browser in headless mode (not recommended) |
| `--output FILE` | Save JSON to local file |
| `--bucket NAME` | S3 bucket name (default: cbb-data-files) |

## Output Format

The script uploads JSON to: `s3://cbb-data-files/cache/barttorvik_teamsheets_2026.json`

```json
{
  "fetched_at": "2026-01-21T12:00:00+00:00",
  "year": 2026,
  "team_count": 364,
  "source": "raspberry-pi-fetcher",
  "teams": [
    {
      "rank": 1,
      "team": "Auburn",
      "seed": 1,
      "resume": {
        "net": 1,
        "kpi": 1,
        "sor": 2,
        "wab": 1,
        "avg": 1.25
      },
      "quality": {
        "bpi": 1,
        "kenpom": 1,
        "trk": 1,
        "avg": 1.0
      },
      "quadrants": {
        "q1a": {"record": "5-1", "wins": 5, "losses": 1},
        "q1": {"record": "8-2", "wins": 8, "losses": 2},
        ...
      }
    },
    ...
  ]
}
```

## Troubleshooting

### Cloudflare still blocking?
- Try without `--headless` flag (default)
- Increase wait times in the script
- Check if your ISP is blocking the site

### Browser won't start on Pi?
- Make sure system dependencies are installed (see Setup step 2)
- Try running with `DISPLAY=:0` if you have a desktop environment

### S3 upload failing?
- Verify AWS credentials are correct
- Check bucket permissions allow PutObject
- Ensure the bucket exists
