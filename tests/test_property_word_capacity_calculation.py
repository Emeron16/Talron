"""Property-based tests for word capacity calculation.

**Feature: themed-word-search-game, Property 4: Word capacity calculation**
**Validates: Requirements 2.3, 2.4**
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.services.game_controller import GameController
from src.models.core import GameSettings


class TestWordCapacityCalculation:
    """Property tests for word capacity calculation."""

    @given(
        grid_size=st.integers(min_value=8, max_value=20),
        word_list=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
                min_size=3,
                max_size=12
            ),
            min_size=1,
            max_size=50
        )
    )
    def test_word_capacity_does_not_exceed_grid_theoretical_maximum(self, grid_size: int, word_list: list):
        """
        Property 4: Word capacity calculation
        For any combination of grid size and word list, the maximum word count 
        should not exceed the theoretical placement capacity of the grid.
        
        **Feature: themed-word-search-game, Property 4: Word capacity calculation**
        **Validates: Requirements 2.3, 2.4**
        """
        # Filter out empty strings and ensure valid words
        valid_words = [word.strip() for word in word_list if word.strip() and 3 <= len(word.strip()) <= 12]
        assume(len(valid_words) > 0)
        
        controller = GameController()
        capacity = controller.calculate_word_capacity(grid_size, valid_words)
        
        # Capacity should never exceed the number of available words
        assert capacity <= len(valid_words)
        
        # Capacity should never exceed theoretical grid maximum
        # (conservative estimate: each word needs at least 1 cell)
        total_cells = grid_size * grid_size
        assert capacity <= total_cells
        
        # Capacity should be non-negative
        assert capacity >= 0

    @given(
        grid_size=st.integers(min_value=8, max_value=20),
        word_lengths=st.lists(
            st.integers(min_value=3, max_value=12),
            min_size=1,
            max_size=30
        )
    )
    def test_capacity_decreases_with_longer_words(self, grid_size: int, word_lengths: list):
        """
        Property 4: Word capacity calculation
        For any grid size, longer words should generally result in lower capacity
        due to placement constraints.
        
        **Feature: themed-word-search-game, Property 4: Word capacity calculation**
        **Validates: Requirements 2.3**
        """
        controller = GameController()
        
        # Create word lists with different average lengths
        short_words = ['A' * length for length in word_lengths if length <= 6]
        long_words = ['B' * length for length in word_lengths if length >= 8]
        
        if short_words and long_words:
            short_capacity = controller.calculate_word_capacity(grid_size, short_words)
            long_capacity = controller.calculate_word_capacity(grid_size, long_words)
            
            # Both capacities should be valid
            assert short_capacity >= 0
            assert long_capacity >= 0
            
            # For same number of words, shorter words should generally allow higher capacity
            if len(short_words) == len(long_words):
                # This is a general trend, not absolute due to overlap possibilities
                total_short_length = sum(len(w) for w in short_words)
                total_long_length = sum(len(w) for w in long_words)
                
                if total_long_length > total_short_length:
                    assert long_capacity <= short_capacity

    @given(
        grid_size=st.integers(min_value=8, max_value=20)
    )
    def test_empty_word_list_returns_zero_capacity(self, grid_size: int):
        """
        Property 4: Word capacity calculation
        For any grid size with an empty word list, capacity should be zero.
        
        **Feature: themed-word-search-game, Property 4: Word capacity calculation**
        **Validates: Requirements 2.3**
        """
        controller = GameController()
        capacity = controller.calculate_word_capacity(grid_size, [])
        
        assert capacity == 0

    @given(
        word_list=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
                min_size=3,
                max_size=12
            ),
            min_size=1,
            max_size=20
        )
    )
    def test_larger_grids_allow_higher_capacity(self, word_list: list):
        """
        Property 4: Word capacity calculation
        For any word list, larger grids should allow equal or higher word capacity.
        
        **Feature: themed-word-search-game, Property 4: Word capacity calculation**
        **Validates: Requirements 2.3**
        """
        # Filter out empty strings and ensure valid words
        valid_words = [word.strip() for word in word_list if word.strip() and 3 <= len(word.strip()) <= 12]
        assume(len(valid_words) > 0)
        
        controller = GameController()
        
        # Test with different grid sizes
        small_grid_capacity = controller.calculate_word_capacity(8, valid_words)
        medium_grid_capacity = controller.calculate_word_capacity(14, valid_words)
        large_grid_capacity = controller.calculate_word_capacity(20, valid_words)
        
        # Larger grids should allow equal or higher capacity
        assert small_grid_capacity <= medium_grid_capacity
        assert medium_grid_capacity <= large_grid_capacity
        
        # All capacities should be within bounds
        assert 0 <= small_grid_capacity <= len(valid_words)
        assert 0 <= medium_grid_capacity <= len(valid_words)
        assert 0 <= large_grid_capacity <= len(valid_words)

    @given(
        grid_size=st.one_of(
            st.integers(max_value=7),
            st.integers(min_value=21)
        ),
        word_list=st.lists(st.text(min_size=3, max_size=12), min_size=1)
    )
    def test_invalid_grid_size_raises_error(self, grid_size: int, word_list: list):
        """
        Property 4: Word capacity calculation
        For any invalid grid size, the system should raise a ValueError.
        
        **Feature: themed-word-search-game, Property 4: Word capacity calculation**
        **Validates: Requirements 2.4**
        """
        controller = GameController()
        
        with pytest.raises(ValueError, match="Grid size must be between 8 and 20"):
            controller.calculate_word_capacity(grid_size, word_list)

    @given(
        grid_size=st.integers(min_value=8, max_value=20),
        word_list=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
                min_size=3,
                max_size=12
            ),
            min_size=1,
            max_size=100
        )
    )
    def test_word_count_adjustment_respects_capacity(self, grid_size: int, word_list: list):
        """
        Property 4: Word capacity calculation
        For any word list and grid size, automatic word count adjustment should
        never exceed the calculated capacity.
        
        **Feature: themed-word-search-game, Property 4: Word capacity calculation**
        **Validates: Requirements 2.4**
        """
        # Filter out empty strings and ensure valid words
        valid_words = [word.strip() for word in word_list if word.strip() and 3 <= len(word.strip()) <= 12]
        assume(len(valid_words) > 0)
        
        controller = GameController()
        
        # Calculate capacity
        capacity = controller.calculate_word_capacity(grid_size, valid_words)
        
        # Adjust word count
        adjusted_words = controller.adjust_word_count_for_grid(valid_words, grid_size)
        
        # Adjusted word count should not exceed capacity
        assert len(adjusted_words) <= capacity
        
        # If original list was within capacity, it should remain unchanged
        if len(valid_words) <= capacity:
            assert len(adjusted_words) == len(valid_words)
        
        # Adjusted words should be a subset of original words
        assert all(word in valid_words for word in adjusted_words)