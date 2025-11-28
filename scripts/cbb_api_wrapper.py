"""
College Basketball Data API Wrapper

A comprehensive Python wrapper for the College Basketball Data API.
Provides easy access to all available endpoints with proper error handling.
"""

import requests
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import time
from config import Config


class CollegeBasketballAPI:
    """Main API wrapper class for College Basketball Data API."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Config] = None):
        """
        Initialize the API wrapper.
        
        Args:
            api_key: API key for authentication
            config: Config object with API settings
        """
        self.config = config or Config(api_key)
        self.session = requests.Session()
        self.session.headers.update(self.config.get_headers())
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests (increased to avoid rate limits)
        
        # API call tracking
        self.api_call_count = 0
        self.api_calls_log = []  # List of (endpoint, timestamp, duration) tuples
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, retry_count: int = 0) -> Dict[str, Any]:
        """
        Make a request to the API with proper error handling and rate limiting.
        Includes retry logic with exponential backoff for rate limit errors.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            retry_count: Internal counter for retries (max 3 retries)
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.RequestException: For HTTP errors
            ValueError: For invalid responses
        """
        import time
        start_time = time.time()
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        url = f"{self.config.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            self.last_request_time = time.time()
            
            # Track API call
            duration = time.time() - start_time
            self.api_call_count += 1
            self.api_calls_log.append({
                'endpoint': endpoint,
                'params': params,
                'timestamp': time.time(),
                'duration': duration,
                'status_code': response.status_code
            })
            
            # Handle different status codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise requests.RequestException("Unauthorized: Invalid API key")
            elif response.status_code == 403:
                raise requests.RequestException("Forbidden: API key doesn't have permission")
            elif response.status_code == 404:
                raise requests.RequestException(f"Not Found: Endpoint {endpoint} not found")
            elif response.status_code == 429:
                # Rate limited - retry with exponential backoff
                if retry_count < 3:
                    wait_time = (2 ** retry_count) * 2  # 2s, 4s, 8s
                    print(f"Rate limited on {endpoint}. Retrying in {wait_time}s (attempt {retry_count + 1}/3)...")
                    time.sleep(wait_time)
                    return self._make_request(endpoint, params, retry_count + 1)
                else:
                    raise requests.RequestException("Rate Limited: Too many requests (max retries exceeded)")
            else:
                response.raise_for_status()
                
        except requests.exceptions.Timeout:
            self.api_call_count += 1
            self.api_calls_log.append({
                'endpoint': endpoint,
                'params': params,
                'timestamp': time.time(),
                'duration': time.time() - start_time,
                'status_code': None,
                'error': 'timeout'
            })
            raise requests.RequestException("Request timed out")
        except requests.exceptions.ConnectionError:
            self.api_call_count += 1
            self.api_calls_log.append({
                'endpoint': endpoint,
                'params': params,
                'timestamp': time.time(),
                'duration': time.time() - start_time,
                'status_code': None,
                'error': 'connection'
            })
            raise requests.RequestException("Connection error")
        except json.JSONDecodeError:
            self.api_call_count += 1
            self.api_calls_log.append({
                'endpoint': endpoint,
                'params': params,
                'timestamp': time.time(),
                'duration': time.time() - start_time,
                'status_code': None,
                'error': 'json_decode'
            })
            raise ValueError("Invalid JSON response")
    
    def get_api_call_summary(self) -> Dict:
        """Get summary of API calls made."""
        if not self.api_calls_log:
            return {'total_calls': 0, 'total_time': 0}
        
        total_time = sum(call['duration'] for call in self.api_calls_log)
        
        # Group by endpoint
        endpoint_counts = {}
        for call in self.api_calls_log:
            endpoint = call['endpoint']
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
        
        return {
            'total_calls': self.api_call_count,
            'total_time': total_time,
            'average_time': total_time / len(self.api_calls_log) if self.api_calls_log else 0,
            'endpoint_counts': endpoint_counts,
            'calls': self.api_calls_log
        }
    
    def print_api_call_summary(self):
        """Print a summary of all API calls made."""
        summary = self.get_api_call_summary()
        
        print("\n" + "=" * 60)
        print("API CALL SUMMARY")
        print("=" * 60)
        print(f"Total API Calls: {summary['total_calls']}")
        print(f"Total Time: {summary['total_time']:.2f}s")
        print(f"Average Time: {summary['average_time']:.2f}s")
        print("\nCalls by Endpoint:")
        for endpoint, count in sorted(summary['endpoint_counts'].items()):
            print(f"  {endpoint}: {count}")
        
        print("\nDetailed Log:")
        for i, call in enumerate(self.api_calls_log, 1):
            params_str = f" (params: {call['params']})" if call['params'] else ""
            status = call.get('status_code', call.get('error', 'unknown'))
            print(f"  {i}. {call['endpoint']}{params_str} - {call['duration']:.3f}s - {status}")
        print("=" * 60 + "\n")
    
    def test_connection(self) -> bool:
        """
        Test the API connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try a simple endpoint to test connection
            self._make_request("teams")
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    # Teams endpoints
    def get_teams(self, year: Optional[int] = None) -> List[Dict]:
        """Get all teams."""
        params = {"year": year} if year else None
        return self._make_request("teams", params)
    
    def get_team_by_id(self, team_id: int) -> Dict:
        """Get team by ID using query parameter."""
        teams = self._make_request("teams", {"id": team_id})
        if teams and len(teams) > 0:
            return teams[0]
        else:
            raise ValueError(f"Team with ID {team_id} not found")
    
    def get_team_roster(self, season: int, team: Optional[str] = None) -> List[Dict]:
        """Get team roster with player details."""
        params = {"season": season}
        if team:
            params["team"] = team
        return self._make_request("teams/roster", params)
    
    # Games endpoints
    def get_games(self, year: int, month: Optional[int] = None, day: Optional[int] = None) -> List[Dict]:
        """Get games for a specific date or year."""
        params = {"year": year}
        if month:
            params["month"] = month
        if day:
            params["day"] = day
        
        return self._make_request("games", params)
    
    def get_game_by_id(self, game_id: int) -> Dict:
        """Get game by ID using query parameter."""
        games = self._make_request("games", {"id": game_id})
        if games and len(games) > 0:
            return games[0]
        else:
            raise ValueError(f"Game with ID {game_id} not found")
    
    # Player statistics endpoints
    def get_player_season_stats(self, season: int, team: Optional[str] = None, season_type: Optional[str] = None) -> List[Dict]:
        """Get player season statistics."""
        params = {"season": season}
        if team:
            params["team"] = team
        if season_type:
            params["seasonType"] = season_type
        return self._make_request("stats/player/season", params)
    
    def get_player_game_stats(self, season: int, team: Optional[str] = None) -> List[Dict]:
        """Get player game statistics."""
        params = {"season": season}
        if team:
            params["team"] = team
        return self._make_request("stats/player/game", params)
    
    # Team statistics endpoints
    def get_team_season_stats(self, season: int, team: Optional[str] = None, season_type: Optional[str] = None) -> List[Dict]:
        """Get team season statistics."""
        params = {"season": season}
        if team:
            params["team"] = team
        if season_type:
            params["seasonType"] = season_type
        return self._make_request("stats/team/season", params)
    
    def get_team_game_stats(self, season: int, team: Optional[str] = None) -> List[Dict]:
        """Get team game statistics."""
        params = {"season": season}
        if team:
            params["team"] = team
        return self._make_request("stats/team/game", params)
    
    # Per-game player statistics
    def get_player_game_stats_by_date(self, start_date: str, end_date: str, team: Optional[str] = None) -> List[Dict]:
        """Get per-game player statistics for a date range."""
        params = {
            "startDateRange": start_date,
            "endDateRange": end_date
        }
        if team:
            params["team"] = team
        return self._make_request("games/players", params)
    
    # Team game statistics
    def get_team_game_stats(self, season: int, start_date: Optional[str] = None, end_date: Optional[str] = None, team: Optional[str] = None, season_type: Optional[str] = None) -> List[Dict]:
        """Get team game statistics."""
        params = {"season": season}
        if start_date:
            params["startDateRange"] = start_date
        if end_date:
            params["endDateRange"] = end_date
        if team:
            params["team"] = team
        if season_type:
            params["seasonType"] = season_type
        return self._make_request("games/teams", params)
    
    # Recruiting endpoints
    def get_recruiting_players(self, team: Optional[str] = None, year: Optional[int] = None) -> List[Dict]:
        """Get recruiting players."""
        params = {}
        if team:
            params["team"] = team
        if year:
            params["year"] = year
        return self._make_request("recruiting/players", params)
    
    # Conferences endpoints
    def get_conferences(self) -> List[Dict]:
        """Get all conferences."""
        return self._make_request("conferences")
    
    def get_conference_by_id(self, conference_id: int) -> Dict:
        """Get conference by ID using query parameter."""
        conferences = self._make_request("conferences", {"id": conference_id})
        if conferences and len(conferences) > 0:
            return conferences[0]
        else:
            raise ValueError(f"Conference with ID {conference_id} not found")
    
    # Rankings endpoints
    def get_rankings(self, year: int, week: Optional[int] = None) -> List[Dict]:
        """Get rankings."""
        params = {"year": year}
        if week:
            params["week"] = week
        
        return self._make_request("rankings", params)
    
    # Tournament endpoints - may not be available
    def get_tournament_games(self, year: int) -> List[Dict]:
        """Get tournament games for a year - may not be available."""
        try:
            return self._make_request("tournament/games", {"year": year})
        except Exception as e:
            raise NotImplementedError(f"Tournament games endpoint not available: {e}")
    
    def get_tournament_bracket(self, year: int) -> Dict:
        """Get tournament bracket for a year - may not be available."""
        try:
            return self._make_request("tournament/bracket", {"year": year})
        except Exception as e:
            raise NotImplementedError(f"Tournament bracket endpoint not available: {e}")


class APITester:
    """Class to systematically test all API endpoints."""
    
    def __init__(self, api: CollegeBasketballAPI):
        """Initialize with API instance."""
        self.api = api
        self.test_results = {}
    
    def test_all_endpoints(self) -> Dict[str, Any]:
        """
        Test all available endpoints systematically.
        
        Returns:
            Dictionary with test results for each endpoint
        """
        print("Starting comprehensive API endpoint testing...")
        print("=" * 50)
        
        # Test connection first
        if not self.api.test_connection():
            print("❌ Connection test failed. Check your API key and network connection.")
            return {"connection": False}
        
        print("✅ Connection test passed")
        
        # Define test cases - only for endpoints that actually exist
        test_cases = [
            # Teams
            ("teams", lambda: self.api.get_teams()),
            ("teams_with_year", lambda: self.api.get_teams(2024)),
            
            # Games
            ("games_2024", lambda: self.api.get_games(2024)),
            ("games_2024_march", lambda: self.api.get_games(2024, 3)),
            
            # Player Statistics
            ("player_season_stats_2024", lambda: self.api.get_player_season_stats(2024)),
            ("player_season_stats_ucla", lambda: self.api.get_player_season_stats(2024, "ucla")),
            
            # Team Statistics
            ("team_season_stats_2024", lambda: self.api.get_team_season_stats(2024)),
            ("team_season_stats_ucla", lambda: self.api.get_team_season_stats(2024, "ucla")),
            
            # Conferences
            ("conferences", lambda: self.api.get_conferences()),
            
            # Rankings
            ("rankings_2024", lambda: self.api.get_rankings(2024)),
        ]
        
        # Run tests
        for test_name, test_func in test_cases:
            try:
                print(f"Testing {test_name}...", end=" ")
                result = test_func()
                
                if isinstance(result, (list, dict)) and result:
                    print("✅ PASSED")
                    self.test_results[test_name] = {
                        "status": "success",
                        "data_type": type(result).__name__,
                        "count": len(result) if isinstance(result, list) else 1
                    }
                else:
                    print("⚠️  EMPTY RESPONSE")
                    self.test_results[test_name] = {
                        "status": "empty",
                        "data_type": type(result).__name__,
                        "count": 0
                    }
                    
            except Exception as e:
                print(f"❌ FAILED: {str(e)}")
                self.test_results[test_name] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        # Test specific ID endpoints if we have data
        self._test_id_endpoints()
        
        print("\n" + "=" * 50)
        print("Testing Summary:")
        self._print_summary()
        
        return self.test_results
    
    def _test_id_endpoints(self):
        """Test endpoints that require specific IDs."""
        try:
            # Get a team ID from teams endpoint
            teams = self.api.get_teams()
            if teams and len(teams) > 0:
                team_id = teams[0].get('id')
                if team_id:
                    print(f"Testing team by ID ({team_id})...", end=" ")
                    try:
                        team = self.api.get_team_by_id(team_id)
                        print("✅ PASSED")
                        self.test_results[f"team_by_id_{team_id}"] = {
                            "status": "success",
                            "data_type": type(team).__name__
                        }
                    except Exception as e:
                        print(f"❌ FAILED: {str(e)}")
                        self.test_results[f"team_by_id_{team_id}"] = {
                            "status": "failed",
                            "error": str(e)
                        }
        except Exception as e:
            print(f"Could not test ID endpoints: {e}")
    
    def _print_summary(self):
        """Print test summary."""
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results.values() if r["status"] == "success")
        failed = sum(1 for r in self.test_results.values() if r["status"] == "failed")
        empty = sum(1 for r in self.test_results.values() if r["status"] == "empty")
        
        print(f"Total tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Empty responses: {empty}")
        
        if failed > 0:
            print("\nFailed tests:")
            for test_name, result in self.test_results.items():
                if result["status"] == "failed":
                    print(f"  - {test_name}: {result['error']}")


def main():
    """Main function to run API testing."""
    import sys
    
    try:
        # Check for API key as command line argument
        api_key = None
        if len(sys.argv) > 1:
            api_key = sys.argv[1]
            print(f"Using API key from command line: {api_key[:8]}...")
        
        # Initialize API
        api = CollegeBasketballAPI(api_key=api_key)
        
        # Run comprehensive testing
        tester = APITester(api)
        results = tester.test_all_endpoints()
        
        # Save results to file
        with open('api_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nTest results saved to api_test_results.json")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have set your API key in the CBB_API_KEY environment variable")
        print("Or pass it as a command line argument: python3 cbb_api_wrapper.py YOUR_API_KEY")


if __name__ == "__main__":
    main()
