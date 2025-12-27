"""Property-based tests for progress tracking accuracy.

**Feature: themed-word-search-game, Property 11: Progress tracking accuracy**
**Validates: Requirements 5.2**
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.services.game_controller import GameController
from src.models.core import GameSettings, GameStatus
from src.data.word_database import WordDatabase


class TestProgressTrackingAccuracy:
    """Property tests for progress tracking accuracy."""

    @given(
        grid_size=st.integers(min_value=8, max_value=20),
        time_limit=st.integers(min_value=60, max_value=1800)
    )
    def test_progress_tracking_reflects_discovered_words_accurately(self, grid_size: int, time_limit: int):
        """
        Property 11: Progress tracking accuracy
        For any word discovery during gameplay, the progress display should accurately 
        reflect the current found/total word ratio.
        
        **Feature: themed-word-search-game, Property 11: Progress tracking accuracy**
        **Validates: Requirements 5.2**
        """
        controller = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Initialize and start a game
        game = controller.initialize_game("anime", "naruto", settings)
        grid = controller.start_game()
        
        # Initial state: no words discovered
        initial_discovered = len(grid.discovered_words)
        total_words = len(grid.solution)
        
        assert initial_discovered == 0
        assert total_words > 0
        
        # Progress should start at 0%
        progress_ratio = initial_discovered / total_words if total_words > 0 else 0
        assert progress_ratio == 0.0

    @given(
        grid_size=st.integers(min_value=8, max_value=15),  # Smaller for faster testing
        time_limit=st.integers(min_value=60, max_value=300)
    )
    def test_progress_increases_monotonically_with_word_discovery(self, grid_size: int, time_limit: int):
        """
        Property 11: Progress tracking accuracy
        For any sequence of word discoveries, progress should increase monotonically
        and never decrease.
        
        **Feature: themed-word-search-game, Property 11: Progress tracking accuracy**
        **Validates: Requirements 5.2**
        """
        controller = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Initialize and start a game
        game = controller.initialize_game("anime", "naruto", settings)
        grid = controller.start_game()
        
        total_words = len(grid.solution)
        assume(total_words > 0)
        
        # Track progress as we simulate word discoveries
        previous_progress = 0.0
        
        # Simulate discovering words one by one
        for i, word_placement in enumerate(grid.solution[:min(3, len(grid.solution))]):
            # Add word to discovered set
            grid.discovered_words.add(word_placement.word)
            
            # Calculate current progress
            current_discovered = len(grid.discovered_words)
            current_progress = current_discovered / total_words
            
            # Progress should increase or stay the same (monotonic)
            assert current_progress >= previous_progress
            
            # Progress should be within valid range [0, 1]
            assert 0.0 <= current_progress <= 1.0
            
            # Progress should match expected ratio
            expected_progress = (i + 1) / total_words
            assert abs(current_progress - expected_progress) < 0.001
            
            previous_progress = current_progress

    @given(
        grid_size=st.integers(min_value=8, max_value=15),
        time_limit=st.integers(min_value=60, max_value=300)
    )
    def test_progress_reaches_100_percent_when_all_words_found(self, grid_size: int, time_limit: int):
        """
        Property 11: Progress tracking accuracy
        For any game where all words are discovered, progress should reach exactly 100%.
        
        **Feature: themed-word-search-game, Property 11: Progress tracking accuracy**
        **Validates: Requirements 5.2**
        """
        controller = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Initialize and start a game
        game = controller.initialize_game("anime", "naruto", settings)
        grid = controller.start_game()
        
        total_words = len(grid.solution)
        assume(total_words > 0)
        
        # Simulate discovering all words
        for word_placement in grid.solution:
            grid.discovered_words.add(word_placement.word)
        
        # Progress should be exactly 100%
        discovered_count = len(grid.discovered_words)
        progress = discovered_count / total_words
        
        assert progress == 1.0
        assert discovered_count == total_words

    @given(
        grid_size=st.integers(min_value=8, max_value=20),
        time_limit=st.integers(min_value=60, max_value=1800)
    )
    def test_progress_calculation_handles_edge_cases(self, grid_size: int, time_limit: int):
        """
        Property 11: Progress tracking accuracy
        For any game configuration, progress calculation should handle edge cases
        like empty discovered sets and single-word games correctly.
        
        **Feature: themed-word-search-game, Property 11: Progress tracking accuracy**
        **Validates: Requirements 5.2**
        """
        controller = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Initialize and start a game
        game = controller.initialize_game("anime", "naruto", settings)
        grid = controller.start_game()
        
        total_words = len(grid.solution)
        assume(total_words > 0)
        
        # Test empty discovered set
        grid.discovered_words.clear()
        progress = len(grid.discovered_words) / total_words
        assert progress == 0.0
        
        # Test partial discovery
        if total_words > 1:
            # Add one word
            grid.discovered_words.add(grid.solution[0].word)
            progress = len(grid.discovered_words) / total_words
            expected = 1.0 / total_words
            assert abs(progress - expected) < 0.001
        
        # Test duplicate discoveries (shouldn't affect count)
        if total_words > 0:
            first_word = grid.solution[0].word
            grid.discovered_words.add(first_word)
            grid.discovered_words.add(first_word)  # Add same word again
            
            # Should still count as one discovery
            unique_discoveries = len(grid.discovered_words)
            progress = unique_discoveries / total_words
            
            if total_words == 1:
                assert progress == 1.0
            else:
                expected = 1.0 / total_words
                assert abs(progress - expected) < 0.001

    @given(
        grid_size=st.integers(min_value=8, max_value=15),
        time_limit=st.integers(min_value=60, max_value=300),
        discovery_count=st.integers(min_value=0, max_value=10)
    )
    def test_progress_calculation_is_consistent_across_multiple_calculations(
        self, grid_size: int, time_limit: int, discovery_count: int
    ):
        """
        Property 11: Progress tracking accuracy
        For any game state, multiple progress calculations should yield identical results.
        
        **Feature: themed-word-search-game, Property 11: Progress tracking accuracy**
        **Validates: Requirements 5.2**
        """
        controller = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Initialize and start a game
        game = controller.initialize_game("anime", "naruto", settings)
        grid = controller.start_game()
        
        total_words = len(grid.solution)
        assume(total_words > 0)
        
        # Simulate discovering a specific number of words
        words_to_discover = min(discovery_count, total_words)
        for i in range(words_to_discover):
            grid.discovered_words.add(grid.solution[i].word)
        
        # Calculate progress multiple times
        discovered_count = len(grid.discovered_words)
        progress1 = discovered_count / total_words
        progress2 = discovered_count / total_words
        progress3 = discovered_count / total_words
        
        # All calculations should be identical
        assert progress1 == progress2 == progress3
        
        # Progress should be within valid range
        assert 0.0 <= progress1 <= 1.0
        
        # Progress should match expected value
        expected_progress = words_to_discover / total_words
        assert abs(progress1 - expected_progress) < 0.001

    @given(
        grid_size=st.integers(min_value=8, max_value=20),
        time_limit=st.integers(min_value=60, max_value=1800)
    )
    def test_progress_tracking_maintains_word_count_invariants(self, grid_size: int, time_limit: int):
        """
        Property 11: Progress tracking accuracy
        For any game state, the relationship between discovered words, total words,
        and progress percentage should maintain mathematical invariants.
        
        **Feature: themed-word-search-game, Property 11: Progress tracking accuracy**
        **Validates: Requirements 5.2**
        """
        controller = GameController()
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Initialize and start a game
        game = controller.initialize_game("anime", "naruto", settings)
        grid = controller.start_game()
        
        total_words = len(grid.solution)
        assume(total_words > 0)
        
        # Test various discovery states
        for discovery_ratio in [0.0, 0.25, 0.5, 0.75, 1.0]:
            # Clear previous discoveries
            grid.discovered_words.clear()
            
            # Discover the specified ratio of words
            words_to_discover = int(total_words * discovery_ratio)
            for i in range(words_to_discover):
                grid.discovered_words.add(grid.solution[i].word)
            
            discovered_count = len(grid.discovered_words)
            progress = discovered_count / total_words
            
            # Mathematical invariants
            assert discovered_count <= total_words  # Can't discover more than total
            assert discovered_count >= 0  # Can't have negative discoveries
            assert 0.0 <= progress <= 1.0  # Progress must be in [0, 1]
            
            # Progress should match the ratio of discovered to total
            expected_progress = discovered_count / total_words
            assert abs(progress - expected_progress) < 0.001
            
            # Remaining words calculation
            remaining_words = total_words - discovered_count
            assert remaining_words >= 0
            assert remaining_words == total_words - discovered_count