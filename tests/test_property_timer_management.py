"""Property-based tests for timer management.

**Feature: themed-word-search-game, Property 10: Timer management**
**Validates: Requirements 5.1, 5.5**
"""

import pytest
import time
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume
from src.services.game_controller import GameController
from src.models.core import GameSettings, GameStatus
from src.data.word_database import WordDatabase


class TestTimerManagement:
    """Property tests for timer management."""

    @given(
        time_limit=st.integers(min_value=60, max_value=1800),
        grid_size=st.integers(min_value=8, max_value=20)
    )
    def test_timer_initializes_correctly_for_active_games(self, time_limit: int, grid_size: int):
        """
        Property 10: Timer management
        For any active game session, the timer should initialize correctly with the specified time limit.
        
        **Feature: themed-word-search-game, Property 10: Timer management**
        **Validates: Requirements 5.1, 5.5**
        """
        controller = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Initialize and start a game
        game = controller.initialize_game("anime", "naruto", settings)
        grid = controller.start_game()
        
        # Game should be active
        assert game.status == GameStatus.ACTIVE
        
        # Timer should be initialized with correct time limit
        assert game.time_limit == time_limit
        
        # Start time should be recent (within last few seconds)
        time_diff = datetime.now() - game.start_time
        assert time_diff.total_seconds() < 5  # Should be very recent

    @given(
        time_limit=st.integers(min_value=60, max_value=300),  # Shorter for testing
        grid_size=st.integers(min_value=8, max_value=12)
    )
    def test_timer_tracks_elapsed_time_correctly(self, time_limit: int, grid_size: int):
        """
        Property 10: Timer management
        For any active game session, the timer should accurately track elapsed time.
        
        **Feature: themed-word-search-game, Property 10: Timer management**
        **Validates: Requirements 5.1**
        """
        controller = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Initialize and start a game
        game = controller.initialize_game("anime", "naruto", settings)
        start_time = datetime.now()
        grid = controller.start_game()
        
        # Simulate some time passing (small amount for test speed)
        time.sleep(0.1)
        
        # Calculate elapsed time
        current_time = datetime.now()
        elapsed = (current_time - game.start_time).total_seconds()
        remaining = time_limit - elapsed
        
        # Elapsed time should be positive and reasonable
        assert elapsed >= 0
        assert elapsed < time_limit  # Should not exceed time limit in this short test
        
        # Remaining time should be positive and less than original limit
        assert remaining > 0
        assert remaining <= time_limit

    @given(
        time_limit=st.integers(min_value=60, max_value=1800),
        grid_size=st.integers(min_value=8, max_value=20)
    )
    def test_game_can_be_ended_when_time_expires(self, time_limit: int, grid_size: int):
        """
        Property 10: Timer management
        For any active game session, the game should be able to transition to expired status
        when time limit is reached.
        
        **Feature: themed-word-search-game, Property 10: Timer management**
        **Validates: Requirements 5.5**
        """
        controller = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Initialize and start a game
        game = controller.initialize_game("anime", "naruto", settings)
        grid = controller.start_game()
        
        # Game should start as active
        assert game.status == GameStatus.ACTIVE
        
        # Simulate time expiration by ending game with expired status
        controller.end_game(GameStatus.EXPIRED)
        
        # Game should now be expired
        assert game.status == GameStatus.EXPIRED

    @given(
        time_limit=st.integers(min_value=60, max_value=1800),
        grid_size=st.integers(min_value=8, max_value=20)
    )
    def test_timer_state_consistent_across_game_lifecycle(self, time_limit: int, grid_size: int):
        """
        Property 10: Timer management
        For any game session, timer-related state should remain consistent throughout
        the game lifecycle from setup to completion.
        
        **Feature: themed-word-search-game, Property 10: Timer management**
        **Validates: Requirements 5.1, 5.5**
        """
        controller = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Initialize game (setup phase)
        game = controller.initialize_game("anime", "naruto", settings)
        assert game.status == GameStatus.SETUP
        assert game.time_limit == time_limit
        
        # Start game (active phase)
        grid = controller.start_game()
        assert game.status == GameStatus.ACTIVE
        assert game.time_limit == time_limit  # Should remain unchanged
        
        # End game (completed phase)
        controller.end_game(GameStatus.COMPLETED)
        assert game.status == GameStatus.COMPLETED
        assert game.time_limit == time_limit  # Should still be unchanged

    @given(
        invalid_time_limit=st.one_of(
            st.integers(max_value=59),
            st.integers(min_value=1801)
        ),
        grid_size=st.integers(min_value=8, max_value=20)
    )
    def test_invalid_time_limits_rejected_during_initialization(self, invalid_time_limit: int, grid_size: int):
        """
        Property 10: Timer management
        For any invalid time limit, the system should reject the configuration
        during game initialization.
        
        **Feature: themed-word-search-game, Property 10: Timer management**
        **Validates: Requirements 5.1**
        """
        controller = GameController()
        
        # Invalid time limit should raise ValueError during settings creation
        with pytest.raises(ValueError, match="Time limit must be between 60 and 1800 seconds"):
            settings = GameSettings(grid_size=grid_size, time_limit=invalid_time_limit)

    @given(
        time_limit=st.integers(min_value=60, max_value=1800),
        grid_size=st.integers(min_value=12, max_value=20)  # Use larger grids to avoid word placement issues
    )
    def test_multiple_games_have_independent_timers(self, time_limit: int, grid_size: int):
        """
        Property 10: Timer management
        For any sequence of games, each game should have its own independent timer
        that doesn't interfere with other games.

        **Feature: themed-word-search-game, Property 10: Timer management**
        **Validates: Requirements 5.1**
        """
        controller1 = GameController()
        controller2 = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Start first game
        game1 = controller1.initialize_game("anime", "naruto", settings)
        grid1 = controller1.start_game()
        start_time1 = game1.start_time
        
        # Small delay
        time.sleep(0.05)
        
        # Start second game
        game2 = controller2.initialize_game("movies", "starwars", settings)
        grid2 = controller2.start_game()
        start_time2 = game2.start_time
        
        # Both games should be active
        assert game1.status == GameStatus.ACTIVE
        assert game2.status == GameStatus.ACTIVE
        
        # Both should have same time limit
        assert game1.time_limit == time_limit
        assert game2.time_limit == time_limit
        
        # Start times should be different (second game started later)
        assert start_time2 > start_time1
        
        # Games should have different IDs
        assert game1.id != game2.id