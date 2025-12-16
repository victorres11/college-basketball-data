#!/usr/bin/env python3
"""
Centralized team lookup library for College Basketball Data.

Provides a single API for looking up team information and service-specific
slugs/identifiers from any team name variation.

Usage:
    from scripts.team_lookup import TeamLookup, get_team_lookup

    # Get singleton instance
    lookup = get_team_lookup()

    # Look up service slug from any team name
    bballnet_slug = lookup.lookup("Western Kentucky", "bballnet")  # → "western-kentucky"
    wiki_page = lookup.lookup("UCLA", "wikipedia_page")  # → "UCLA Bruins men's basketball"

    # Get team ID from name
    team_id = lookup.get_team_id("Arizona State")  # → 221

    # Get full team info
    team_info = lookup.get_team(221)
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any

# Default registry path
DEFAULT_REGISTRY_PATH = Path(__file__).parent.parent / 'config' / 'team_registry.json'

# Singleton instance
_lookup_instance = None


class TeamLookup:
    """
    Centralized team lookup service.

    Loads the team registry and provides O(1) lookups from any team name
    variation to team ID, and from team ID to any service-specific slug.
    """

    def __init__(self, registry_path: str = None):
        """
        Initialize the lookup service.

        Args:
            registry_path: Path to team_registry.json. If not provided,
                          uses the default location in config/.
        """
        self.registry_path = Path(registry_path) if registry_path else DEFAULT_REGISTRY_PATH
        self.registry = self._load_registry()
        self.teams = self.registry.get('teams', {})
        self.alias_index = self.registry.get('alias_index', {})

    def _load_registry(self) -> Dict:
        """Load the team registry from JSON file"""
        if not self.registry_path.exists():
            print(f"[TeamLookup] Warning: Registry not found at {self.registry_path}")
            return {"teams": {}, "alias_index": {}}

        with open(self.registry_path, 'r') as f:
            registry = json.load(f)

        print(f"[TeamLookup] Loaded {len(registry.get('teams', {}))} teams, "
              f"{len(registry.get('alias_index', {}))} aliases")
        return registry

    def get_team_id(self, name: str) -> Optional[int]:
        """
        Get team ID from any name variation.

        Args:
            name: Team name in any format (e.g., "UCLA", "Western Kentucky",
                  "Western Ky.", "arizona state", etc.)

        Returns:
            CBB API team ID (int), or None if not found
        """
        if not name:
            return None

        # Normalize for lookup
        normalized = name.lower().strip()

        # Try direct alias lookup
        team_id = self.alias_index.get(normalized)
        if team_id is not None:
            return team_id

        # Try without periods
        normalized_no_dots = normalized.replace('.', '')
        team_id = self.alias_index.get(normalized_no_dots)
        if team_id is not None:
            return team_id

        # Try with common substitutions
        # "state" ↔ "st"
        if "state" in normalized:
            alt = normalized.replace("state", "st")
            team_id = self.alias_index.get(alt)
            if team_id is not None:
                return team_id
        elif " st" in normalized or normalized.endswith(" st"):
            alt = normalized.replace(" st", " state")
            team_id = self.alias_index.get(alt)
            if team_id is not None:
                return team_id

        # Log warning for missing team
        print(f"[TeamLookup] Warning: Team not found: '{name}'")
        return None

    def get_team(self, team_id: int) -> Optional[Dict[str, Any]]:
        """
        Get full team information by ID.

        Args:
            team_id: CBB API team ID

        Returns:
            Team dict with canonical_name, display_name, mascot, aliases,
            and services dict. None if not found.
        """
        return self.teams.get(str(team_id))

    def get_service_slug(self, team_id: int, service: str) -> Optional[str]:
        """
        Get service-specific slug for a team.

        Args:
            team_id: CBB API team ID
            service: Service name (bballnet, sports_reference, wikipedia_page,
                    barttorvik, kenpom)

        Returns:
            Service-specific slug/identifier, or None if not found
        """
        team = self.get_team(team_id)
        if team:
            return team.get('services', {}).get(service)
        return None

    def lookup(self, name: str, service: str) -> Optional[str]:
        """
        One-liner: Look up service slug from team name.

        This is the primary method for most use cases.

        Args:
            name: Team name in any format
            service: Service name (bballnet, sports_reference, wikipedia_page,
                    barttorvik, kenpom)

        Returns:
            Service-specific slug/identifier, or None if not found

        Examples:
            lookup.lookup("Western Kentucky", "bballnet")  # → "western-kentucky"
            lookup.lookup("Arizona St.", "sports_reference")  # → "arizona-state"
            lookup.lookup("UCLA", "wikipedia_page")  # → "UCLA Bruins men's basketball"
        """
        team_id = self.get_team_id(name)
        if team_id is not None:
            return self.get_service_slug(team_id, service)
        return None

    def get_canonical_name(self, name: str) -> Optional[str]:
        """
        Get canonical team name from any variation.

        Args:
            name: Team name in any format

        Returns:
            Canonical team name (e.g., "UCLA", "Western Kentucky")
        """
        team_id = self.get_team_id(name)
        if team_id is not None:
            team = self.get_team(team_id)
            if team:
                return team.get('canonical_name')
        return None

    def get_display_name(self, name: str) -> Optional[str]:
        """
        Get full display name with mascot from any variation.

        Args:
            name: Team name in any format

        Returns:
            Full display name (e.g., "UCLA Bruins", "Western Kentucky Hilltoppers")
        """
        team_id = self.get_team_id(name)
        if team_id is not None:
            team = self.get_team(team_id)
            if team:
                return team.get('display_name')
        return None

    def team_exists(self, name: str) -> bool:
        """
        Check if a team exists in the registry.

        Args:
            name: Team name in any format

        Returns:
            True if team is found, False otherwise
        """
        return self.get_team_id(name) is not None

    def list_teams(self) -> list:
        """
        List all teams in the registry.

        Returns:
            List of (team_id, canonical_name) tuples
        """
        return [(int(tid), t['canonical_name']) for tid, t in self.teams.items()]

    def list_missing_service(self, service: str) -> list:
        """
        List teams missing a particular service mapping.

        Args:
            service: Service name

        Returns:
            List of (team_id, canonical_name) tuples for teams missing the mapping
        """
        missing = []
        for tid, team in self.teams.items():
            if not team.get('services', {}).get(service):
                missing.append((int(tid), team['canonical_name']))
        return missing


def get_team_lookup(registry_path: str = None) -> TeamLookup:
    """
    Get singleton TeamLookup instance.

    This is the recommended way to get a TeamLookup - it ensures only
    one instance is loaded per process.

    Args:
        registry_path: Optional path to registry file.
                      Only used on first call.

    Returns:
        TeamLookup singleton instance
    """
    global _lookup_instance
    if _lookup_instance is None:
        _lookup_instance = TeamLookup(registry_path)
    return _lookup_instance


# For convenience, expose commonly used functions at module level
def lookup(name: str, service: str) -> Optional[str]:
    """
    Convenience function: Look up service slug from team name.

    See TeamLookup.lookup() for details.
    """
    return get_team_lookup().lookup(name, service)


def get_team_id(name: str) -> Optional[int]:
    """
    Convenience function: Get team ID from name.

    See TeamLookup.get_team_id() for details.
    """
    return get_team_lookup().get_team_id(name)


if __name__ == '__main__':
    # Test the lookup
    print("Testing TeamLookup...")

    lookup_service = get_team_lookup()

    # Test cases
    test_cases = [
        ("UCLA", "bballnet"),
        ("Western Kentucky", "bballnet"),
        ("Arizona State", "bballnet"),
        ("Arizona St.", "sports_reference"),
        ("western ky", "bballnet"),
        ("oregon", "wikipedia_page"),
    ]

    for name, service in test_cases:
        result = lookup_service.lookup(name, service)
        team_id = lookup_service.get_team_id(name)
        print(f"  {name} ({service}): {result} [ID: {team_id}]")
