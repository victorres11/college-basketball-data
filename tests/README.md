# Generator Tests

Automated end-to-end tests for the College Basketball Data generator.

## Test Teams
- **Oregon** (Pac-12)
- **Western Kentucky** (C-USA)
- **Arizona State** (Big 12)

## Running Tests Locally

### Run all end-to-end tests:
```bash
pytest tests/test_generator_e2e.py -v
```

### Run for a specific team:
```bash
pytest tests/test_generator_e2e.py -v -k "Oregon"
```

### Run all tests together (convenience):
```bash
pytest tests/test_generator_e2e.py::test_all_teams_locally -v
```

### Validate existing data files:
```bash
pytest tests/test_schema_validation.py -v
```

## CI/CD

### Manual/On-Demand Run Only
- Tests run **only when manually triggered** (not automatic on pushes)
- Validates generator against 3 test teams
- Strict mode: All subprocesses must succeed

### How to Run Tests in CI
1. Go to GitHub Actions tab
2. Select "Generator E2E Tests" workflow
3. Click "Run workflow"
4. Choose team to test (or "all")

## Test Validation

Tests validate:
- ✅ All subprocesses complete successfully (STRICT mode)
- ✅ Output JSON file exists and is valid
- ✅ Required fields present (team, season, players, metadata, etc.)
- ✅ Player stats internally consistent (PPG = points/games, etc.)
- ✅ Team records sum correctly (home + away + neutral = total)
- ✅ No hard-coded values - handles changing mid-season data
- ✅ Made shots ≤ attempted shots
- ✅ Percentages in valid range (0-100)
- ✅ Game-by-game totals match season totals

## Failure Modes

Test fails if:
- ❌ Any core subprocess fails (Game Data, Roster, etc.)
- ❌ Any optional subprocess fails (Wikipedia, KenPom, etc.) - STRICT mode
- ❌ Output JSON missing required fields
- ❌ Data inconsistencies (e.g., wins+losses ≠ games)
- ❌ Invalid stat values (negative numbers, percentages > 100)

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # pytest fixtures and configuration
├── test_generator_e2e.py          # End-to-end generator tests
├── test_schema_validation.py      # JSON schema validation
├── utils/
│   ├── __init__.py
│   └── validators.py              # Reusable validation functions
└── output/                        # Test output directory (git-ignored)
```

## Requirements

Before running tests, ensure you have:
1. Python 3.11+
2. All dependencies installed: `pip install -r requirements.txt`
3. API key configured in `config/api_config.txt` or `CBB_API_KEY` environment variable

## Next Steps for CI/CD Setup

1. **Set up GitHub Secret**: Add `CBB_API_KEY` in repository settings (Settings → Secrets and variables → Actions → New repository secret)
2. **Test locally first**: Run `pytest tests/test_generator_e2e.py -v` to verify everything works
3. **Push to main**: Tests will run automatically on the next push
4. **Monitor results**: Check GitHub Actions tab for test results
5. **Optional secrets**: Add `KENPOM_USERNAME` and `KENPOM_PASSWORD` if using KenPom
