"""Property test for selection validation and state management.

**Feature: themed-word-search-game, Property 8: Selection validation and state management**
**Validates: Requirements 4.2, 4.3, 4.4**
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.services.grid_generator import GridGenerator
from src.services.selection_validator import SelectionValidator
from src.models.core import WordType, Coordinate


@given(
    words=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=65, max_codepoint=90),  # A-Z
            min_size=3,
            max_size=8
        ).filter(lambda x: x.isalpha()),
        min_size=1,
        max_size=6
    ),
    grid_size=st.integers(min_value=8, max_value=15)
)
def test_selection_validation_and_state_management(words, grid_size):
    """
    Property 8: Selection validation and state management
    For any player word selection, valid words should be marked as discovered 
    and update game state, while invalid selections should be cleared without 
    affecting game state.
    """
    # Filter out duplicate words and ensure they're valid
    unique_words = list(set(word.upper() for word in words if word.isalpha()))
    assume(len(unique_words) > 0)
    
    # Create word types
    word_types = [WordType.CHARACTER if i % 2 == 0 else WordType.DEFINING 
                  for i in range(len(unique_words))]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(unique_words, word_types, grid_size)
    validator = SelectionValidator(grid)
    
    # Test valid word selections
    for placement in grid.solution:
        # Get initial state
        initial_discovered = validator.get_discovered_words().copy()
        initial_count = len(initial_discovered)
        
        # Validate the word using its solution coordinates
        is_valid, found_word = validator.validate_selection(placement.coordinates)
        
        # Valid word should be recognized
        assert is_valid, f"Valid word '{placement.word}' was not recognized as valid"
        assert found_word == placement.word, (
            f"Expected word '{placement.word}' but got '{found_word}'"
        )
        
        # Mark word as discovered
        was_newly_discovered = validator.mark_word_discovered(placement.word)
        
        # State should be updated for newly discovered words
        if placement.word not in initial_discovered:
            assert was_newly_discovered, (
                f"Word '{placement.word}' should be newly discovered"
            )
            assert validator.is_word_discovered(placement.word), (
                f"Word '{placement.word}' should be marked as discovered"
            )
            assert len(validator.get_discovered_words()) == initial_count + 1, (
                "Discovered word count should increase by 1"
            )
        else:
            assert not was_newly_discovered, (
                f"Word '{placement.word}' should not be newly discovered (already found)"
            )
            assert len(validator.get_discovered_words()) == initial_count, (
                "Discovered word count should not change for already discovered words"
            )


@given(
    grid_size=st.integers(min_value=8, max_value=15)
)
def test_invalid_selection_handling(grid_size):
    """Test that invalid selections don't affect game state."""
    words = ["CAT", "DOG", "BIRD"]
    word_types = [WordType.CHARACTER] * len(words)
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, grid_size)
    validator = SelectionValidator(grid)
    
    # Get initial state
    initial_discovered = validator.get_discovered_words().copy()
    initial_stats = validator.get_progress_stats()
    
    # Create coordinates that are out of bounds
    out_of_bounds_coords = [
        Coordinate(grid_size, 0),  # Row out of bounds
        Coordinate(0, grid_size)   # Column out of bounds
    ]
    
    # Test invalid selection (out of bounds)
    is_valid, found_word = validator.validate_selection(out_of_bounds_coords)
    
    # Invalid selection should be rejected
    assert not is_valid, "Out of bounds coordinates should not be valid"
    assert found_word is None, "Invalid selection should not return a word"
    
    # Game state should remain unchanged
    assert validator.get_discovered_words() == initial_discovered, (
        "Invalid selection should not change discovered words"
    )
    assert validator.get_progress_stats() == initial_stats, (
        "Invalid selection should not change progress stats"
    )


@given(
    grid_size=st.integers(min_value=8, max_value=12)
)
def test_disconnected_path_rejection(grid_size):
    """Test that disconnected coordinate paths are rejected."""
    words = ["HELLO", "WORLD"]
    word_types = [WordType.CHARACTER, WordType.DEFINING]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, grid_size)
    validator = SelectionValidator(grid)
    
    # Create disconnected coordinates (jump from one corner to another)
    disconnected_coords = [
        Coordinate(0, 0),
        Coordinate(grid_size-1, grid_size-1)  # Far corner
    ]
    
    # Get initial state
    initial_discovered = validator.get_discovered_words().copy()
    
    # Test disconnected path
    is_valid, found_word = validator.validate_selection(disconnected_coords)
    
    # Should be rejected due to disconnected path
    assert not is_valid, "Disconnected path should be invalid"
    assert found_word is None, "Disconnected path should not return a word"
    
    # State should remain unchanged
    assert validator.get_discovered_words() == initial_discovered, (
        "Disconnected path should not change game state"
    )


@given(
    words=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=65, max_codepoint=90),
            min_size=3,
            max_size=6
        ).filter(lambda x: x.isalpha()),
        min_size=2,
        max_size=5
    ),
    grid_size=st.integers(min_value=10, max_value=15)
)
def test_progress_tracking_accuracy(words, grid_size):
    """Test that progress tracking accurately reflects discovered words."""
    unique_words = list(set(word.upper() for word in words if word.isalpha()))
    assume(len(unique_words) >= 2)
    
    word_types = [WordType.CHARACTER] * len(unique_words)
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(unique_words, word_types, grid_size)
    validator = SelectionValidator(grid)
    
    # Initially no words should be discovered
    discovered, total, percentage = validator.get_progress_stats()
    assert discovered == 0, "Initially no words should be discovered"
    assert total == len(grid.solution), "Total should match solution count"
    assert percentage == 0.0, "Initial percentage should be 0"
    assert not validator.is_game_complete(), "Game should not be complete initially"
    
    # Discover words one by one and verify progress
    discovered_count = 0
    for placement in grid.solution:
        # Validate and mark word as discovered
        is_valid, found_word = validator.validate_selection(placement.coordinates)
        if is_valid:
            was_newly_discovered = validator.mark_word_discovered(found_word)
            if was_newly_discovered:
                discovered_count += 1
                
                # Check progress stats
                current_discovered, current_total, current_percentage = validator.get_progress_stats()
                assert current_discovered == discovered_count, (
                    f"Progress should show {discovered_count} discovered words"
                )
                assert current_total == len(grid.solution), (
                    "Total count should remain constant"
                )
                expected_percentage = (discovered_count / len(grid.solution)) * 100
                assert abs(current_percentage - expected_percentage) < 0.01, (
                    f"Percentage should be {expected_percentage}, got {current_percentage}"
                )
    
    # Check if game is complete
    if discovered_count == len(grid.solution):
        assert validator.is_game_complete(), "Game should be complete when all words found"
    else:
        assert not validator.is_game_complete(), "Game should not be complete with missing words"


@given(
    grid_size=st.integers(min_value=8, max_value=12)
)
def test_duplicate_discovery_handling(grid_size):
    """Test that discovering the same word multiple times doesn't affect state."""
    words = ["TEST", "WORD"]
    word_types = [WordType.CHARACTER, WordType.DEFINING]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, grid_size)
    validator = SelectionValidator(grid)
    
    if len(grid.solution) > 0:
        placement = grid.solution[0]
        
        # First discovery
        is_valid1, found_word1 = validator.validate_selection(placement.coordinates)
        assume(is_valid1)  # Skip if word wasn't placed successfully
        
        was_newly_discovered1 = validator.mark_word_discovered(found_word1)
        assert was_newly_discovered1, "First discovery should be new"
        
        stats_after_first = validator.get_progress_stats()
        
        # Second discovery of same word
        is_valid2, found_word2 = validator.validate_selection(placement.coordinates)
        assert is_valid2, "Word should still be valid on second selection"
        assert found_word2 == found_word1, "Should find same word"
        
        was_newly_discovered2 = validator.mark_word_discovered(found_word2)
        assert not was_newly_discovered2, "Second discovery should not be new"
        
        stats_after_second = validator.get_progress_stats()
        
        # Stats should remain unchanged
        assert stats_after_first == stats_after_second, (
            "Progress stats should not change for duplicate discoveries"
        )


def test_empty_selection_handling():
    """Test handling of empty coordinate selections."""
    words = ["TEST"]
    word_types = [WordType.CHARACTER]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, 10)
    validator = SelectionValidator(grid)
    
    # Test empty selection
    is_valid, found_word = validator.validate_selection([])
    
    assert not is_valid, "Empty selection should be invalid"
    assert found_word is None, "Empty selection should not return a word"


def test_single_coordinate_selection():
    """Test handling of single coordinate selections."""
    words = ["A"]  # Single letter word
    word_types = [WordType.CHARACTER]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, 10)
    validator = SelectionValidator(grid)
    
    # Single coordinate should be valid path connectivity
    single_coord = [Coordinate(0, 0)]
    is_valid, found_word = validator.validate_selection(single_coord)
    
    # Should be valid path (single coordinate is trivially connected)
    # But may not be a valid word depending on grid generation
    if is_valid:
        assert found_word is not None, "Valid selection should return a word"
    else:
        assert found_word is None, "Invalid selection should not return a word"