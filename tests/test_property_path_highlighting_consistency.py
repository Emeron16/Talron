"""Property test for path highlighting consistency.

**Feature: themed-word-search-game, Property 9: Path highlighting consistency**
**Validates: Requirements 4.1, 4.5**
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.services.grid_generator import GridGenerator
from src.services.selection_validator import SelectionValidator
from src.models.core import WordType, Coordinate


class MockHighlighter:
    """Mock highlighter to track highlighting behavior for testing."""
    
    def __init__(self):
        self.highlighted_paths = []
        self.cleared_count = 0
    
    def highlight_path(self, coordinates):
        """Mock method to highlight a path."""
        self.highlighted_paths.append(coordinates.copy())
    
    def clear_highlight(self):
        """Mock method to clear highlighting."""
        self.cleared_count += 1
    
    def get_last_highlighted_path(self):
        """Get the most recently highlighted path."""
        return self.highlighted_paths[-1] if self.highlighted_paths else None


class HighlightingSelectionValidator(SelectionValidator):
    """Extended SelectionValidator that tracks highlighting for testing."""
    
    def __init__(self, grid, highlighter=None):
        super().__init__(grid)
        self.highlighter = highlighter or MockHighlighter()
        self.last_highlighted_path = None
    
    def validate_selection_with_highlighting(self, coordinates):
        """
        Validate selection and provide highlighting feedback.
        
        This method simulates the UI highlighting behavior that should occur
        when a player makes a selection.
        """
        # Handle empty selection
        if not coordinates:
            self.highlighter.clear_highlight()
            return False, None
        
        # Validate path connectivity first
        if not self._validate_path_connectivity(coordinates):
            self.highlighter.clear_highlight()
            return False, None
        
        # Validate bounds
        if not self._validate_coordinates_bounds(coordinates):
            self.highlighter.clear_highlight()
            return False, None
        
        # For valid adjacent paths, provide highlighting
        self.highlighter.highlight_path(coordinates)
        self.last_highlighted_path = coordinates.copy()
        
        # Then validate if it's a real word
        is_valid, word = self.validate_selection(coordinates)
        
        return is_valid, word
    
    def clear_selection(self):
        """Override to include highlighting clear."""
        super().clear_selection()
        self.highlighter.clear_highlight()


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
def test_path_highlighting_consistency(words, grid_size):
    """
    Property 9: Path highlighting consistency
    For any valid adjacent-cell selection path, the system should provide 
    visual feedback highlighting the selected letters.
    """
    # Filter out duplicate words and ensure they're valid
    unique_words = list(set(word.upper() for word in words if word.isalpha()))
    assume(len(unique_words) > 0)
    
    # Create word types
    word_types = [WordType.CHARACTER if i % 2 == 0 else WordType.DEFINING 
                  for i in range(len(unique_words))]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(unique_words, word_types, grid_size)
    
    highlighter = MockHighlighter()
    validator = HighlightingSelectionValidator(grid, highlighter)
    
    # Test highlighting for valid adjacent paths (solution words)
    for placement in grid.solution:
        initial_highlight_count = len(highlighter.highlighted_paths)
        
        # Validate with highlighting
        is_valid, found_word = validator.validate_selection_with_highlighting(placement.coordinates)
        
        # Valid adjacent path should be highlighted
        assert len(highlighter.highlighted_paths) > initial_highlight_count, (
            f"Valid path for word '{placement.word}' should be highlighted"
        )
        
        # The highlighted path should match the input coordinates
        last_highlighted = highlighter.get_last_highlighted_path()
        assert last_highlighted == placement.coordinates, (
            f"Highlighted path should match input coordinates for word '{placement.word}'"
        )
        
        # Store the highlighted path for consistency check
        validator_highlighted_path = validator.last_highlighted_path
        assert validator_highlighted_path == placement.coordinates, (
            f"Validator should track the highlighted path for word '{placement.word}'"
        )


@given(
    grid_size=st.integers(min_value=8, max_value=12)
)
def test_invalid_path_highlighting_behavior(grid_size):
    """Test highlighting behavior for invalid paths."""
    words = ["TEST", "WORD", "GAME"]
    word_types = [WordType.CHARACTER] * len(words)
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, grid_size)
    
    highlighter = MockHighlighter()
    validator = HighlightingSelectionValidator(grid, highlighter)
    
    # Test disconnected path (should not be highlighted)
    disconnected_coords = [
        Coordinate(0, 0),
        Coordinate(grid_size-1, grid_size-1)  # Far corner - disconnected
    ]
    
    initial_clear_count = highlighter.cleared_count
    initial_highlight_count = len(highlighter.highlighted_paths)
    
    is_valid, found_word = validator.validate_selection_with_highlighting(disconnected_coords)
    
    # Invalid path should not be highlighted, but should trigger clear
    assert highlighter.cleared_count > initial_clear_count, (
        "Invalid disconnected path should trigger highlight clearing"
    )
    assert len(highlighter.highlighted_paths) == initial_highlight_count, (
        "Invalid disconnected path should not add new highlighting"
    )
    assert not is_valid, "Disconnected path should be invalid"
    assert found_word is None, "Invalid path should not return a word"


@given(
    grid_size=st.integers(min_value=8, max_value=12)
)
def test_out_of_bounds_highlighting_behavior(grid_size):
    """Test highlighting behavior for out-of-bounds coordinates."""
    words = ["HELLO"]
    word_types = [WordType.CHARACTER]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, grid_size)
    
    highlighter = MockHighlighter()
    validator = HighlightingSelectionValidator(grid, highlighter)
    
    # Test out of bounds coordinates
    out_of_bounds_coords = [
        Coordinate(0, 0),
        Coordinate(grid_size, 0)  # Out of bounds
    ]
    
    initial_clear_count = highlighter.cleared_count
    initial_highlight_count = len(highlighter.highlighted_paths)
    
    is_valid, found_word = validator.validate_selection_with_highlighting(out_of_bounds_coords)
    
    # Out of bounds should trigger clear, not highlighting
    assert highlighter.cleared_count > initial_clear_count, (
        "Out of bounds coordinates should trigger highlight clearing"
    )
    assert len(highlighter.highlighted_paths) == initial_highlight_count, (
        "Out of bounds coordinates should not add new highlighting"
    )
    assert not is_valid, "Out of bounds path should be invalid"


@given(
    grid_size=st.integers(min_value=8, max_value=12)
)
def test_adjacent_path_highlighting_consistency(grid_size):
    """Test that all valid adjacent paths get consistent highlighting."""
    words = ["CAT", "DOG"]
    word_types = [WordType.CHARACTER, WordType.DEFINING]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, grid_size)
    
    highlighter = MockHighlighter()
    validator = HighlightingSelectionValidator(grid, highlighter)
    
    # Create various valid adjacent paths
    valid_adjacent_paths = [
        # Horizontal path
        [Coordinate(0, 0), Coordinate(0, 1), Coordinate(0, 2)],
        # Vertical path  
        [Coordinate(1, 0), Coordinate(2, 0), Coordinate(3, 0)],
        # Diagonal path
        [Coordinate(2, 2), Coordinate(3, 3), Coordinate(4, 4)],
        # Mixed direction path
        [Coordinate(5, 5), Coordinate(5, 6), Coordinate(6, 6)]
    ]
    
    for path in valid_adjacent_paths:
        # Skip paths that go out of bounds
        if any(coord.row >= grid_size or coord.col >= grid_size for coord in path):
            continue
            
        initial_highlight_count = len(highlighter.highlighted_paths)
        
        # Test highlighting (may or may not be a valid word, but should highlight if adjacent)
        is_path_connected = validator._validate_path_connectivity(path)
        is_bounds_valid = validator._validate_coordinates_bounds(path)
        
        if is_path_connected and is_bounds_valid:
            validator.validate_selection_with_highlighting(path)
            
            # Should be highlighted since it's a valid adjacent path
            assert len(highlighter.highlighted_paths) > initial_highlight_count, (
                f"Valid adjacent path {path} should be highlighted"
            )
            
            # Highlighted path should match input
            last_highlighted = highlighter.get_last_highlighted_path()
            assert last_highlighted == path, (
                f"Highlighted path should match input path {path}"
            )


def test_single_cell_highlighting():
    """Test highlighting behavior for single cell selections."""
    words = ["A"]
    word_types = [WordType.CHARACTER]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, 10)
    
    highlighter = MockHighlighter()
    validator = HighlightingSelectionValidator(grid, highlighter)
    
    # Single cell selection
    single_cell = [Coordinate(0, 0)]
    
    initial_highlight_count = len(highlighter.highlighted_paths)
    
    is_valid, found_word = validator.validate_selection_with_highlighting(single_cell)
    
    # Single cell should be highlighted (trivially adjacent to itself)
    assert len(highlighter.highlighted_paths) > initial_highlight_count, (
        "Single cell selection should be highlighted"
    )
    
    last_highlighted = highlighter.get_last_highlighted_path()
    assert last_highlighted == single_cell, (
        "Single cell highlighting should match input"
    )


def test_empty_selection_no_highlighting():
    """Test that empty selections don't trigger highlighting."""
    words = ["TEST"]
    word_types = [WordType.CHARACTER]
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, 10)
    
    highlighter = MockHighlighter()
    validator = HighlightingSelectionValidator(grid, highlighter)
    
    initial_highlight_count = len(highlighter.highlighted_paths)
    initial_clear_count = highlighter.cleared_count
    
    # Empty selection
    is_valid, found_word = validator.validate_selection_with_highlighting([])
    
    # Empty selection should not add highlighting or clearing
    assert len(highlighter.highlighted_paths) == initial_highlight_count, (
        "Empty selection should not add highlighting"
    )
    assert highlighter.cleared_count > initial_clear_count, (
        "Empty selection should trigger clearing"
    )
    assert not is_valid, "Empty selection should be invalid"


@given(
    grid_size=st.integers(min_value=8, max_value=12)
)
def test_highlighting_state_consistency(grid_size):
    """Test that highlighting state remains consistent across multiple selections."""
    words = ["WORD", "TEST", "GAME"]
    word_types = [WordType.CHARACTER] * len(words)
    
    generator = GridGenerator(seed=42)
    grid = generator.generate_grid(words, word_types, grid_size)
    
    highlighter = MockHighlighter()
    validator = HighlightingSelectionValidator(grid, highlighter)
    
    # Make multiple selections and verify highlighting consistency
    for i, placement in enumerate(grid.solution[:2]):  # Test first 2 words
        initial_highlight_count = len(highlighter.highlighted_paths)
        
        # Make selection with highlighting
        is_valid, found_word = validator.validate_selection_with_highlighting(placement.coordinates)
        
        if is_valid:
            # Should have added highlighting
            assert len(highlighter.highlighted_paths) > initial_highlight_count, (
                f"Selection {i} should add highlighting"
            )
            
            # Current highlighted path should match this selection
            current_highlighted = validator.last_highlighted_path
            assert current_highlighted == placement.coordinates, (
                f"Selection {i} highlighting should be consistent"
            )
            
            # Highlighter should track the same path
            last_highlighted = highlighter.get_last_highlighted_path()
            assert last_highlighted == placement.coordinates, (
                f"Highlighter state should match validator state for selection {i}"
            )