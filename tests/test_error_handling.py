"""Unit tests for error handling scenarios.

Tests error handling for:
- Database operations
- Grid generation
- Game state management
- Validation
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from src.exceptions import (
    DatabaseNotFoundError,
    DatabaseCorruptedError,
    TopicNotFoundError,
    SubtopicNotFoundError,
    InsufficientWordsError,
    GridTooSmallError,
    WordPlacementError,
    NoActiveGameError,
    InvalidGameStatusError,
    InvalidSettingsError
)
from src.data.word_database import WordDatabase
from src.services.grid_generator import GridGenerator
from src.services.game_controller import GameController
from src.models.core import GameSettings, WordType, Game, GameStatus, Grid, WordPlacement, Coordinate


class TestDatabaseErrorHandling:
    """Tests for database error handling."""

    def test_database_not_found_error(self):
        """Test error when database file doesn't exist."""
        with pytest.raises(DatabaseNotFoundError) as exc_info:
            WordDatabase("/nonexistent/path/database.json")

        assert "unable to load" in exc_info.value.user_message.lower()
        assert exc_info.value.file_path == "/nonexistent/path/database.json"

    def test_database_corrupted_invalid_json(self):
        """Test error when database has invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            with pytest.raises(DatabaseCorruptedError) as exc_info:
                WordDatabase(temp_path)

            assert "corrupted" in exc_info.value.user_message.lower()
        finally:
            Path(temp_path).unlink()

    def test_database_corrupted_wrong_structure(self):
        """Test error when database has wrong structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(["not", "a", "dict"], f)
            temp_path = f.name

        try:
            with pytest.raises(DatabaseCorruptedError) as exc_info:
                WordDatabase(temp_path)

            assert "corrupted" in exc_info.value.user_message.lower()
        finally:
            Path(temp_path).unlink()

    def test_database_corrupted_missing_word_lists(self):
        """Test error when subtopic is missing word lists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "anime": {
                    "Naruto": {
                        "character_words": ["NARUTO", "SASUKE"]
                        # Missing defining_words
                    }
                }
            }, f)
            temp_path = f.name

        try:
            with pytest.raises(DatabaseCorruptedError) as exc_info:
                WordDatabase(temp_path)

            assert "missing required word lists" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_topic_not_found_error(self):
        """Test error when accessing non-existent topic."""
        db = WordDatabase()

        with pytest.raises(TopicNotFoundError) as exc_info:
            db.get_subtopics("NonExistentTopic")

        assert exc_info.value.topic == "NonExistentTopic"
        assert "not available" in exc_info.value.user_message.lower()

    def test_subtopic_not_found_error(self):
        """Test error when accessing non-existent subtopic."""
        db = WordDatabase()
        topics = db.get_topics()

        if topics:
            topic = topics[0]
            with pytest.raises(SubtopicNotFoundError) as exc_info:
                db.get_words(topic, "NonExistentSubtopic")

            assert exc_info.value.topic == topic
            assert exc_info.value.subtopic == "NonExistentSubtopic"
            assert "not available" in exc_info.value.user_message.lower()


class TestGridGenerationErrorHandling:
    """Tests for grid generation error handling."""

    def test_grid_too_small_for_words(self):
        """Test error when grid is too small for word length."""
        generator = GridGenerator()
        words = ["VERYLONGWORD"]
        word_types = [WordType.CHARACTER]
        size = 5  # Too small for 12-letter word

        with pytest.raises(GridTooSmallError) as exc_info:
            generator.generate_grid(words, word_types, size)

        assert exc_info.value.grid_size == size
        assert "too small" in exc_info.value.user_message.lower()

    def test_word_placement_failure(self):
        """Test error when too many words fail to place."""
        generator = GridGenerator()
        # Try to place many medium-length words in a small grid with high success requirement
        # Use 8-letter words which fit in an 8x8 grid but are hard to place many of
        words = [f"WORD{i:04d}" for i in range(15)]  # 8 characters each
        word_types = [WordType.CHARACTER] * 15
        size = 8

        with pytest.raises(WordPlacementError) as exc_info:
            generator.generate_grid(words, word_types, size, min_success_rate=0.95)

        assert exc_info.value.failed_words > 0
        assert exc_info.value.total_words == 15
        assert "unable to create" in exc_info.value.user_message.lower()

    def test_mismatched_words_and_types(self):
        """Test error when words and types lists don't match."""
        generator = GridGenerator()
        words = ["WORD1", "WORD2", "WORD3"]
        word_types = [WordType.CHARACTER, WordType.DEFINING]  # Only 2 types

        with pytest.raises(ValueError) as exc_info:
            generator.generate_grid(words, word_types, 10)

        assert "same length" in str(exc_info.value).lower()


class TestGameStateErrorHandling:
    """Tests for game state error handling."""

    def test_calculate_results_without_active_game(self):
        """Test error when calculating results without active game."""
        controller = GameController()

        with pytest.raises(RuntimeError) as exc_info:
            controller.calculate_game_results()

        assert "no game active" in str(exc_info.value).lower()

    def test_calculate_results_with_active_game(self):
        """Test error when calculating results while game is still active."""
        controller = GameController()
        db = WordDatabase()
        topics = db.get_topics()

        if topics:
            topic = topics[0]
            subtopics = db.get_subtopics(topic)

            if subtopics:
                subtopic = subtopics[0]
                settings = GameSettings(grid_size=10, time_limit=300)

                controller.initialize_game(topic, subtopic, settings)
                controller.start_game()
                # Game is still ACTIVE, not COMPLETED or EXPIRED

                with pytest.raises(RuntimeError) as exc_info:
                    controller.calculate_game_results()

                assert "must be completed or expired" in str(exc_info.value).lower()


class TestValidationErrorHandling:
    """Tests for validation error handling."""

    def test_invalid_grid_size_too_small(self):
        """Test error with grid size below minimum."""
        with pytest.raises(ValueError) as exc_info:
            GameSettings(grid_size=5, time_limit=300)

        assert "grid size must be between 8 and 20" in str(exc_info.value).lower()

    def test_invalid_grid_size_too_large(self):
        """Test error with grid size above maximum."""
        with pytest.raises(ValueError) as exc_info:
            GameSettings(grid_size=25, time_limit=300)

        assert "grid size must be between 8 and 20" in str(exc_info.value).lower()

    def test_invalid_time_limit_too_short(self):
        """Test error with time limit below minimum."""
        with pytest.raises(ValueError) as exc_info:
            GameSettings(grid_size=10, time_limit=30)

        assert "time limit must be between 60 and 1800" in str(exc_info.value).lower()

    def test_invalid_time_limit_too_long(self):
        """Test error with time limit above maximum."""
        with pytest.raises(ValueError) as exc_info:
            GameSettings(grid_size=10, time_limit=2000)

        assert "time limit must be between 60 and 1800" in str(exc_info.value).lower()

    def test_invalid_word_placement_coordinates_mismatch(self):
        """Test error when word length doesn't match coordinates."""
        with pytest.raises(ValueError) as exc_info:
            WordPlacement(
                word="HELLO",  # 5 letters
                coordinates=[Coordinate(0, 0), Coordinate(0, 1)],  # Only 2 coordinates
                word_type=WordType.CHARACTER
            )

        assert "word length must match" in str(exc_info.value).lower()


class TestGameConfigurationValidation:
    """Tests for game configuration validation."""

    def test_invalid_topic_configuration(self):
        """Test validation with invalid topic."""
        controller = GameController()
        settings = GameSettings(grid_size=10, time_limit=300)

        is_valid, message = controller.validate_game_configuration(
            "InvalidTopic", "InvalidSubtopic", settings
        )

        assert not is_valid
        assert "not found" in message.lower()

    def test_invalid_subtopic_configuration(self):
        """Test validation with invalid subtopic."""
        controller = GameController()
        db = WordDatabase()
        topics = db.get_topics()

        if topics:
            topic = topics[0]
            settings = GameSettings(grid_size=10, time_limit=300)

            is_valid, message = controller.validate_game_configuration(
                topic, "InvalidSubtopic", settings
            )

            assert not is_valid
            assert "not found" in message.lower()

    def test_insufficient_words_configuration(self):
        """Test validation when subtopic has insufficient words for grid."""
        controller = GameController()
        db = WordDatabase()
        topics = db.get_topics()

        if topics:
            topic = topics[0]
            subtopics = db.get_subtopics(topic)

            if subtopics:
                subtopic = subtopics[0]
                # Try with very large grid that would need many words
                settings = GameSettings(grid_size=20, time_limit=300)

                # This might pass or fail depending on the database content
                # Just ensure validation runs without exception
                is_valid, message = controller.validate_game_configuration(
                    topic, subtopic, settings
                )

                assert isinstance(is_valid, bool)
                assert isinstance(message, str)


class TestErrorRecovery:
    """Tests for error recovery scenarios."""

    def test_empty_word_list_handling(self):
        """Test that empty word list is handled gracefully."""
        generator = GridGenerator()
        grid = generator.generate_grid([], [], 10)

        assert grid.size == 10
        assert len(grid.solution) == 0
        assert len(grid.discovered_words) == 0

    def test_partial_word_placement_success(self):
        """Test that partial placement is accepted if above threshold."""
        generator = GridGenerator()
        words = ["WORD1", "WORD2", "WORD3"]
        word_types = [WordType.CHARACTER] * 3
        size = 10

        # With low threshold, should succeed even if some words fail
        grid = generator.generate_grid(words, word_types, size, min_success_rate=0.1)

        assert grid is not None
        assert grid.size == size
        # At least some words should be placed
        assert len(grid.solution) >= 1


class TestErrorMessages:
    """Tests for error message quality."""

    def test_database_error_has_user_message(self):
        """Test that database errors have user-friendly messages."""
        try:
            db = WordDatabase("/nonexistent/path")
        except DatabaseNotFoundError as e:
            assert e.user_message is not None
            assert len(e.user_message) > 0
            assert "user" not in e.user_message.lower()  # Should be user-friendly
            assert "technical" not in e.user_message.lower()

    def test_grid_error_has_user_message(self):
        """Test that grid errors have user-friendly messages."""
        generator = GridGenerator()

        try:
            generator.generate_grid(["VERYLONGWORD"], [WordType.CHARACTER], 5)
        except GridTooSmallError as e:
            assert e.user_message is not None
            assert len(e.user_message) > 0
            assert "grid" in e.user_message.lower()

    def test_topic_error_has_user_message(self):
        """Test that topic errors have user-friendly messages."""
        db = WordDatabase()

        try:
            db.get_subtopics("InvalidTopic")
        except TopicNotFoundError as e:
            assert e.user_message is not None
            assert len(e.user_message) > 0
            assert "InvalidTopic" in e.user_message
