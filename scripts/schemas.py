"""
Pydantic models for validating generated JSON data.

These schemas validate the structure of team data JSON files before writing,
catching structural issues early and providing clear error messages.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Any, Literal


# =============================================================================
# NESTED STRUCTURES
# =============================================================================

class ShootingStats(BaseModel):
    """Field goal, 3-point, or free throw statistics."""
    made: int = Field(ge=0)
    attempted: int = Field(ge=0)
    percentage: float = Field(ge=0, le=100)


class ShootingStatsNoPercentage(BaseModel):
    """Shooting stats without percentage (used in game logs)."""
    made: int = Field(ge=0)
    attempted: int = Field(ge=0)


class Rebounds(BaseModel):
    """Rebound breakdown."""
    offensive: int = Field(ge=0)
    defensive: int = Field(ge=0)
    total: int = Field(ge=0)


class ReboundsGameLog(BaseModel):
    """Rebound breakdown for game logs (no total)."""
    offensive: int = Field(ge=0)
    defensive: int = Field(ge=0)


class Record(BaseModel):
    """Win-loss record."""
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    games: int = Field(ge=0)


# =============================================================================
# PLAYER MODELS
# =============================================================================

class PlayerSeasonTotals(BaseModel):
    """Player's aggregated season statistics."""
    games: int = Field(ge=0)
    gamesStarted: int = Field(ge=0)
    minutes: int = Field(ge=0)
    mpg: float = Field(ge=0)
    points: int = Field(ge=0)
    ppg: float = Field(ge=0)
    rebounds: Rebounds
    rpg: float = Field(ge=0)
    assists: int = Field(ge=0)
    apg: float = Field(ge=0)
    turnovers: int = Field(ge=0)
    steals: int = Field(ge=0)
    spg: float = Field(ge=0)
    blocks: int = Field(ge=0)
    bpg: float = Field(ge=0)
    fouls: int = Field(ge=0)
    foulOuts: int = Field(ge=0)
    ejections: int = Field(ge=0)
    fieldGoals: ShootingStats
    threePointFieldGoals: ShootingStats
    freeThrows: ShootingStats
    assistToTurnoverRatio: float = Field(ge=0)


class PlayerGameLog(BaseModel):
    """Single game statistics for a player."""
    date: str
    opponent: str
    isHome: bool
    conferenceGame: bool
    starter: bool
    minutes: int = Field(ge=0)
    points: int = Field(ge=0)
    rebounds: ReboundsGameLog
    assists: int = Field(ge=0)
    turnovers: int = Field(ge=0)
    steals: int = Field(ge=0)
    blocks: int = Field(ge=0)
    fouls: int = Field(ge=0)
    ejected: bool
    fieldGoals: ShootingStatsNoPercentage
    threePointFieldGoals: ShootingStatsNoPercentage
    freeThrows: ShootingStatsNoPercentage


# Valid class years - N/A is NOT valid (indicates missing FoxSports mapping)
VALID_CLASS_YEARS = {'FR', 'SO', 'JR', 'SR', 'GS'}


class Player(BaseModel):
    """Individual player data."""
    model_config = ConfigDict(extra='allow', populate_by_name=True)

    name: str
    jerseyNumber: str
    position: str
    height: str
    class_: str = Field(alias='class')
    isFreshman: bool

    @field_validator('class_')
    @classmethod
    def validate_class_year(cls, v: str) -> str:
        """Validate class year is a known value. N/A is NOT valid."""
        if v == 'N/A':
            raise ValueError(
                "Class year 'N/A' is not valid. This indicates a FoxSports team ID mapping issue. "
                "Check that the CBB API team ID is correctly mapped to a FoxSports team ID in "
                "foxsports_rosters/cbb_to_foxsports_team_mapping.json"
            )
        if v not in VALID_CLASS_YEARS:
            raise ValueError(f"Invalid class year '{v}'. Must be one of: {VALID_CLASS_YEARS}")
        return v
    hometown: str
    highSchool: str
    seasonTotals: PlayerSeasonTotals
    gameByGame: List[PlayerGameLog]
    # Optional fields (validated if present via extra='allow')
    conferenceRankings: Optional[dict] = None
    previousSeasons: Optional[List[Any]] = None
    shootingStats: Optional[dict] = None
    seasonStatsWithRankings: Optional[dict] = None
    # Advanced stats that may be present
    offensiveRating: Optional[float] = None
    defensiveRating: Optional[float] = None
    netRating: Optional[float] = None
    PORPAG: Optional[float] = None
    usage: Optional[float] = None
    assistsTurnoverRatio: Optional[float] = None
    offensiveReboundPct: Optional[float] = None
    freeThrowRate: Optional[float] = None
    effectiveFieldGoalPct: Optional[float] = None
    trueShootingPct: Optional[float] = None
    winShares: Optional[dict] = None
    twoPointFieldGoals: Optional[dict] = None


# =============================================================================
# METADATA
# =============================================================================

class APRankings(BaseModel):
    """AP poll ranking data."""
    current: Optional[int] = None
    highest: Optional[int] = None


class Metadata(BaseModel):
    """Generation metadata."""
    model_config = ConfigDict(extra='allow')

    totalPlayers: int = Field(ge=0)
    apiCalls: int = Field(ge=0)
    apRankings: Optional[APRankings] = None


# =============================================================================
# EXTERNAL DATA MODELS (Optional)
# =============================================================================

class NetRating(BaseModel):
    """NET rating data from bballnet."""
    model_config = ConfigDict(extra='allow')

    rating: Optional[int] = None
    previousRating: Optional[int] = None
    source: str = "bballnet.com"
    url: str


class CoachSeason(BaseModel):
    """Single season in coach history."""
    model_config = ConfigDict(extra='allow')

    season: str
    conference: str
    overallWL: str
    conferenceWL: str
    ncaaTournament: str
    seed: str
    coach: str


class CoachHistory(BaseModel):
    """Historical coaching data."""
    model_config = ConfigDict(extra='allow')

    seasons: List[CoachSeason]
    averageOverallWins: Optional[float] = None
    averageConferenceWins: Optional[float] = None
    winningestCoach: Optional[dict] = None
    winningestCoachUrl: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None


class UpcomingGame(BaseModel):
    """Upcoming game on schedule."""
    quadrant: str
    location: str
    rank: Optional[int] = None
    opponent: str
    date: str


class QuadrantRecord(BaseModel):
    """Record against a specific quadrant."""
    record: str
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    opponents: List[str] = []


class QuadrantRecords(BaseModel):
    """All quadrant records."""
    model_config = ConfigDict(extra='allow')

    quad1: Optional[QuadrantRecord] = None
    quad2: Optional[QuadrantRecord] = None
    quad3: Optional[QuadrantRecord] = None
    quad4: Optional[QuadrantRecord] = None


# =============================================================================
# MAIN MODEL
# =============================================================================

class TeamData(BaseModel):
    """
    Main schema for team scouting data JSON files.

    Required fields are strictly validated.
    Optional fields (external data sources) are validated if present.
    Unknown fields are allowed via extra='allow' for forward compatibility.
    """
    model_config = ConfigDict(extra='allow')

    # Required fields
    team: str
    season: str
    seasonType: str
    dataGenerated: str
    players: List[Player]
    metadata: Metadata

    # Optional team stats
    teamGameStats: Optional[List[dict]] = None
    teamSeasonStats: Optional[dict] = None
    conferenceRankings: Optional[dict] = None
    d1Rankings: Optional[dict] = None

    # Optional records
    totalRecord: Optional[Record] = None
    conferenceRecord: Optional[Record] = None
    homeRecord: Optional[Record] = None
    awayRecord: Optional[Record] = None
    neutralRecord: Optional[Record] = None

    # Optional external data
    netRating: Optional[NetRating] = None
    coachHistory: Optional[CoachHistory] = None
    kenpom: Optional[dict] = None
    barttorvik: Optional[dict] = None
    wikipedia: Optional[dict] = None
    mascot: Optional[str] = None
    quadrantRecords: Optional[QuadrantRecords] = None
    upcomingGames: Optional[List[UpcomingGame]] = None


# =============================================================================
# VALIDATION FUNCTION
# =============================================================================

def validate_team_data(data: dict) -> TeamData:
    """
    Validate team data dictionary against schema.

    Args:
        data: Dictionary of team data (typically before JSON serialization)

    Returns:
        TeamData: Validated Pydantic model

    Raises:
        pydantic.ValidationError: If validation fails with detailed error messages
    """
    return TeamData(**data)


class DataQualityWarning:
    """Represents a data quality issue that isn't a hard failure."""
    def __init__(self, field: str, message: str, severity: str = "warning"):
        self.field = field
        self.message = message
        self.severity = severity  # "warning" or "error"

    def __str__(self):
        return f"[{self.severity.upper()}] {self.field}: {self.message}"


def check_data_quality(data: dict, strict: bool = False) -> List[DataQualityWarning]:
    """
    Check data quality beyond structural validation.

    This catches issues like:
    - All players having N/A class (FoxSports mapping issue)
    - Missing external data sources
    - Suspiciously low player counts

    Args:
        data: Team data dictionary
        strict: If True, raise exception on errors; if False, return warnings

    Returns:
        List of DataQualityWarning objects

    Raises:
        ValueError: If strict=True and errors are found
    """
    warnings = []
    players = data.get('players', [])
    team_name = data.get('team', 'Unknown')

    # Check 1: Player count validation
    # (N/A class checking is now done in Check 5 with specific player names)

    # Check 2: Suspiciously low player count
    if len(players) < 5:
        warnings.append(DataQualityWarning(
            field="players",
            message=f"Only {len(players)} players found. Expected 10-17 for a full roster.",
            severity="warning" if len(players) > 0 else "error"
        ))

    # Check 3: Missing key external data (for D1 teams)
    if not data.get('netRating'):
        warnings.append(DataQualityWarning(
            field="netRating",
            message="NET rating data missing.",
            severity="warning"
        ))

    if not data.get('coachHistory'):
        warnings.append(DataQualityWarning(
            field="coachHistory",
            message="Coach history data missing.",
            severity="warning"
        ))

    # Check 4: isFreshman consistency with class
    for player in players:
        player_class = player.get('class', 'N/A')
        is_freshman = player.get('isFreshman', False)

        if player_class == 'FR' and not is_freshman:
            warnings.append(DataQualityWarning(
                field="isFreshman",
                message=f"{player.get('name')}: class='FR' but isFreshman=False",
                severity="warning"
            ))
        elif player_class not in ('FR', 'N/A') and is_freshman:
            warnings.append(DataQualityWarning(
                field="isFreshman",
                message=f"{player.get('name')}: class='{player_class}' but isFreshman=True",
                severity="warning"
            ))

    # Check 5: N/A class values (should be caught by schema, but check for pre-validation data)
    na_players = [p.get('name') for p in players if p.get('class') == 'N/A']
    if na_players:
        warnings.append(DataQualityWarning(
            field="class",
            message=f"{len(na_players)} players have 'N/A' class: {', '.join(na_players[:3])}{'...' if len(na_players) > 3 else ''}. "
                    "This indicates a FoxSports team ID mapping issue.",
            severity="error"
        ))

    # If strict mode, raise on errors
    if strict:
        errors = [w for w in warnings if w.severity == "error"]
        if errors:
            error_msgs = "\n".join(f"  - {w}" for w in errors)
            raise ValueError(f"Data quality errors for {team_name}:\n{error_msgs}")

    return warnings
