"""Property-based tests for results calculation accuracy.

Property 14: Results calculation accuracy
- Validates: Requirements 7.1, 7.2, 7.3
"""

import pytest
from hypothesis import given, strategies as st, assume
from datetime import datetime, timedelta
import uuid

from src.models.core import Game, Grid, GameStatus, WordPlacement, WordType, Coordinate
from src.services.results_calculator import ResultsCalculator


# Strategies for generating test data
@st.composite
def game_strategy(draw):
    """Generate a valid Game instance."""
    grid_size = draw(st.integers(min_value=8, max_value=20))
    time_limit = draw(st.integers(min_value=60, max_value=1800))
    max_words = draw(st.integers(min_value=1, max_value=50))

    return Game(
        id=str(uuid.uuid4()),
        topic=draw(st.sampled_from(['anime', 'movies', 'shows'])),
        subtopic=draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        grid_size=grid_size,
        time_limit=time_limit,
        max_words=max_words,
        start_time=datetime.now(),
        status=draw(st.sampled_from([GameStatus.COMPLETED, GameStatus.EXPIRED]))
    )


@st.composite
def word_placement_strategy(draw, grid_size, word_type=None):
    """Generate a valid WordPlacement."""
    word_length = draw(st.integers(min_value=3, max_value=min(12, grid_size)))
    word = draw(st.text(min_size=word_length, max_size=word_length,
                       alphabet=st.characters(whitelist_categories=('Lu',))))

    # Generate valid coordinates within grid
    start_row = draw(st.integers(min_value=0, max_value=grid_size - 1))
    start_col = draw(st.integers(min_value=0, max_value=grid_size - 1))

    coordinates = []
    used_positions = set()
    row, col = start_row, start_col

    for i in range(word_length):
        # Ensure we stay within grid and don't reuse positions
        if (row, col) in used_positions or row >= grid_size or col >= grid_size:
            # Try to find adjacent position
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if (0 <= new_row < grid_size and 0 <= new_col < grid_size and
                    (new_row, new_col) not in used_positions):
                    row, col = new_row, new_col
                    break
            else:
                # Can't place word, assume it won't work
                assume(False)

        coordinates.append(Coordinate(row=row, col=col))
        used_positions.add((row, col))

        # Move to adjacent cell for next letter
        if i < word_length - 1:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            dr, dc = draw(st.sampled_from(directions))
            row, col = row + dr, col + dc

    if word_type is None:
        word_type = draw(st.sampled_from([WordType.CHARACTER, WordType.DEFINING]))

    return WordPlacement(word=word, coordinates=coordinates, word_type=word_type)


@st.composite
def grid_strategy(draw, game):
    """Generate a valid Grid instance."""
    size = game.grid_size

    # Generate letters
    letters = []
    for _ in range(size):
        row = []
        for _ in range(size):
            row.append(draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ')))
        letters.append(row)

    # Generate solution with at least 1 word
    num_words = draw(st.integers(min_value=1, max_value=min(game.max_words, 20)))
    solution = []

    for _ in range(num_words):
        try:
            placement = draw(word_placement_strategy(size))
            solution.append(placement)
        except:
            # Skip if we can't generate valid placement
            continue

    assume(len(solution) > 0)

    # Generate discovered words (subset of solution)
    solution_words = [wp.word for wp in solution]
    num_discovered = draw(st.integers(min_value=0, max_value=len(solution_words)))
    discovered_words = set(draw(st.lists(
        st.sampled_from(solution_words),
        min_size=num_discovered,
        max_size=num_discovered,
        unique=True
    )))

    return Grid(size=size, letters=letters, solution=solution, discovered_words=discovered_words)


class TestResultsCalculationAccuracy:
    """Property tests for results calculation accuracy."""

    @given(game=game_strategy(), elapsed_seconds=st.integers(min_value=1, max_value=1800))
    def test_property_14_completion_percentage_calculation(self, game, elapsed_seconds):
        """Property 14a: Completion percentage is correctly calculated.

        Validates: Requirement 7.2 - percentage of words discovered
        """
        calculator = ResultsCalculator()
        grid = Grid(
            size=game.grid_size,
            letters=[['A' for _ in range(game.grid_size)] for _ in range(game.grid_size)],
            solution=[
                WordPlacement(
                    word=f"WORD{i}",
                    coordinates=[Coordinate(row=0, col=j) for j in range(5)],
                    word_type=WordType.CHARACTER
                ) for i in range(10)
            ],
            discovered_words=set([f"WORD{i}" for i in range(5)])  # Found 5 out of 10
        )

        end_time = game.start_time + timedelta(seconds=elapsed_seconds)
        results = calculator.calculate_results(game, grid, end_time)

        # Property: Completion percentage should equal (found/total) * 100
        expected_percentage = (5 / 10) * 100
        assert results['completion_percentage'] == expected_percentage
        assert results['found_words'] == 5
        assert results['total_words'] == 10
        assert results['unfound_words'] == 5

    @given(game=game_strategy())
    def test_property_14_perfect_game_detection(self, game):
        """Property 14b: Perfect game is correctly detected.

        Validates: Requirement 7.1, 7.3 - total words found and perfect completion
        """
        calculator = ResultsCalculator()

        # Create grid with all words found
        solution = [
            WordPlacement(
                word=f"WORD{i}",
                coordinates=[Coordinate(row=0, col=j) for j in range(5)],
                word_type=WordType.CHARACTER
            ) for i in range(5)
        ]

        grid = Grid(
            size=game.grid_size,
            letters=[['A' for _ in range(game.grid_size)] for _ in range(game.grid_size)],
            solution=solution,
            discovered_words=set([f"WORD{i}" for i in range(5)])  # All words found
        )

        end_time = game.start_time + timedelta(seconds=60)
        results = calculator.calculate_results(game, grid, end_time)

        # Property: Perfect game when all words are found
        assert results['perfect_game'] is True
        assert results['completion_percentage'] == 100.0
        assert results['found_words'] == results['total_words']

    @given(game=game_strategy())
    def test_property_14_imperfect_game_detection(self, game):
        """Property 14c: Imperfect game is correctly detected.

        Validates: Requirement 7.1, 7.2 - accurate word counts and percentages
        """
        calculator = ResultsCalculator()

        # Create grid with some words missing
        solution = [
            WordPlacement(
                word=f"WORD{i}",
                coordinates=[Coordinate(row=0, col=j) for j in range(5)],
                word_type=WordType.CHARACTER
            ) for i in range(10)
        ]

        grid = Grid(
            size=game.grid_size,
            letters=[['A' for _ in range(game.grid_size)] for _ in range(game.grid_size)],
            solution=solution,
            discovered_words=set([f"WORD{i}" for i in range(7)])  # 7 out of 10
        )

        end_time = game.start_time + timedelta(seconds=60)
        results = calculator.calculate_results(game, grid, end_time)

        # Property: Not perfect when some words are missing
        assert results['perfect_game'] is False
        assert results['completion_percentage'] == 70.0
        assert results['found_words'] < results['total_words']
        assert results['unfound_words'] == 3

    @given(game=game_strategy(), elapsed_seconds=st.integers(min_value=1, max_value=1800))
    def test_property_14_time_calculations(self, game, elapsed_seconds):
        """Property 14d: Time calculations are accurate.

        Validates: Requirement 7.3 - completion time tracking
        """
        assume(elapsed_seconds <= game.time_limit)

        calculator = ResultsCalculator()
        grid = Grid(
            size=game.grid_size,
            letters=[['A' for _ in range(game.grid_size)] for _ in range(game.grid_size)],
            solution=[
                WordPlacement(
                    word=f"WORD{i}",
                    coordinates=[Coordinate(row=0, col=j) for j in range(5)],
                    word_type=WordType.CHARACTER
                ) for i in range(5)
            ],
            discovered_words=set([f"WORD{i}" for i in range(5)])
        )

        end_time = game.start_time + timedelta(seconds=elapsed_seconds)
        results = calculator.calculate_results(game, grid, end_time)

        # Property: Time calculations should be accurate
        assert results['elapsed_time'] == elapsed_seconds
        assert results['time_remaining'] == max(0, game.time_limit - elapsed_seconds)
        assert results['time_limit'] == game.time_limit

    @given(game=game_strategy())
    def test_property_14_word_type_breakdown(self, game):
        """Property 14e: Word breakdown by type is accurate.

        Validates: Requirement 7.1 - accurate word counting by type
        """
        calculator = ResultsCalculator()

        # Create grid with specific word types (using fixed-length words)
        solution = [
            WordPlacement(
                word=f"WORD{i}",  # 5 characters
                coordinates=[Coordinate(row=0, col=j) for j in range(5)],
                word_type=WordType.CHARACTER
            ) for i in range(6)
        ] + [
            WordPlacement(
                word=f"TERM{i}",  # 5 characters
                coordinates=[Coordinate(row=1, col=j) for j in range(5)],
                word_type=WordType.DEFINING
            ) for i in range(4)
        ]

        # Found 4 character words and 2 defining words
        grid = Grid(
            size=game.grid_size,
            letters=[['A' for _ in range(game.grid_size)] for _ in range(game.grid_size)],
            solution=solution,
            discovered_words=set([f"WORD{i}" for i in range(4)] + [f"TERM{i}" for i in range(2)])
        )

        end_time = game.start_time + timedelta(seconds=60)
        results = calculator.calculate_results(game, grid, end_time)

        # Property: Word breakdown should be accurate by type
        breakdown = results['word_breakdown']
        assert breakdown['character_words']['total'] == 6
        assert breakdown['character_words']['found'] == 4
        assert breakdown['defining_words']['total'] == 4
        assert breakdown['defining_words']['found'] == 2

    @given(game=game_strategy())
    def test_property_14_score_calculation_consistency(self, game):
        """Property 14f: Score calculation is consistent and non-negative.

        Validates: Requirements 7.1, 7.2 - score calculation
        """
        calculator = ResultsCalculator()
        grid = Grid(
            size=game.grid_size,
            letters=[['A' for _ in range(game.grid_size)] for _ in range(game.grid_size)],
            solution=[
                WordPlacement(
                    word=f"WORD{i}",
                    coordinates=[Coordinate(row=0, col=j) for j in range(5)],
                    word_type=WordType.CHARACTER
                ) for i in range(5)
            ],
            discovered_words=set([f"WORD{i}" for i in range(3)])
        )

        end_time = game.start_time + timedelta(seconds=60)
        results = calculator.calculate_results(game, grid, end_time)

        # Property: Scores should be non-negative and consistent
        assert results['word_score'] >= 0
        assert results['time_bonus'] >= 0
        assert results['total_score'] >= 0
        assert results['difficulty_multiplier'] >= 1.0

        # Property: Total score should be word_score + time_bonus multiplied by difficulty
        expected_total = int((results['word_score'] + results['time_bonus']) *
                           results['difficulty_multiplier'])
        assert results['total_score'] == expected_total

    @given(game=game_strategy())
    def test_property_14_zero_words_edge_case(self, game):
        """Property 14g: Handle edge case of zero words found.

        Validates: Requirement 7.1, 7.2 - edge case handling
        """
        calculator = ResultsCalculator()
        grid = Grid(
            size=game.grid_size,
            letters=[['A' for _ in range(game.grid_size)] for _ in range(game.grid_size)],
            solution=[
                WordPlacement(
                    word=f"WORD{i}",
                    coordinates=[Coordinate(row=0, col=j) for j in range(5)],
                    word_type=WordType.CHARACTER
                ) for i in range(5)
            ],
            discovered_words=set()  # No words found
        )

        end_time = game.start_time + timedelta(seconds=60)
        results = calculator.calculate_results(game, grid, end_time)

        # Property: Should handle zero words gracefully
        assert results['found_words'] == 0
        assert results['completion_percentage'] == 0.0
        assert results['perfect_game'] is False
        assert results['word_score'] == 0
        assert results['time_bonus'] == 0  # No bonus without perfect game
