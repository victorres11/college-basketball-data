"""
Configuration module for College Basketball Data API wrapper.
Handles API key management and configuration settings.
"""

import os
from typing import Optional


class Config:
    """Configuration class for API settings."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            api_key: API key for authentication. If None, will try to load from environment.
        """
        self.base_url = "http://api.collegebasketballdata.com"
        self.api_key = api_key or self._load_api_key()
        
        if not self.api_key:
            raise ValueError(
                "API key not found. Please set the CBB_API_KEY environment variable "
                "or pass it directly to the Config constructor."
            )
    
    def _load_api_key(self) -> Optional[str]:
        """Load API key from environment variables or config file."""
        # First try environment variable
        api_key = os.getenv('CBB_API_KEY')
        if api_key:
            return api_key
        
        # Then try config file
        config_file = os.path.join(os.path.dirname(__file__), 'api_config.txt')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('CBB_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            # Remove any newlines or extra whitespace
                            return api_key.replace('\n', '').replace('\r', '').strip()
            except Exception:
                pass
        
        return None
    
    def get_headers(self) -> dict:
        """Get headers for API requests."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'CBB-API-Wrapper/1.0'
        }
    
    def validate_config(self) -> bool:
        """Validate that configuration is properly set up."""
        return bool(self.api_key and self.base_url)


def setup_api_key():
    """
    Interactive setup for API key.
    Prompts user to enter API key and saves it to environment.
    """
    print("College Basketball Data API Setup")
    print("=" * 40)
    
    api_key = input("Enter your API key: ").strip()
    
    if not api_key:
        print("Error: API key cannot be empty.")
        return False
    
    # Save to environment file
    env_file = os.path.expanduser("~/.cbb_api_env")
    
    try:
        with open(env_file, 'w') as f:
            f.write(f"export CBB_API_KEY='{api_key}'\n")
        
        print(f"API key saved to {env_file}")
        print("To use this API key, run: source ~/.cbb_api_env")
        print("Or add the following line to your shell profile:")
        print(f"export CBB_API_KEY='{api_key}'")
        
        return True
    except Exception as e:
        print(f"Error saving API key: {e}")
        return False


if __name__ == "__main__":
    setup_api_key()
