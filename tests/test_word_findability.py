"""Test that all words placed in the grid can actually be found by players."""

import pytest
from src.services.grid_generator import GridGenerator
from src.services.selection_validator import SelectionValidator
from src.models.core import WordType


class TestWordFindability:
    """Test that generated grids only contain findable words."""

    def test_all_placed_words_are_findable(self):
        """Verify that every word placed in the grid can be found by the validator."""
        generator = GridGenerator(seed=42)

        # Test with words that have repeated letters
        words = ["LEVEL", "SPEED", "BELLE", "ARROW"]
        word_types = [WordType.DEFINING] * len(words)

        grid = generator.generate_grid(words, word_types, size=15)

        # Create validator
        validator = SelectionValidator(grid)

        # Check that every word in the solution can be validated
        for placement in grid.solution:
            word = placement.word
            coordinates = placement.coordinates

            # The validator should accept the exact path used in the solution
            is_valid, found_word = validator.validate_selection(coordinates)

            assert is_valid, f"Word '{word}' placed in grid but cannot be validated"
            assert found_word == word, f"Expected '{word}' but validator returned '{found_word}'"

    def test_no_letter_reuse_in_placements(self):
        """Verify that word placements don't reuse cells from other words."""
        generator = GridGenerator(seed=123)

        words = ["HERO", "VILLAIN", "QUEST", "MAGIC", "SWORD"]
        word_types = [WordType.DEFINING] * len(words)

        grid = generator.generate_grid(words, word_types, size=12)

        # Collect all coordinates used across all placements
        all_coords = []
        for placement in grid.solution:
            all_coords.extend(placement.coordinates)

        # Check that no coordinate appears more than once
        coord_tuples = [(c.row, c.col) for c in all_coords]
        unique_coords = set(coord_tuples)

        assert len(coord_tuples) == len(unique_coords), \
            "Words are sharing cells - this makes them unfindable by players"

    def test_repeated_letter_words(self):
        """Test words with repeated letters like LEVEL, PEPPER, etc."""
        generator = GridGenerator(seed=999)

        # These words have repeated letters which was causing the issue
        words = ["LEVEL", "PEPPER", "COFFEE", "LETTER"]
        word_types = [WordType.DEFINING] * len(words)

        grid = generator.generate_grid(words, word_types, size=15)
        validator = SelectionValidator(grid)

        # Every placed word should be findable
        for placement in grid.solution:
            is_valid, found_word = validator.validate_selection(placement.coordinates)
            assert is_valid, f"Word '{placement.word}' with repeated letters cannot be found"
            assert found_word == placement.word

    def test_horizontal_and_vertical_only(self):
        """Verify that all placed words use only horizontal and vertical connections."""
        generator = GridGenerator(seed=456)

        words = ["DRAGON", "WIZARD", "CASTLE"]
        word_types = [WordType.DEFINING] * len(words)

        grid = generator.generate_grid(words, word_types, size=12)

        # Check each word's path
        for placement in grid.solution:
            coords = placement.coordinates

            # Verify adjacent connectivity (horizontal/vertical only)
            for i in range(1, len(coords)):
                curr = coords[i-1]
                next_coord = coords[i]

                row_diff = abs(curr.row - next_coord.row)
                col_diff = abs(curr.col - next_coord.col)

                # Must be exactly 1 step in one direction (not diagonal)
                is_horizontal_or_vertical = (
                    (row_diff == 1 and col_diff == 0) or
                    (row_diff == 0 and col_diff == 1)
                )

                assert is_horizontal_or_vertical, \
                    f"Word '{placement.word}' has diagonal connection at position {i}"
