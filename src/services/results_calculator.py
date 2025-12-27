"""Results calculation and scoring system for the word search game."""

from typing import Dict, Any
from datetime import datetime
from ..models.core import Game, Grid, GameStatus, WordType


class ResultsCalculator:
    """Calculates game results, scores, and completion metrics."""

    # Scoring constants
    POINTS_PER_WORD = 100
    TIME_BONUS_MULTIPLIER = 10
    DIFFICULTY_MULTIPLIERS = {
        8: 1.0,
        10: 1.2,
        12: 1.5,
        15: 1.8,
        20: 2.0
    }

    def __init__(self):
        """Initialize the results calculator."""
        pass

    def calculate_results(self, game: Game, grid: Grid, end_time: datetime) -> Dict[str, Any]:
        """Calculate complete game results and scoring.

        Args:
            game: The game instance.
            grid: The final game grid.
            end_time: Time when the game ended.

        Returns:
            Dictionary containing all result metrics.
        """
        # Basic stats
        total_words = len(grid.solution)
        found_words = len(grid.discovered_words)
        completion_percentage = (found_words / total_words * 100) if total_words > 0 else 0

        # Time calculation
        elapsed_time = int((end_time - game.start_time).total_seconds())
        time_remaining = max(0, game.time_limit - elapsed_time)

        # Perfect game check
        perfect_game = (found_words == total_words)

        # Score calculation
        word_score = self._calculate_word_score(found_words)
        time_bonus = self._calculate_time_bonus(time_remaining, perfect_game)
        difficulty_multiplier = self._get_difficulty_multiplier(game.grid_size)

        base_score = word_score + time_bonus
        total_score = int(base_score * difficulty_multiplier)

        # Word breakdown by type
        word_breakdown = self._calculate_word_breakdown(grid)

        return {
            # Basic stats
            'total_words': total_words,
            'found_words': found_words,
            'unfound_words': total_words - found_words,
            'completion_percentage': completion_percentage,

            # Time stats
            'elapsed_time': elapsed_time,
            'time_remaining': time_remaining,
            'time_limit': game.time_limit,

            # Game status
            'perfect_game': perfect_game,
            'game_status': game.status,
            'completed_on_time': game.status == GameStatus.COMPLETED,
            'expired': game.status == GameStatus.EXPIRED,

            # Score components
            'word_score': word_score,
            'time_bonus': time_bonus,
            'difficulty_multiplier': difficulty_multiplier,
            'total_score': total_score,

            # Word breakdown
            'word_breakdown': word_breakdown,

            # Game info
            'topic': game.topic,
            'subtopic': game.subtopic,
            'grid_size': game.grid_size
        }

    def _calculate_word_score(self, found_words: int) -> int:
        """Calculate base score from words found.

        Args:
            found_words: Number of words found.

        Returns:
            Base word score.
        """
        return found_words * self.POINTS_PER_WORD

    def _calculate_time_bonus(self, time_remaining: int, perfect_game: bool) -> int:
        """Calculate time bonus for early completion.

        Args:
            time_remaining: Seconds remaining when game ended.
            perfect_game: Whether all words were found.

        Returns:
            Time bonus points.
        """
        if not perfect_game:
            return 0

        return time_remaining * self.TIME_BONUS_MULTIPLIER

    def _get_difficulty_multiplier(self, grid_size: int) -> float:
        """Get difficulty multiplier based on grid size.

        Args:
            grid_size: Size of the grid.

        Returns:
            Difficulty multiplier.
        """
        # Find the closest defined multiplier
        if grid_size <= 8:
            return self.DIFFICULTY_MULTIPLIERS[8]
        elif grid_size <= 10:
            return self.DIFFICULTY_MULTIPLIERS[10]
        elif grid_size <= 12:
            return self.DIFFICULTY_MULTIPLIERS[12]
        elif grid_size <= 15:
            return self.DIFFICULTY_MULTIPLIERS[15]
        else:
            return self.DIFFICULTY_MULTIPLIERS[20]

    def _calculate_word_breakdown(self, grid: Grid) -> Dict[str, Dict[str, int]]:
        """Calculate breakdown of words by type.

        Args:
            grid: The game grid.

        Returns:
            Dictionary with word counts by type.
        """
        character_total = 0
        character_found = 0
        defining_total = 0
        defining_found = 0

        for word_placement in grid.solution:
            if word_placement.word_type == WordType.CHARACTER:
                character_total += 1
                if word_placement.word in grid.discovered_words:
                    character_found += 1
            else:
                defining_total += 1
                if word_placement.word in grid.discovered_words:
                    defining_found += 1

        return {
            'character_words': {
                'total': character_total,
                'found': character_found,
                'percentage': (character_found / character_total * 100) if character_total > 0 else 0
            },
            'defining_words': {
                'total': defining_total,
                'found': defining_found,
                'percentage': (defining_found / defining_total * 100) if defining_total > 0 else 0
            }
        }

    def get_performance_rating(self, completion_percentage: float, perfect_game: bool,
                              time_percentage: float) -> str:
        """Get a performance rating based on completion and time.

        Args:
            completion_percentage: Percentage of words found.
            perfect_game: Whether all words were found.
            time_percentage: Percentage of time used.

        Returns:
            Performance rating string.
        """
        if perfect_game:
            if time_percentage < 50:
                return "LEGENDARY"
            elif time_percentage < 75:
                return "EXCEPTIONAL"
            else:
                return "EXCELLENT"
        elif completion_percentage >= 90:
            return "OUTSTANDING"
        elif completion_percentage >= 75:
            return "GREAT"
        elif completion_percentage >= 50:
            return "GOOD"
        elif completion_percentage >= 25:
            return "FAIR"
        else:
            return "NEEDS_IMPROVEMENT"

    def calculate_session_stats(self, results_list: list) -> Dict[str, Any]:
        """Calculate statistics across multiple game sessions.

        Args:
            results_list: List of result dictionaries from multiple games.

        Returns:
            Dictionary with session statistics.
        """
        if not results_list:
            return {
                'games_played': 0,
                'total_words_found': 0,
                'perfect_games': 0,
                'average_completion': 0.0,
                'total_score': 0,
                'average_score': 0.0
            }

        games_played = len(results_list)
        total_words_found = sum(r['found_words'] for r in results_list)
        perfect_games = sum(1 for r in results_list if r['perfect_game'])
        average_completion = sum(r['completion_percentage'] for r in results_list) / games_played
        total_score = sum(r['total_score'] for r in results_list)
        average_score = total_score / games_played

        return {
            'games_played': games_played,
            'total_words_found': total_words_found,
            'perfect_games': perfect_games,
            'perfect_game_rate': (perfect_games / games_played * 100) if games_played > 0 else 0,
            'average_completion': average_completion,
            'total_score': total_score,
            'average_score': average_score,
            'best_score': max(r['total_score'] for r in results_list),
            'best_completion': max(r['completion_percentage'] for r in results_list)
        }
