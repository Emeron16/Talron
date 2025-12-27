"""Property test for word overlap consistency.

**Feature: themed-word-search-game, Property 6: Word overlap consistency**
**Validates: Requirements 3.2**
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
            max_size=8  # Smaller words to increase overlap probability
        ).filter(lambda x: x.isalpha()),
        min_size=2,
        max_size=6  # Fewer words to increase overlap probability
    ),
    grid_size=st.integers(min_value=8, max_value=12)  # Smaller grids to force overlaps
)
def test_word_overlap_consistency(words, grid_size):
    """
    Property 6: Word overlap consistency
    For any grid with overlapping words, shared letters should maintain 
    consistency across all overlapping word placements.
    """
    # Filter out duplicate words and ensure they're valid
    unique_words = list(set(word.upper() for word in words if word.isalpha()))
    assume(len(unique_words) >= 2)
    
    # Create word types
    word_types = [WordType.CHARACTER if i % 2 == 0 else WordType.DEFINING 
                  for i in range(len(unique_words))]
    
    generator = GridGenerator(seed=42)  # Use seed for reproducible tests
    
    # Generate grid
    grid = generator.generate_grid(unique_words, word_types, grid_size)
    
    # Find all overlapping positions
    position_to_words = {}  # Maps (row, col) to list of (word, letter_index)
    
    for placement in grid.solution:
        for i, coord in enumerate(placement.coordinates):
            pos = (coord.row, coord.col)
            if pos not in position_to_words:
                position_to_words[pos] = []
            position_to_words[pos].append((placement.word, i))
    
    # Check consistency at overlapping positions
    for pos, word_letter_pairs in position_to_words.items():
        if len(word_letter_pairs) > 1:  # This position has overlapping words
            row, col = pos
            grid_letter = grid.letters[row][col]
            
            # All words at this position should have the same letter
            for word, letter_index in word_letter_pairs:
                expected_letter = word[letter_index]
                assert expected_letter == grid_letter, (
                    f"Overlap inconsistency at ({row}, {col}): "
                    f"grid has '{grid_letter}' but word '{word}' expects '{expected_letter}' "
                    f"at position {letter_index}"
                )
                
                # Verify all overlapping words agree on the letter
                for other_word, other_index in word_letter_pairs:
                    other_expected = other_word[other_index]
                    assert expected_letter == other_expected, (
                        f"Word overlap inconsistency: '{word}' has '{expected_letter}' "
                        f"but '{other_word}' has '{other_expected}' at position ({row}, {col})"
                    )


@given(
    grid_size=st.integers(min_value=8, max_value=12)
)
def test_forced_overlap_scenario(grid_size):
    """Test overlap consistency with words designed to overlap."""
    # Create words that share common letters to force overlaps
    words = ["HELLO", "WORLD", "LOVE", "OVER"]  # These share O, L, E
    word_types = [WordType.CHARACTER] * len(words)
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, grid_size)
    
    # Check for any overlaps and verify consistency
    position_map = {}
    for placement in grid.solution:
        for i, coord in enumerate(placement.coordinates):
            pos = (coord.row, coord.col)
            letter = placement.word[i]
            
            if pos in position_map:
                # This position is shared - verify same letter
                existing_letter = position_map[pos]
                assert letter == existing_letter, (
                    f"Overlap inconsistency at {pos}: "
                    f"expected '{existing_letter}' but got '{letter}'"
                )
            else:
                position_map[pos] = letter
            
            # Verify grid matches placement
            assert grid.letters[coord.row][coord.col] == letter


@given(
    word1=st.text(
        alphabet=st.characters(min_codepoint=65, max_codepoint=90),
        min_size=4,
        max_size=8
    ).filter(lambda x: x.isalpha()),
    word2=st.text(
        alphabet=st.characters(min_codepoint=65, max_codepoint=90),
        min_size=4,
        max_size=8
    ).filter(lambda x: x.isalpha()),
    grid_size=st.integers(min_value=10, max_value=15)
)
def test_two_word_overlap_consistency(word1, word2, grid_size):
    """Test overlap consistency specifically between two words."""
    assume(word1 != word2)
    assume(len(set(word1) & set(word2)) > 0)  # Words must share at least one letter
    
    words = [word1.upper(), word2.upper()]
    word_types = [WordType.CHARACTER, WordType.DEFINING]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, grid_size)
    
    if len(grid.solution) >= 2:  # Both words were placed
        # Create position mapping
        positions = {}
        for placement in grid.solution:
            for i, coord in enumerate(placement.coordinates):
                pos = (coord.row, coord.col)
                letter = placement.word[i]
                
                if pos in positions:
                    # Overlap detected - verify consistency
                    assert positions[pos] == letter, (
                        f"Inconsistent overlap at {pos}: "
                        f"'{positions[pos]}' vs '{letter}'"
                    )
                else:
                    positions[pos] = letter