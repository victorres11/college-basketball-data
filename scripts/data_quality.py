#!/usr/bin/env python3
"""
Data Quality Monitoring Framework

Provides validation infrastructure for detecting data quality issues during generation.
Catches bugs like the Northwestern issue where wrong team's FoxSports cache was applied.

Usage:
    from data_quality import DataQualityHub, Severity, ValidationResult

    # In generator
    quality_hub = DataQualityHub(team_name, season, progress_callback)
    quality_hub.collect('api_roster_players', roster_data)
    quality_hub.collect('foxsports_players', foxsports_data)

    # Run validators
    quality_hub.run_validators()
    report = quality_hub.finalize()
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional


class Severity(IntEnum):
    """
    Validation severity levels with escalation behavior.

    INFO: Logged, part of summary
    WARNING: Highlighted in email (yellow)
    ERROR: Red highlight, subject tag
    CRITICAL: Urgent email formatting, requires review
    """
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    validator_name: str
    severity: Severity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    remediation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"[{self.severity.name}] {self.validator_name}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'validator': self.validator_name,
            'severity': self.severity.name,
            'message': self.message,
            'details': self.details,
            'remediation': self.remediation,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class QualityReport:
    """Aggregated quality report for entire generation."""
    team_name: str
    season: int
    checks_run: int = 0
    checks_passed: int = 0
    results: List[ValidationResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    @property
    def max_severity(self) -> Severity:
        """Get the highest severity level from all results."""
        if not self.results:
            return Severity.INFO
        return max(r.severity for r in self.results)

    @property
    def max_severity_name(self) -> str:
        """Get the name of the highest severity level."""
        return self.max_severity.name

    @property
    def has_critical(self) -> bool:
        """Check if any CRITICAL issues exist."""
        return any(r.severity == Severity.CRITICAL for r in self.results)

    @property
    def has_errors(self) -> bool:
        """Check if any ERROR or higher issues exist."""
        return any(r.severity >= Severity.ERROR for r in self.results)

    @property
    def has_warnings(self) -> bool:
        """Check if any WARNING or higher issues exist."""
        return any(r.severity >= Severity.WARNING for r in self.results)

    @property
    def issues(self) -> List[ValidationResult]:
        """Get all results with WARNING or higher severity."""
        return [r for r in self.results if r.severity >= Severity.WARNING]

    @property
    def pass_rate(self) -> float:
        """Calculate the pass rate as a percentage."""
        if self.checks_run == 0:
            return 100.0
        return (self.checks_passed / self.checks_run) * 100

    def add(self, result: ValidationResult):
        """Add a validation result to the report."""
        self.results.append(result)
        self.checks_run += 1
        if result.severity <= Severity.WARNING:
            self.checks_passed += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'team_name': self.team_name,
            'season': self.season,
            'checks_run': self.checks_run,
            'checks_passed': self.checks_passed,
            'pass_rate': round(self.pass_rate, 1),
            'max_severity': self.max_severity_name,
            'has_critical': self.has_critical,
            'has_errors': self.has_errors,
            'issues': [r.to_dict() for r in self.issues],
            'all_results': [r.to_dict() for r in self.results],
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def summary(self) -> str:
        """Get a human-readable summary."""
        status = "PASSED" if not self.has_errors else "FAILED"
        return (f"Data Quality: {status} - {self.checks_passed}/{self.checks_run} checks passed "
                f"({self.pass_rate:.0f}%) - Max severity: {self.max_severity_name}")


class DataQualityHub:
    """
    Central orchestrator for data quality checks.

    Collects data during generation, runs validators, and aggregates results.
    """

    def __init__(self, team_name: str, season: int, progress_callback: dict = None):
        """
        Initialize the quality hub.

        Args:
            team_name: Name of the team being generated
            season: Season year (e.g., 2026)
            progress_callback: Optional dict to update progress (from generator)
        """
        self.report = QualityReport(team_name=team_name, season=season)
        self.progress_callback = progress_callback
        self.validators: List[Callable] = []
        self._collected_data: Dict[str, Any] = {
            'team_name': team_name,
            'season': season
        }

    @property
    def data(self) -> Dict[str, Any]:
        """Access collected data for validators."""
        return self._collected_data

    def register_validator(self, validator_fn: Callable):
        """
        Register a validator function to be run during finalization.

        Args:
            validator_fn: Function that takes collected_data dict and returns List[ValidationResult]
        """
        self.validators.append(validator_fn)

    def collect(self, key: str, value: Any):
        """
        Collect data during generation for later validation.

        Args:
            key: Data key (e.g., 'api_roster_players', 'foxsports_players')
            value: Data value
        """
        self._collected_data[key] = value

    def check(self, result: ValidationResult):
        """
        Record a validation result.

        Args:
            result: The validation result to record
        """
        self.report.add(result)
        self._log_result(result)
        self._update_status(result)

    def run_validators(self):
        """Run all registered validators."""
        for validator in self.validators:
            try:
                results = validator(self._collected_data)
                if results:
                    for result in results:
                        self.check(result)
            except Exception as e:
                # Validator itself failed - log as ERROR
                self.check(ValidationResult(
                    validator_name=getattr(validator, '__name__', 'unknown'),
                    severity=Severity.ERROR,
                    message=f"Validator failed: {str(e)}",
                    details={'exception': str(type(e).__name__)}
                ))

    def run_immediate(self, validator_fn: Callable) -> List[ValidationResult]:
        """
        Run a validator immediately (not deferred to finalize).

        Use this for critical checks that should happen as soon as data is available.

        Args:
            validator_fn: Validator function to run

        Returns:
            List of validation results
        """
        try:
            results = validator_fn(self._collected_data)
            if results:
                for result in results:
                    self.check(result)
            return results or []
        except Exception as e:
            error_result = ValidationResult(
                validator_name=getattr(validator_fn, '__name__', 'unknown'),
                severity=Severity.ERROR,
                message=f"Validator failed: {str(e)}"
            )
            self.check(error_result)
            return [error_result]

    def finalize(self) -> QualityReport:
        """
        Finalize and return the quality report.

        Runs any remaining registered validators and marks the report complete.
        """
        self.run_validators()
        self.report.completed_at = datetime.now()
        return self.report

    def _log_result(self, result: ValidationResult):
        """Log a validation result to console."""
        severity_prefix = {
            Severity.INFO: "[INFO]",
            Severity.WARNING: "[WARN]",
            Severity.ERROR: "[ERROR]",
            Severity.CRITICAL: "[CRITICAL]"
        }
        prefix = severity_prefix.get(result.severity, "[?]")
        print(f"[DATA QUALITY] {prefix} {result.validator_name}: {result.message}")

    def _update_status(self, result: ValidationResult):
        """Update progress callback with validation status if available."""
        if self.progress_callback is None:
            return

        # Only add status entries for WARNING and above
        if result.severity >= Severity.WARNING:
            if 'dataStatus' not in self.progress_callback:
                self.progress_callback['dataStatus'] = []

            status_map = {
                Severity.WARNING: 'warning',
                Severity.ERROR: 'warning',  # Use 'warning' status, but message shows ERROR
                Severity.CRITICAL: 'warning'  # Non-blocking, so still 'warning'
            }

            self.progress_callback['dataStatus'].append({
                'name': f'Quality: {result.validator_name}',
                'status': status_map.get(result.severity, 'warning'),
                'message': f'[{result.severity.name}] {result.message}',
                'details': result.remediation or ''
            })


def normalize_name(name: str) -> str:
    """
    Normalize player name for comparison.

    - Lowercase
    - Remove Jr/Sr/III/IV suffixes
    - Remove punctuation
    - Normalize whitespace

    Args:
        name: Raw player name

    Returns:
        Normalized name for comparison
    """
    if not name:
        return ''

    # Lowercase and strip
    name = name.lower().strip()

    # Remove common suffixes (Jr., Sr., III, IV, etc.)
    name = re.sub(r'\s+(jr\.?|sr\.?|iii?|iv|v)$', '', name, flags=re.IGNORECASE)

    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)

    # Normalize whitespace
    name = ' '.join(name.split())

    return name
