"""Selection validation and game interaction system for the themed word search game."""

from typing import List, Set, Optional, Tuple
from ..models.core import Grid, Coordinate, WordPlacement


class SelectionValidator:
    """Handles word selection validation, path connectivity, and discovered word tracking."""

    def __init__(self, grid: Grid = None):
        """
        Initialize the selection validator with a game grid.

        Args:
            grid: The game grid containing letters and solution (optional for static usage)
        """
        self.grid = grid
        self._solution_words = {placement.word: placement for placement in grid.solution} if grid else {}
    
    def validate_selection(self, grid_or_coordinates, coordinates=None):
        """
        Validate a player's word selection.

        Can be called in two ways:
        1. validate_selection(coordinates) - returns (is_valid, word) tuple
        2. validate_selection(grid, coordinates) - returns word string or None (for main.py compatibility)

        Args:
            grid_or_coordinates: Either Grid object or List[Coordinate]
            coordinates: List[Coordinate] if first arg is Grid, None otherwise

        Returns:
            Tuple (bool, str|None) when called with 1 arg, or str|None when called with 2 args
        """
        # Determine which calling convention is being used
        if coordinates is None:
            # Called as validate_selection(coordinates) - return tuple for backwards compatibility
            coords = grid_or_coordinates
            grid = self.grid
            return_tuple = True
        else:
            # Called as validate_selection(grid, coordinates) - return string for main.py
            grid = grid_or_coordinates
            coords = coordinates
            return_tuple = False

        if not coords:
            return (False, None) if return_tuple else None

        # Create temporary validator if needed
        if grid != self.grid:
            temp_validator = SelectionValidator(grid)
            word = temp_validator._validate(coords)
        else:
            word = self._validate(coords)

        if return_tuple:
            return (word is not None, word)
        else:
            return word

    def _validate(self, coordinates: List[Coordinate]) -> Optional[str]:
        """
        Internal validation logic.

        Args:
            coordinates: List of coordinates representing the selected path

        Returns:
            The word if valid, None if invalid
        """
        if not coordinates:
            return None

        # Validate path connectivity
        if not self._validate_path_connectivity(coordinates):
            return None

        # Validate coordinates are within grid bounds
        if not self._validate_coordinates_bounds(coordinates):
            return None

        # Extract word from coordinates
        word = self._extract_word_from_coordinates(coordinates)

        # Check if word exists in solution (solution words are uppercase)
        if word.upper() in self._solution_words:
            return word.upper()  # Return in same case as solution

        return None
    
    def _validate_path_connectivity(self, coordinates: List[Coordinate]) -> bool:
        """
        Validate that coordinates form a connected path through adjacent cells.
        
        Args:
            coordinates: List of coordinates to validate
            
        Returns:
            True if path is connected, False otherwise
        """
        if len(coordinates) < 2:
            return True
        
        for i in range(1, len(coordinates)):
            current = coordinates[i-1]
            next_coord = coordinates[i]
            
            # Check if coordinates are adjacent (4-directional - horizontal or vertical only)
            row_diff = abs(current.row - next_coord.row)
            col_diff = abs(current.col - next_coord.col)

            # Must be exactly 1 step in one direction (not diagonal, not same cell)
            if not ((row_diff == 1 and col_diff == 0) or (row_diff == 0 and col_diff == 1)):
                return False
        
        return True
    
    def _validate_coordinates_bounds(self, coordinates: List[Coordinate]) -> bool:
        """
        Validate that all coordinates are within grid bounds.
        
        Args:
            coordinates: List of coordinates to validate
            
        Returns:
            True if all coordinates are valid, False otherwise
        """
        for coord in coordinates:
            if coord.row < 0 or coord.row >= self.grid.size:
                return False
            if coord.col < 0 or coord.col >= self.grid.size:
                return False
        
        return True
    
    def _extract_word_from_coordinates(self, coordinates: List[Coordinate]) -> str:
        """
        Extract the word formed by the given coordinates.
        
        Args:
            coordinates: List of coordinates forming the word
            
        Returns:
            The word formed by the coordinates
        """
        word = ""
        for coord in coordinates:
            word += self.grid.letters[coord.row][coord.col]
        return word
    
    def mark_word_discovered(self, word: str) -> bool:
        """
        Mark a word as discovered and update game state.
        
        Args:
            word: The word to mark as discovered
            
        Returns:
            True if word was successfully marked, False if already discovered
        """
        if word in self.grid.discovered_words:
            return False
        
        if word in self._solution_words:
            self.grid.discovered_words.add(word)
            return True
        
        return False
    
    def is_word_discovered(self, word: str) -> bool:
        """
        Check if a word has already been discovered.
        
        Args:
            word: The word to check
            
        Returns:
            True if word is discovered, False otherwise
        """
        return word in self.grid.discovered_words
    
    def get_discovered_words(self) -> Set[str]:
        """
        Get the set of all discovered words.
        
        Returns:
            Set of discovered words
        """
        return self.grid.discovered_words.copy()
    
    def get_undiscovered_words(self) -> Set[str]:
        """
        Get the set of all undiscovered words.
        
        Returns:
            Set of undiscovered words
        """
        all_words = set(self._solution_words.keys())
        return all_words - self.grid.discovered_words
    
    def get_word_placement(self, word: str) -> Optional[WordPlacement]:
        """
        Get the placement information for a specific word.
        
        Args:
            word: The word to get placement for
            
        Returns:
            WordPlacement if word exists in solution, None otherwise
        """
        return self._solution_words.get(word)
    
    def clear_selection(self) -> None:
        """
        Clear any temporary selection state.
        
        This method is called when an invalid selection is made
        to reset any temporary highlighting or selection state.
        """
        # This method provides a hook for UI components to clear
        # visual selection state. The base implementation does nothing
        # as state management is handled by the UI layer.
        pass
    
    def get_progress_stats(self) -> Tuple[int, int, float]:
        """
        Get current progress statistics.
        
        Returns:
            Tuple of (discovered_count, total_count, percentage)
        """
        discovered_count = len(self.grid.discovered_words)
        total_count = len(self._solution_words)
        percentage = (discovered_count / total_count * 100) if total_count > 0 else 0.0
        
        return discovered_count, total_count, percentage
    
    def is_game_complete(self) -> bool:
        """
        Check if all words have been discovered.
        
        Returns:
            True if game is complete, False otherwise
        """
        return len(self.grid.discovered_words) == len(self._solution_words)
    
    def validate_and_process_selection(self, coordinates: List[Coordinate]) -> Tuple[bool, Optional[str], bool]:
        """
        Validate a selection and process it if valid.
        
        This is a convenience method that combines validation and state update.
        
        Args:
            coordinates: List of coordinates representing the selected path
            
        Returns:
            Tuple of (is_valid, word_if_valid, was_newly_discovered)
            - is_valid: True if selection forms a valid word
            - word_if_valid: The word if valid, None if invalid
            - was_newly_discovered: True if word was newly discovered, False if already found
        """
        is_valid, word = self.validate_selection(coordinates)
        
        if not is_valid:
            self.clear_selection()
            return False, None, False
        
        was_newly_discovered = self.mark_word_discovered(word)
        return True, word, was_newly_discovered