"""
Data Quality Validators

This package contains validator functions for the data quality framework.
Each validator takes a collected_data dict and returns a List[ValidationResult].
"""

from .roster_validators import (
    validate_foxsports_roster_match,
    validate_class_year_coverage,
    validate_roster_size,
)

__all__ = [
    'validate_foxsports_roster_match',
    'validate_class_year_coverage',
    'validate_roster_size',
]
