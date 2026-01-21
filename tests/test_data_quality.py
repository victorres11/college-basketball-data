#!/usr/bin/env python3
"""
Unit tests for the data quality monitoring framework.

Tests:
- Severity levels and ValidationResult
- QualityReport aggregation
- DataQualityHub operations
- Roster validators (FoxSports match, class coverage, roster size)
"""

import sys
import os
import pytest

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from data_quality import (
    Severity,
    ValidationResult,
    QualityReport,
    DataQualityHub,
    normalize_name,
)
from validators.roster_validators import (
    validate_foxsports_roster_match,
    validate_class_year_coverage,
    validate_roster_size,
)


class TestSeverity:
    """Test Severity enum."""

    def test_severity_ordering(self):
        """Verify severity levels are properly ordered."""
        assert Severity.INFO < Severity.WARNING
        assert Severity.WARNING < Severity.ERROR
        assert Severity.ERROR < Severity.CRITICAL

    def test_severity_values(self):
        """Verify severity numeric values."""
        assert Severity.INFO == 0
        assert Severity.WARNING == 1
        assert Severity.ERROR == 2
        assert Severity.CRITICAL == 3


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_creation(self):
        """Test creating a validation result."""
        result = ValidationResult(
            validator_name="Test Validator",
            severity=Severity.WARNING,
            message="Test message",
            details={'key': 'value'},
            remediation="Fix it"
        )
        assert result.validator_name == "Test Validator"
        assert result.severity == Severity.WARNING
        assert result.message == "Test message"
        assert result.details == {'key': 'value'}
        assert result.remediation == "Fix it"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ValidationResult(
            validator_name="Test",
            severity=Severity.ERROR,
            message="Error message"
        )
        d = result.to_dict()
        assert d['validator'] == "Test"
        assert d['severity'] == "ERROR"
        assert d['message'] == "Error message"


class TestQualityReport:
    """Test QualityReport aggregation."""

    def test_empty_report(self):
        """Test empty report properties."""
        report = QualityReport(team_name="Test", season=2026)
        assert report.max_severity == Severity.INFO
        assert not report.has_critical
        assert not report.has_errors
        assert report.pass_rate == 100.0

    def test_add_results(self):
        """Test adding results updates counts."""
        report = QualityReport(team_name="Test", season=2026)

        report.add(ValidationResult("V1", Severity.INFO, "ok"))
        assert report.checks_run == 1
        assert report.checks_passed == 1

        report.add(ValidationResult("V2", Severity.ERROR, "bad"))
        assert report.checks_run == 2
        assert report.checks_passed == 1  # ERROR doesn't pass

    def test_max_severity(self):
        """Test max severity calculation."""
        report = QualityReport(team_name="Test", season=2026)
        report.add(ValidationResult("V1", Severity.INFO, "ok"))
        report.add(ValidationResult("V2", Severity.WARNING, "warn"))
        report.add(ValidationResult("V3", Severity.ERROR, "error"))

        assert report.max_severity == Severity.ERROR
        assert report.has_errors
        assert not report.has_critical

    def test_has_critical(self):
        """Test CRITICAL detection."""
        report = QualityReport(team_name="Test", season=2026)
        report.add(ValidationResult("V1", Severity.CRITICAL, "critical issue"))

        assert report.has_critical
        assert report.has_errors  # CRITICAL implies errors

    def test_pass_rate(self):
        """Test pass rate calculation."""
        report = QualityReport(team_name="Test", season=2026)

        # 2 passing (INFO, WARNING), 1 failing (ERROR)
        report.add(ValidationResult("V1", Severity.INFO, "ok"))
        report.add(ValidationResult("V2", Severity.WARNING, "warn"))
        report.add(ValidationResult("V3", Severity.ERROR, "error"))

        # INFO and WARNING count as passed
        assert report.checks_passed == 2
        assert report.checks_run == 3
        assert abs(report.pass_rate - 66.67) < 1  # ~66.67%


class TestDataQualityHub:
    """Test DataQualityHub orchestrator."""

    def test_collect_data(self):
        """Test collecting data for validators."""
        hub = DataQualityHub("Test Team", 2026)
        hub.collect('key1', 'value1')
        hub.collect('key2', [1, 2, 3])

        assert hub.data['key1'] == 'value1'
        assert hub.data['key2'] == [1, 2, 3]
        assert hub.data['team_name'] == "Test Team"

    def test_check_adds_to_report(self):
        """Test check() adds results to report."""
        hub = DataQualityHub("Test", 2026)
        result = ValidationResult("Test", Severity.WARNING, "test")
        hub.check(result)

        assert len(hub.report.results) == 1
        assert hub.report.results[0] == result

    def test_run_validators(self):
        """Test running registered validators."""
        hub = DataQualityHub("Test", 2026)
        hub.collect('test_value', 42)

        def test_validator(data):
            return [ValidationResult(
                "TestValidator",
                Severity.INFO,
                f"Value is {data.get('test_value')}"
            )]

        hub.register_validator(test_validator)
        hub.run_validators()

        assert len(hub.report.results) == 1
        assert "42" in hub.report.results[0].message

    def test_finalize(self):
        """Test finalizing the report."""
        hub = DataQualityHub("Test", 2026)
        hub.check(ValidationResult("V1", Severity.INFO, "ok"))

        report = hub.finalize()
        assert report.completed_at is not None
        assert report.checks_run == 1


class TestNormalizeName:
    """Test player name normalization."""

    def test_basic_normalization(self):
        """Test basic lowercase and trim."""
        assert normalize_name("John Smith") == "john smith"
        assert normalize_name("  John Smith  ") == "john smith"

    def test_suffix_removal(self):
        """Test Jr/Sr/III removal."""
        assert normalize_name("John Smith Jr.") == "john smith"
        assert normalize_name("John Smith Jr") == "john smith"
        assert normalize_name("John Smith Sr.") == "john smith"
        assert normalize_name("John Smith III") == "john smith"
        assert normalize_name("John Smith IV") == "john smith"

    def test_punctuation_removal(self):
        """Test punctuation handling."""
        assert normalize_name("D'Angelo Russell") == "dangelo russell"
        assert normalize_name("O'Brien") == "obrien"

    def test_empty_handling(self):
        """Test empty/None handling."""
        assert normalize_name("") == ""
        assert normalize_name(None) == ""


class TestValidateFoxsportsRosterMatch:
    """Test FoxSports roster cross-validation."""

    def test_critical_when_low_match(self):
        """CRITICAL severity when <50% match (likely wrong team)."""
        data = {
            'api_roster_players': [
                {'name': 'Player A'},
                {'name': 'Player B'},
                {'name': 'Player C'},
                {'name': 'Player D'},
            ],
            'foxsports_players': [
                {'name': 'Wrong Player X'},
                {'name': 'Wrong Player Y'},
            ],
            'team_name': 'Test Team',
            'foxsports_id': '123',
        }

        results = validate_foxsports_roster_match(data)

        # Should have CRITICAL result
        critical = [r for r in results if r.severity == Severity.CRITICAL]
        assert len(critical) == 1
        assert "wrong team" in critical[0].message.lower()

    def test_error_when_moderate_match(self):
        """ERROR severity when 50-70% match."""
        data = {
            'api_roster_players': [
                {'name': 'Player A'},
                {'name': 'Player B'},
                {'name': 'Player C'},
                {'name': 'Player D'},
                {'name': 'Player E'},
            ],
            'foxsports_players': [
                {'name': 'Player A'},
                {'name': 'Player B'},
                {'name': 'Player C'},
                # 3/5 = 60% match
            ],
            'foxsports_id': '123',
        }

        results = validate_foxsports_roster_match(data)

        # Should have ERROR result
        errors = [r for r in results if r.severity == Severity.ERROR]
        assert len(errors) == 1

    def test_info_when_high_match(self):
        """INFO severity when >90% match (healthy)."""
        data = {
            'api_roster_players': [
                {'name': 'Nick Martinelli'},
                {'name': 'Brooks Barnhizer'},
                {'name': 'Jayden Reid'},
            ],
            'foxsports_players': [
                {'name': 'Nick Martinelli'},
                {'name': 'Brooks Barnhizer'},
                {'name': 'Jayden Reid'},
            ],
            'foxsports_id': '90',
        }

        results = validate_foxsports_roster_match(data)

        # Should all be INFO
        assert all(r.severity <= Severity.INFO for r in results)

    def test_warning_when_no_foxsports_data(self):
        """WARNING when FoxSports data not available."""
        data = {
            'api_roster_players': [{'name': 'Player A'}],
            'foxsports_players': [],
            'foxsports_id': '123',
        }

        results = validate_foxsports_roster_match(data)
        assert any(r.severity == Severity.WARNING for r in results)

    def test_warning_when_on_demand_fetch(self):
        """WARNING when roster was fetched on-demand."""
        data = {
            'api_roster_players': [{'name': 'Player A'}],
            'foxsports_players': [{'name': 'Player A'}],
            'foxsports_id': '123',
            'foxsports_source': 'fetched',
        }

        results = validate_foxsports_roster_match(data)

        # Should have warning about on-demand fetch
        fetch_warnings = [r for r in results if 'on-demand' in r.message.lower()]
        assert len(fetch_warnings) == 1


class TestValidateClassYearCoverage:
    """Test class year coverage validation."""

    def test_error_when_low_coverage(self):
        """ERROR when <50% have class year."""
        data = {
            'players': [
                {'name': 'P1', 'class': 'SR'},
                {'name': 'P2', 'class': 'N/A'},
                {'name': 'P3', 'class': ''},
                {'name': 'P4', 'class': 'N/A'},
            ]
        }

        results = validate_class_year_coverage(data)
        errors = [r for r in results if r.severity == Severity.ERROR]
        assert len(errors) == 1

    def test_warning_when_moderate_coverage(self):
        """WARNING when 50-80% have class year."""
        data = {
            'players': [
                {'name': 'P1', 'class': 'SR'},
                {'name': 'P2', 'class': 'JR'},
                {'name': 'P3', 'class': 'SO'},
                {'name': 'P4', 'class': 'N/A'},
                {'name': 'P5', 'class': 'N/A'},
            ]
        }  # 60% coverage

        results = validate_class_year_coverage(data)
        warnings = [r for r in results if r.severity == Severity.WARNING]
        assert len(warnings) == 1

    def test_info_when_high_coverage(self):
        """INFO when >80% have class year."""
        data = {
            'players': [
                {'name': 'P1', 'class': 'SR'},
                {'name': 'P2', 'class': 'JR'},
                {'name': 'P3', 'class': 'SO'},
                {'name': 'P4', 'class': 'FR'},
                {'name': 'P5', 'class': 'N/A'},
            ]
        }  # 80% coverage

        results = validate_class_year_coverage(data)
        assert all(r.severity <= Severity.INFO for r in results)


class TestValidateRosterSize:
    """Test roster size validation."""

    def test_error_when_very_small(self):
        """ERROR when <5 players."""
        data = {
            'players': [{'name': f'P{i}'} for i in range(3)],
            'team_name': 'Test',
        }

        results = validate_roster_size(data)
        errors = [r for r in results if r.severity == Severity.ERROR]
        assert len(errors) == 1

    def test_warning_when_small(self):
        """WARNING when 5-9 players."""
        data = {
            'players': [{'name': f'P{i}'} for i in range(7)],
            'team_name': 'Test',
        }

        results = validate_roster_size(data)
        warnings = [r for r in results if r.severity == Severity.WARNING]
        assert len(warnings) == 1

    def test_info_when_normal(self):
        """INFO when 10-20 players (normal)."""
        data = {
            'players': [{'name': f'P{i}'} for i in range(15)],
            'team_name': 'Test',
        }

        results = validate_roster_size(data)
        assert all(r.severity == Severity.INFO for r in results)

    def test_warning_when_large(self):
        """WARNING when >20 players."""
        data = {
            'players': [{'name': f'P{i}'} for i in range(25)],
            'team_name': 'Test',
        }

        results = validate_roster_size(data)
        warnings = [r for r in results if r.severity == Severity.WARNING]
        assert len(warnings) == 1


class TestNorthwesternBugRegression:
    """
    Regression tests for the Northwestern bug.

    The bug: Generator used wrong FoxSports team ID, loaded Eastern Illinois
    roster cache, and applied wrong class years to Northwestern players.

    These tests verify the validators would catch this class of bugs.
    """

    def test_detects_wrong_team_cache(self):
        """Verify CRITICAL alert when wrong team's cache is loaded."""
        # Simulate: Northwestern API roster vs Eastern Illinois FoxSports cache
        data = {
            'api_roster_players': [
                # Northwestern players
                {'name': 'Nick Martinelli'},
                {'name': 'Brooks Barnhizer'},
                {'name': 'Jayden Reid'},
                {'name': 'Ty Berry'},
                {'name': 'Ryan Langborg'},
            ],
            'foxsports_players': [
                # Eastern Illinois players (wrong team!)
                {'name': 'Nakyel Shelton'},
                {'name': 'Henry Abraham'},
                {'name': 'Zion Fruster'},
            ],
            'team_name': 'Northwestern',
            'foxsports_id': '212',  # Wrong ID - this is Eastern Illinois
        }

        results = validate_foxsports_roster_match(data)

        # Must detect CRITICAL issue
        critical = [r for r in results if r.severity == Severity.CRITICAL]
        assert len(critical) == 1, "Should detect CRITICAL issue when rosters don't match"

        # Should mention wrong team possibility
        assert "wrong team" in critical[0].message.lower()

        # Should have actionable remediation
        assert "foxsports_id" in critical[0].remediation.lower()

    def test_correct_match_passes(self):
        """Verify correct Northwestern data passes validation."""
        data = {
            'api_roster_players': [
                {'name': 'Nick Martinelli'},
                {'name': 'Brooks Barnhizer'},
                {'name': 'Jayden Reid'},
            ],
            'foxsports_players': [
                {'name': 'Nick Martinelli'},
                {'name': 'Brooks Barnhizer'},
                {'name': 'Jayden Reid'},
            ],
            'team_name': 'Northwestern',
            'foxsports_id': '90',  # Correct ID
        }

        results = validate_foxsports_roster_match(data)

        # Should NOT have CRITICAL or ERROR
        critical_or_error = [r for r in results if r.severity >= Severity.ERROR]
        assert len(critical_or_error) == 0, "Correct data should not trigger errors"
