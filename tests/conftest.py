"""pytest configuration and fixtures for generator tests"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'web-ui'))

@pytest.fixture(scope="session")
def project_root():
    """Project root directory"""
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def test_output_dir(project_root):
    """Directory for test output files"""
    output_dir = project_root / 'tests' / 'output'
    output_dir.mkdir(exist_ok=True)
    return output_dir

@pytest.fixture(scope="session")
def test_teams():
    """Teams to test (as specified by user)"""
    return ["Oregon", "Western Kentucky", "Arizona State"]

@pytest.fixture(scope="session")
def test_season():
    """Current season to test"""
    return 2026  # 2025-26 season

def pytest_configure(config):
    """Configure pytest environment"""
    # Check for API key
    if not os.getenv('CBB_API_KEY') and not os.path.exists('config/api_config.txt'):
        pytest.exit('CBB_API_KEY not set and config/api_config.txt not found')

    # Register custom markers
    config.addinivalue_line("markers", "integration: integration tests (run on-demand)")
    config.addinivalue_line("markers", "e2e: end-to-end tests")
