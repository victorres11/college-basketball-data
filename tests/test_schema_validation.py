"""Schema validation for existing data files"""
import json
import pytest
from pathlib import Path
from tests.utils.validators import validate_data_structure

def test_validate_existing_data_files(project_root):
    """
    Validate all existing JSON files in data/2026/ match expected structure

    This ensures existing generated files maintain consistent structure
    """
    data_dir = project_root / 'data' / '2026'

    if not data_dir.exists():
        pytest.skip("data/2026/ directory not found")

    json_files = list(data_dir.glob('*_scouting_data_2026.json'))

    if not json_files:
        pytest.skip("No data files found in data/2026/")

    failures = []

    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)

            validate_data_structure(data)
            print(f"✅ {json_file.name}")

        except Exception as e:
            failures.append((json_file.name, str(e)))
            print(f"❌ {json_file.name}: {e}")

    if failures:
        error_msg = "\n".join(f"  - {name}: {err}" for name, err in failures)
        pytest.fail(f"Schema validation failures:\n{error_msg}")
