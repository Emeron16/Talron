"""Property test for solution tracking accuracy.

**Feature: themed-word-search-game, Property 7: Solution tracking accuracy**
**Validates: Requirements 3.5**
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.services.grid_generator import GridGenerator
from src.models.core import WordType, Coordinate


@given(
    words=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=65, max_codepoint=90),  # A-Z
            min_size=3,
            max_size=10
        ).filter(lambda x: x.isalpha()),
        min_size=1,
        max_size=8
    ),
    grid_size=st.integers(min_value=8, max_value=20)
)
def test_solution_tracking_accuracy(words, grid_size):
    """
    Property 7: Solution tracking accuracy
    For any generated grid, the solution key should contain accurate
    coordinate paths for all placed words.
    """
    # Filter out duplicate words and ensure they're valid
    unique_words = list(set(word.upper() for word in words if word.isalpha()))
    assume(len(unique_words) > 0)

    # Ensure all words can fit in the grid
    max_word_length = max(len(w) for w in unique_words)
    assume(max_word_length <= grid_size)

    # Create word types
    word_types = [WordType.CHARACTER if i % 2 == 0 else WordType.DEFINING
                  for i in range(len(unique_words))]

    generator = GridGenerator(seed=42)  # Use seed for reproducible tests

    # Generate grid (use lower success rate to allow for placement failures)
    grid = generator.generate_grid(unique_words, word_types, grid_size, min_success_rate=0.5)
    
    # Verify solution tracking accuracy
    for placement in grid.solution:
        # Verify word is in the original word list
        assert placement.word in [w.upper() for w in unique_words], (
            f"Solution contains word '{placement.word}' not in original list"
        )
        
        # Verify coordinate path length matches word length
        assert len(placement.coordinates) == len(placement.word), (
            f"Word '{placement.word}' has {len(placement.word)} letters "
            f"but {len(placement.coordinates)} coordinates"
        )
        
        # Verify each coordinate is within grid bounds
        for coord in placement.coordinates:
            assert 0 <= coord.row < grid_size, (
                f"Row {coord.row} is out of bounds for grid size {grid_size}"
            )
            assert 0 <= coord.col < grid_size, (
                f"Column {coord.col} is out of bounds for grid size {grid_size}"
            )
        
        # Verify coordinates form a valid path (adjacent connectivity)
        for i in range(1, len(placement.coordinates)):
            current = placement.coordinates[i-1]
            next_coord = placement.coordinates[i]
            
            row_diff = abs(current.row - next_coord.row)
            col_diff = abs(current.col - next_coord.col)
            
            assert row_diff <= 1 and col_diff <= 1, (
                f"Non-adjacent coordinates in word '{placement.word}': "
                f"({current.row}, {current.col}) to ({next_coord.row}, {next_coord.col})"
            )
            assert not (row_diff == 0 and col_diff == 0), (
                f"Duplicate coordinates in word '{placement.word}': "
                f"({current.row}, {current.col})"
            )
        
        # Verify grid letters match word letters at solution coordinates
        for i, coord in enumerate(placement.coordinates):
            grid_letter = grid.letters[coord.row][coord.col]
            word_letter = placement.word[i]
            assert grid_letter == word_letter, (
                f"Grid letter '{grid_letter}' at ({coord.row}, {coord.col}) "
                f"doesn't match word letter '{word_letter}' at position {i} "
                f"in word '{placement.word}'"
            )
        
        # Verify word type is valid
        assert placement.word_type in [WordType.CHARACTER, WordType.DEFINING], (
            f"Invalid word type '{placement.word_type}' for word '{placement.word}'"
        )


@given(
    grid_size=st.integers(min_value=8, max_value=15)
)
def test_solution_completeness_with_known_words(grid_size):
    """Test solution tracking with a known set of words."""
    words = ["CAT", "DOG", "BIRD", "FISH"]
    word_types = [WordType.CHARACTER] * len(words)
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, grid_size)
    
    # Verify solution contains only words from our input
    solution_words = {placement.word for placement in grid.solution}
    input_words = {word.upper() for word in words}
    
    assert solution_words.issubset(input_words), (
        f"Solution contains unexpected words: {solution_words - input_words}"
    )
    
    # Verify each solution entry is accurate
    for placement in grid.solution:
        # Reconstruct word from grid using solution coordinates
        reconstructed_word = ""
        for coord in placement.coordinates:
            reconstructed_word += grid.letters[coord.row][coord.col]
        
        assert reconstructed_word == placement.word, (
            f"Solution tracking error: expected '{placement.word}' "
            f"but grid coordinates spell '{reconstructed_word}'"
        )


@given(
    word=st.text(
        alphabet=st.characters(min_codepoint=65, max_codepoint=90),
        min_size=3,
        max_size=8
    ).filter(lambda x: x.isalpha()),
    grid_size=st.integers(min_value=10, max_value=20)
)
def test_single_word_solution_accuracy(word, grid_size):
    """Test solution tracking accuracy for a single word placement."""
    assume(len(word) <= grid_size)  # Word must fit in grid
    
    word = word.upper()
    word_types = [WordType.DEFINING]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid([word], word_types, grid_size)
    
    if len(grid.solution) == 1:  # Word was successfully placed
        placement = grid.solution[0]
        
        # Verify solution accuracy
        assert placement.word == word
        assert placement.word_type == WordType.DEFINING
        assert len(placement.coordinates) == len(word)
        
        # Verify path reconstruction
        reconstructed = ""
        for coord in placement.coordinates:
            assert 0 <= coord.row < grid_size
            assert 0 <= coord.col < grid_size
            reconstructed += grid.letters[coord.row][coord.col]
        
        assert reconstructed == word, (
            f"Solution path reconstruction failed: "
            f"expected '{word}' but got '{reconstructed}'"
        )
        
        # Verify no coordinate duplicates
        coord_set = set((c.row, c.col) for c in placement.coordinates)
        assert len(coord_set) == len(placement.coordinates), (
            "Solution contains duplicate coordinates"
        )


def test_empty_solution_for_no_words():
    """Test that empty word list results in empty solution."""
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid([], [], 10)
    
    assert len(grid.solution) == 0, "Empty word list should result in empty solution"
    assert grid.discovered_words == set(), "Discovered words should be empty initially"