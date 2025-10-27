# College Basketball Data API Wrapper

A comprehensive Python wrapper for the [College Basketball Data API](http://api.collegebasketballdata.com/).

## Features

- 🔐 Secure API key management
- 🧪 Comprehensive endpoint testing
- ⚡ Built-in rate limiting
- 🛡️ Robust error handling
- 📊 Detailed test reporting

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Your API Key

Run the setup script to configure your API key:

```bash
python setup.py
```

Or set it manually:

```bash
export CBB_API_KEY='your_api_key_here'
```

### 3. Test the API

Run comprehensive endpoint testing:

```bash
python cbb_api_wrapper.py
```

## Usage

### Basic Usage

```python
from cbb_api_wrapper import CollegeBasketballAPI

# Initialize the API
api = CollegeBasketballAPI()

# Get all teams
teams = api.get_teams()

# Get games for 2024
games = api.get_games(2024)

# Get players
players = api.get_players(year=2024)
```

### Available Endpoints

The wrapper provides access to all API endpoints:

- **Teams**: `get_teams()`, `get_team_by_id()`
- **Games**: `get_games()`, `get_game_by_id()`
- **Players**: `get_players()`, `get_player_by_id()`, `get_player_stats()`
- **Statistics**: `get_team_stats()`
- **Conferences**: `get_conferences()`, `get_conference_by_id()`
- **Rankings**: `get_rankings()`
- **Tournament**: `get_tournament_games()`, `get_tournament_bracket()`

### Testing

The wrapper includes a comprehensive testing suite:

```python
from cbb_api_wrapper import APITester

api = CollegeBasketballAPI()
tester = APITester(api)
results = tester.test_all_endpoints()
```

## Configuration

The wrapper uses a `Config` class for API settings:

```python
from config import Config

config = Config(api_key="your_api_key")
api = CollegeBasketballAPI(config=config)
```

## Error Handling

The wrapper includes comprehensive error handling for:

- Invalid API keys
- Rate limiting
- Network timeouts
- Invalid responses
- Missing endpoints

## Files

- `cbb_api_wrapper.py` - Main API wrapper class
- `config.py` - Configuration management
- `setup.py` - Interactive setup script
- `requirements.txt` - Python dependencies
- `api_test_results.json` - Test results (generated after testing)

## API Documentation

For detailed API documentation, visit: [http://api.collegebasketballdata.com/](http://api.collegebasketballdata.com/)
