"""Hint system for providing gameplay assistance."""

import random
from typing import Optional, List, Tuple
from ..models.core import Grid, Coordinate, WordPlacement


class HintSystem:
    """Manages hints for the player."""

    def __init__(self, max_hints: int = 3):
        """Initialize the hint system.

        Args:
            max_hints: Maximum number of hints available per game.
        """
        self.max_hints = max_hints
        self.hints_remaining = max_hints
        self.revealed_hints: List[str] = []

    def reset(self):
        """Reset hints for a new game."""
        self.hints_remaining = self.max_hints
        self.revealed_hints.clear()

    def get_hint(self, grid: Grid, hint_type: str = 'auto') -> Optional[dict]:
        """Get a hint for the player.

        Args:
            grid: Current game grid.
            hint_type: Type of hint ('letter', 'word', 'location', 'auto').

        Returns:
            Dictionary with hint information or None if no hints available.
        """
        if self.hints_remaining <= 0:
            return None

        # Get unfound words
        unfound_words = self._get_unfound_words(grid)
        if not unfound_words:
            return None

        # Auto mode picks the hint type
        if hint_type == 'auto':
            hint_type = random.choice(['letter', 'word', 'location'])

        # Generate hint based on type
        hint_data = None
        if hint_type == 'letter':
            hint_data = self._get_letter_hint(grid, unfound_words)
        elif hint_type == 'word':
            hint_data = self._get_word_hint(unfound_words)
        elif hint_type == 'location':
            hint_data = self._get_location_hint(grid, unfound_words)

        if hint_data:
            self.hints_remaining -= 1
            self.revealed_hints.append(hint_data.get('message', ''))

        return hint_data

    def _get_unfound_words(self, grid: Grid) -> List[WordPlacement]:
        """Get list of unfound word placements.

        Args:
            grid: Game grid.

        Returns:
            List of unfound WordPlacement objects.
        """
        return [p for p in grid.solution if p.word not in grid.discovered_words]

    def _get_letter_hint(self, grid: Grid, unfound: List[WordPlacement]) -> dict:
        """Get a hint revealing the first letter of a word.

        Args:
            grid: Game grid.
            unfound: List of unfound word placements.

        Returns:
            Hint dictionary.
        """
        placement = random.choice(unfound)
        first_letter = placement.word[0]

        return {
            'type': 'letter',
            'message': f"There's a word starting with '{first_letter}'",
            'letter': first_letter,
            'word_length': len(placement.word),
            'hint_detail': f"It's {len(placement.word)} letters long"
        }

    def _get_word_hint(self, unfound: List[WordPlacement]) -> dict:
        """Get a hint revealing part of a word.

        Args:
            unfound: List of unfound word placements.

        Returns:
            Hint dictionary.
        """
        placement = random.choice(unfound)
        word = placement.word

        # Reveal some letters based on word length
        reveal_count = max(1, len(word) // 3)
        revealed_positions = random.sample(range(len(word)), reveal_count)

        hint_word = ''
        for i, letter in enumerate(word):
            if i in revealed_positions:
                hint_word += letter
            else:
                hint_word += '_'

        word_type_hint = f"({placement.word_type.value})"

        return {
            'type': 'word',
            'message': f"Look for: {hint_word} {word_type_hint}",
            'pattern': hint_word,
            'word_type': placement.word_type.value
        }

    def _get_location_hint(self, grid: Grid, unfound: List[WordPlacement]) -> dict:
        """Get a hint about where a word is located.

        Args:
            grid: Game grid.
            unfound: List of unfound word placements.

        Returns:
            Hint dictionary.
        """
        placement = random.choice(unfound)

        # Get start position
        start_coord = placement.coordinates[0]

        # Divide grid into quadrants
        mid_point = grid.size // 2

        if start_coord.row < mid_point and start_coord.col < mid_point:
            quadrant = "top-left"
        elif start_coord.row < mid_point and start_coord.col >= mid_point:
            quadrant = "top-right"
        elif start_coord.row >= mid_point and start_coord.col < mid_point:
            quadrant = "bottom-left"
        else:
            quadrant = "bottom-right"

        # Get direction hint
        direction = self._get_direction_hint(placement.coordinates)

        return {
            'type': 'location',
            'message': f"Try the {quadrant} area, going {direction}",
            'quadrant': quadrant,
            'direction': direction,
            'start_coord': start_coord,
            'word_length': len(placement.word)
        }

    def _get_direction_hint(self, coordinates: List[Coordinate]) -> str:
        """Determine the general direction of a word path.

        Args:
            coordinates: List of coordinates forming the word.

        Returns:
            Direction description.
        """
        if len(coordinates) < 2:
            return "in a single cell"

        start = coordinates[0]
        end = coordinates[-1]

        row_diff = end.row - start.row
        col_diff = end.col - start.col

        # Determine primary direction
        if abs(row_diff) > abs(col_diff):
            # Mostly vertical
            if row_diff > 0:
                return "downward"
            else:
                return "upward"
        elif abs(col_diff) > abs(row_diff):
            # Mostly horizontal
            if col_diff > 0:
                return "right"
            else:
                return "left"
        else:
            # Diagonal
            if row_diff > 0 and col_diff > 0:
                return "diagonally down-right"
            elif row_diff > 0 and col_diff < 0:
                return "diagonally down-left"
            elif row_diff < 0 and col_diff > 0:
                return "diagonally up-right"
            else:
                return "diagonally up-left"

    def get_reveal_word_hint(self, grid: Grid) -> Optional[dict]:
        """Get a hint that completely reveals a word location.

        This is a "super hint" that costs 2 regular hints.

        Args:
            grid: Game grid.

        Returns:
            Hint dictionary with full word path or None.
        """
        if self.hints_remaining < 2:
            return None

        unfound = self._get_unfound_words(grid)
        if not unfound:
            return None

        # Pick shortest unfound word
        placement = min(unfound, key=lambda p: len(p.word))

        self.hints_remaining -= 2

        return {
            'type': 'reveal',
            'message': f"Here's where '{placement.word}' is located!",
            'word': placement.word,
            'coordinates': [(c.row, c.col) for c in placement.coordinates]
        }


class DifficultySettings:
    """Manages difficulty-related settings."""

    DIFFICULTY_PRESETS = {
        'easy': {
            'grid_size': 10,
            'time_limit': 20 * 60,  # 20 minutes
            'max_hints': 5,
            'show_word_count': True,
            'show_word_types': True
        },
        'medium': {
            'grid_size': 15,
            'time_limit': 15 * 60,  # 15 minutes
            'max_hints': 3,
            'show_word_count': True,
            'show_word_types': False
        },
        'hard': {
            'grid_size': 18,
            'time_limit': 10 * 60,  # 10 minutes
            'max_hints': 1,
            'show_word_count': False,
            'show_word_types': False
        },
        'expert': {
            'grid_size': 20,
            'time_limit': 8 * 60,  # 8 minutes
            'max_hints': 0,
            'show_word_count': False,
            'show_word_types': False
        }
    }

    @staticmethod
    def get_difficulty_settings(difficulty: str) -> dict:
        """Get settings for a difficulty level.

        Args:
            difficulty: Difficulty level name.

        Returns:
            Dictionary of settings.
        """
        return DifficultySettings.DIFFICULTY_PRESETS.get(
            difficulty.lower(),
            DifficultySettings.DIFFICULTY_PRESETS['medium']
        )

    @staticmethod
    def get_available_difficulties() -> List[str]:
        """Get list of available difficulty levels.

        Returns:
            List of difficulty names.
        """
        return list(DifficultySettings.DIFFICULTY_PRESETS.keys())
