"""Grid generation and word placement system for the themed word search game."""

import random
import string
from typing import List, Set, Optional, Tuple
from ..models.core import Grid, WordPlacement, Coordinate, WordType
from ..exceptions import GridGenerationError, WordPlacementError, GridTooSmallError


class GridGenerator:
    """Handles grid generation and word placement with adjacent-cell connectivity."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the grid generator with optional random seed for testing."""
        if seed is not None:
            random.seed(seed)
    
    def generate_grid(self, words: List[str], word_types: List[WordType], size: int,
                     min_success_rate: float = 0.8) -> Grid:
        """
        Generate a complete grid with words placed and empty cells filled.

        Args:
            words: List of words to place in the grid
            word_types: List of word types corresponding to each word
            size: Size of the N×N grid
            min_success_rate: Minimum fraction of words that must be placed (0.0-1.0)

        Returns:
            Grid object with placed words and filled letters

        Raises:
            ValueError: If words and word_types lists don't match in length.
            GridTooSmallError: If grid is too small for the words.
            WordPlacementError: If too many words fail to place.
        """
        if len(words) != len(word_types):
            raise ValueError("Words and word_types lists must have the same length")

        if not words:
            # Empty word list is valid, return empty grid
            letters = [['' for _ in range(size)] for _ in range(size)]
            self._fill_empty_cells(letters, size)
            return Grid(size=size, letters=letters, solution=[], discovered_words=set())

        # Validate grid size - check if longest word can fit
        max_word_length = max(len(word) for word in words)
        if size < max_word_length:
            # Grid is too small for the longest word
            raise GridTooSmallError(size, len(words))

        # Initialize empty grid
        letters = [['' for _ in range(size)] for _ in range(size)]
        solution = []
        failed_words = []

        # Attempt to place each word
        for word, word_type in zip(words, word_types):
            placement = self._place_word(word, word_type, letters, size)
            if placement:
                solution.append(placement)
                self._apply_word_to_grid(placement, letters)
            else:
                failed_words.append(word)

        # Check if enough words were placed
        success_rate = len(solution) / len(words) if words else 1.0
        if success_rate < min_success_rate:
            raise WordPlacementError(len(failed_words), len(words))

        # Fill empty cells with random letters
        self._fill_empty_cells(letters, size)

        return Grid(
            size=size,
            letters=letters,
            solution=solution,
            discovered_words=set()
        )
    
    def _place_word(self, word: str, word_type: WordType, letters: List[List[str]], size: int) -> Optional[WordPlacement]:
        """
        Attempt to place a word in the grid with adjacent-cell connectivity.

        Args:
            word: The word to place
            word_type: Type of the word (character or defining)
            letters: Current state of the grid
            size: Size of the grid

        Returns:
            WordPlacement if successful, None if placement failed
        """
        max_attempts = 100

        for _ in range(max_attempts):
            # Try random starting position and direction
            start_row = random.randint(0, size - 1)
            start_col = random.randint(0, size - 1)

            # Try to build a path from this starting position
            # CRITICAL: Only accept paths that don't reuse existing letters
            # This ensures players can actually find the word
            path = self._find_valid_path(word, start_row, start_col, letters, size, allow_reuse=False)
            if path:
                return WordPlacement(
                    word=word.upper(),
                    coordinates=path,
                    word_type=word_type
                )

        return None
    
    def _find_valid_path(self, word: str, start_row: int, start_col: int,
                        letters: List[List[str]], size: int, allow_reuse: bool = True) -> Optional[List[Coordinate]]:
        """
        Find a valid path for placing a word using adjacent-cell connectivity.

        Args:
            word: The word to place
            start_row: Starting row position
            start_col: Starting column position
            letters: Current state of the grid
            size: Size of the grid
            allow_reuse: If False, only accept paths through empty cells (ensures player can find it)

        Returns:
            List of coordinates if valid path found, None otherwise
        """
        word = word.upper()
        path = [Coordinate(start_row, start_col)]

        # Check if starting position is compatible
        if letters[start_row][start_col]:
            if letters[start_row][start_col] != word[0]:
                return None
            if not allow_reuse:
                # If we don't allow reuse, starting position must be empty
                return None

        # Build path letter by letter
        for i in range(1, len(word)):
            next_coord = self._find_next_position(
                word[i], path[-1], path, letters, size, allow_reuse
            )
            if not next_coord:
                return None
            path.append(next_coord)

        return path
    
    def _find_next_position(self, letter: str, current: Coordinate,
                           used_positions: List[Coordinate], letters: List[List[str]],
                           size: int, allow_reuse: bool = True) -> Optional[Coordinate]:
        """
        Find the next valid adjacent position for a letter.

        Args:
            letter: The letter to place
            current: Current coordinate position
            used_positions: Already used coordinates in this path
            letters: Current state of the grid
            size: Size of the grid
            allow_reuse: If False, only accept empty cells

        Returns:
            Next coordinate if found, None otherwise
        """
        # Get all adjacent positions (4 directions - only horizontal and vertical)
        directions = [
                      (-1, 0),          # Up
            (0, -1),           (0, 1),  # Left, Right
                      (1, 0)            # Down
        ]

        candidates = []
        for dr, dc in directions:
            new_row = current.row + dr
            new_col = current.col + dc

            # Check bounds
            if 0 <= new_row < size and 0 <= new_col < size:
                new_coord = Coordinate(new_row, new_col)

                # Skip if already used in this path
                if new_coord in used_positions:
                    continue

                # Check if position is compatible
                current_letter = letters[new_row][new_col]

                if allow_reuse:
                    # Original behavior: can reuse cells with matching letters
                    if not current_letter or current_letter == letter:
                        candidates.append(new_coord)
                else:
                    # Strict behavior: only empty cells allowed (ensures player can find word)
                    if not current_letter:
                        candidates.append(new_coord)

        # Return random candidate if any available
        return random.choice(candidates) if candidates else None
    
    def _apply_word_to_grid(self, placement: WordPlacement, letters: List[List[str]]):
        """
        Apply a word placement to the grid letters.
        
        Args:
            placement: The word placement to apply
            letters: The grid to modify
        """
        for i, coord in enumerate(placement.coordinates):
            letters[coord.row][coord.col] = placement.word[i]
    
    def _fill_empty_cells(self, letters: List[List[str]], size: int):
        """
        Fill empty cells in the grid with random letters.
        
        Args:
            letters: The grid to fill
            size: Size of the grid
        """
        for row in range(size):
            for col in range(size):
                if not letters[row][col]:
                    letters[row][col] = random.choice(string.ascii_uppercase)
    
    def calculate_word_capacity(self, grid_size: int, word_lengths: List[int]) -> int:
        """
        Calculate the maximum number of words that can theoretically fit in a grid.
        
        Args:
            grid_size: Size of the N×N grid
            word_lengths: List of word lengths to place
            
        Returns:
            Maximum number of words that can fit
        """
        total_cells = grid_size * grid_size
        total_letters_needed = sum(word_lengths)
        
        # Conservative estimate accounting for overlaps and placement constraints
        # Assume average 20% overlap efficiency
        overlap_factor = 0.8
        effective_letters_needed = int(total_letters_needed * overlap_factor)
        
        if effective_letters_needed <= total_cells:
            return len(word_lengths)
        else:
            # Calculate how many words can fit
            cumulative_length = 0
            word_count = 0
            for length in sorted(word_lengths):
                if cumulative_length + int(length * overlap_factor) <= total_cells:
                    cumulative_length += int(length * overlap_factor)
                    word_count += 1
                else:
                    break
            return word_count
    
    def validate_adjacent_connectivity(self, coordinates: List[Coordinate]) -> bool:
        """
        Validate that a sequence of coordinates represents adjacent-cell connectivity.
        
        Args:
            coordinates: List of coordinates to validate
            
        Returns:
            True if all coordinates are adjacent, False otherwise
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