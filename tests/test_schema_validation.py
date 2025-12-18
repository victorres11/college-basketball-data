"""Schema validation for existing data files"""
import json
import pytest
from pathlib import Path
from tests.utils.validators import validate_data_structure

# Import data quality checker
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from schemas import check_data_quality, DataQualityWarning


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


def test_data_quality_checks(project_root):
    """
    Check data quality for all existing JSON files.

    This catches issues like:
    - All players having N/A class (FoxSports mapping issue)
    - Missing external data sources
    - Suspiciously low player counts
    """
    data_dir = project_root / 'data' / '2026'

    if not data_dir.exists():
        pytest.skip("data/2026/ directory not found")

    json_files = list(data_dir.glob('*_scouting_data_2026.json'))

    if not json_files:
        pytest.skip("No data files found in data/2026/")

    errors = []
    warnings_summary = []

    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)

            warnings = check_data_quality(data, strict=False)

            # Collect errors (severity="error")
            file_errors = [w for w in warnings if w.severity == "error"]
            if file_errors:
                errors.append((json_file.name, file_errors))
                for w in file_errors:
                    print(f"❌ {json_file.name}: {w}")

            # Collect warnings for summary
            file_warnings = [w for w in warnings if w.severity == "warning"]
            if file_warnings:
                warnings_summary.append((json_file.name, file_warnings))
                for w in file_warnings:
                    print(f"⚠️  {json_file.name}: {w}")

            if not warnings:
                print(f"✅ {json_file.name}")

        except Exception as e:
            errors.append((json_file.name, [str(e)]))
            print(f"❌ {json_file.name}: {e}")

    # Print summary
    if warnings_summary:
        print(f"\n📋 Warnings found in {len(warnings_summary)} files")

    # Fail on errors
    if errors:
        error_msg = "\n".join(
            f"  - {name}: {', '.join(str(e) for e in errs)}"
            for name, errs in errors
        )
        pytest.fail(f"Data quality errors found:\n{error_msg}")
