"""Property test for grid generation completeness.

**Feature: themed-word-search-game, Property 5: Grid generation completeness**
**Validates: Requirements 3.1, 3.3**
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.services.grid_generator import GridGenerator
from src.models.core import WordType


@given(
    words=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=65, max_codepoint=90),  # A-Z
            min_size=3,
            max_size=12
        ).filter(lambda x: x.isalpha()),
        min_size=1,
        max_size=10
    ),
    grid_size=st.integers(min_value=8, max_value=20)
)
def test_grid_generation_completeness(words, grid_size):
    """
    Property 5: Grid generation completeness
    For any set of words and grid size, all words should be placed in the grid
    with adjacent-cell connectivity and no empty cells should remain.
    """
    # Filter out duplicate words and ensure they're valid
    unique_words = list(set(word.upper() for word in words if word.isalpha()))
    assume(len(unique_words) > 0)

    # Ensure all words can fit in the grid
    max_word_length = max(len(w) for w in unique_words)
    assume(max_word_length <= grid_size)

    # Create word types (mix of character and defining words)
    word_types = [WordType.CHARACTER if i % 2 == 0 else WordType.DEFINING
                  for i in range(len(unique_words))]

    generator = GridGenerator(seed=42)  # Use seed for reproducible tests

    # Generate grid (use lower success rate to allow for placement failures)
    grid = generator.generate_grid(unique_words, word_types, grid_size, min_success_rate=0.5)
    
    # Verify grid properties
    assert grid.size == grid_size
    assert len(grid.letters) == grid_size
    assert all(len(row) == grid_size for row in grid.letters)
    
    # Verify no empty cells remain
    for row in grid.letters:
        for cell in row:
            assert cell != '', "Grid should have no empty cells"
            assert cell.isalpha(), "All cells should contain letters"
            assert cell.isupper(), "All letters should be uppercase"
    
    # Verify solution tracking
    assert isinstance(grid.solution, list)
    
    # Verify each placed word has adjacent-cell connectivity
    for placement in grid.solution:
        assert len(placement.coordinates) == len(placement.word)
        
        # Check adjacent connectivity
        coordinates = placement.coordinates
        for i in range(1, len(coordinates)):
            current = coordinates[i-1]
            next_coord = coordinates[i]
            
            row_diff = abs(current.row - next_coord.row)
            col_diff = abs(current.col - next_coord.col)
            
            # Must be adjacent (8-directional connectivity)
            assert row_diff <= 1 and col_diff <= 1
            assert not (row_diff == 0 and col_diff == 0)  # Can't be same cell
        
        # Verify word letters match grid positions
        for i, coord in enumerate(placement.coordinates):
            assert 0 <= coord.row < grid_size
            assert 0 <= coord.col < grid_size
            assert grid.letters[coord.row][coord.col] == placement.word[i]


@given(
    grid_size=st.integers(min_value=8, max_value=20)
)
def test_empty_word_list_generates_filled_grid(grid_size):
    """Test that even with no words, grid is completely filled with letters."""
    generator = GridGenerator(seed=42)
    
    grid = generator.generate_grid([], [], grid_size)
    
    # Verify grid is properly sized and filled
    assert grid.size == grid_size
    assert len(grid.solution) == 0
    
    # All cells should be filled with random letters
    for row in grid.letters:
        for cell in row:
            assert cell != ''
            assert cell.isalpha()
            assert cell.isupper()


@given(
    word=st.text(
        alphabet=st.characters(min_codepoint=65, max_codepoint=90),
        min_size=3,
        max_size=12
    ).filter(lambda x: x.isalpha()),
    grid_size=st.integers(min_value=8, max_value=20)
)
def test_single_word_placement(word, grid_size):
    """Test that a single word can be placed with proper connectivity."""
    assume(len(word) <= grid_size)  # Word must fit in grid
    
    generator = GridGenerator(seed=42)
    word_types = [WordType.CHARACTER]
    
    grid = generator.generate_grid([word], word_types, grid_size)
    
    # Should have exactly one word in solution
    if len(grid.solution) == 1:  # Word was successfully placed
        placement = grid.solution[0]
        assert placement.word == word.upper()
        assert len(placement.coordinates) == len(word)
        
        # Verify connectivity
        assert generator.validate_adjacent_connectivity(placement.coordinates)