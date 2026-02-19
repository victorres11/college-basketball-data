"""
Unit tests for the upcoming games date-based filter introduced in
fix/upcoming-games-date-filter.

The filter logic lives in web-ui/generator.py inside the quadrant-data
block. These tests exercise the same logic in isolation so they run
without any API key or external dependencies.
"""
import pytest
from datetime import datetime, date


# ---------------------------------------------------------------------------
# Helper that mirrors the filter block in generator.py exactly, but accepts
# an explicit `today` so tests are date-independent.
# ---------------------------------------------------------------------------
def filter_upcoming_games(games, today=None):
    """
    Return only games whose date is today or in the future.

    - Games with a parseable date in the past are dropped.
    - Games with an unparseable / missing date are kept (safe default).
    """
    if today is None:
        today = datetime.now().date()

    kept, dropped, unparseable = [], [], []
    for game in games:
        date_str = game.get('date', '')
        game_date = None
        if date_str:
            try:
                game_date = datetime.strptime(date_str, "%m/%d/%Y").date()
            except Exception:
                unparseable.append(game)
                game_date = None

        if game_date is None or game_date >= today:
            kept.append(game)
        else:
            dropped.append(game)

    return kept, dropped, unparseable


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------
def make_game(opponent, date_str):
    return {'opponent': opponent, 'date': date_str}


TODAY = date(2026, 2, 19)
YESTERDAY = date(2026, 2, 18)
TOMORROW = date(2026, 2, 20)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestUpcomingGamesFilter:

    def test_future_game_is_kept(self):
        games = [make_game('Duke', '03/08/2026')]
        kept, dropped, _ = filter_upcoming_games(games, today=TODAY)
        assert len(kept) == 1
        assert len(dropped) == 0

    def test_past_game_is_dropped(self):
        games = [make_game('Duke', '01/15/2026')]
        kept, dropped, _ = filter_upcoming_games(games, today=TODAY)
        assert len(kept) == 0
        assert len(dropped) == 1

    def test_todays_game_is_kept(self):
        """A game scheduled for today should not be filtered out."""
        games = [make_game('Duke', TODAY.strftime('%m/%d/%Y'))]
        kept, dropped, _ = filter_upcoming_games(games, today=TODAY)
        assert len(kept) == 1
        assert len(dropped) == 0

    def test_rematch_future_game_is_kept(self):
        """
        Core regression test: if team A already played team B earlier in the
        season, the upcoming road rematch must NOT be filtered out.

        Before this fix the filter used opponent names, which would have
        silently dropped the second game.
        """
        games = [
            make_game('Maryland', '01/21/2026'),  # already played (past)
            make_game('Maryland', '03/08/2026'),  # road rematch (future)
        ]
        kept, dropped, _ = filter_upcoming_games(games, today=TODAY)
        opponents_kept = [g['opponent'] for g in kept]
        assert 'Maryland' in opponents_kept, "Future rematch vs Maryland should be kept"
        assert len(kept) == 1
        assert len(dropped) == 1

    def test_unparseable_date_is_kept_as_safe_default(self):
        """Games with bad date strings must be included, not silently dropped."""
        games = [make_game('Kansas', 'TBD'), make_game('Kentucky', '')]
        kept, dropped, unparseable = filter_upcoming_games(games, today=TODAY)
        assert len(kept) == 2
        assert len(dropped) == 0

    def test_unparseable_date_recorded(self):
        """Filter must report which games had bad dates (for warning logging)."""
        games = [make_game('Kansas', 'TBD')]
        _, _, unparseable = filter_upcoming_games(games, today=TODAY)
        assert len(unparseable) == 1
        assert unparseable[0]['opponent'] == 'Kansas'

    def test_empty_list(self):
        kept, dropped, unparseable = filter_upcoming_games([], today=TODAY)
        assert kept == []
        assert dropped == []
        assert unparseable == []

    def test_mixed_games(self):
        games = [
            make_game('Oregon', '12/02/2025'),   # past — drop
            make_game('Oregon', '02/21/2026'),   # future rematch — keep
            make_game('Kansas', '03/15/2026'),   # future — keep
            make_game('Duke', 'unknown'),         # bad date — keep
        ]
        kept, dropped, _ = filter_upcoming_games(games, today=TODAY)
        assert len(kept) == 3
        assert len(dropped) == 1
        assert dropped[0]['date'] == '12/02/2025'
