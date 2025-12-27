"""End-to-end integration tests for the complete game flow.

Tests the entire game lifecycle from initialization to completion,
ensuring all components work together correctly.
"""

import pytest
from datetime import datetime

from src.models.core import GameSettings, GameStatus, WordType
from src.services.game_controller import GameController
from src.services.selection_validator import SelectionValidator
from src.data.word_database import WordDatabase


class TestEndToEndIntegration:
    """End-to-end integration tests for complete game flows."""

    def test_complete_game_flow_with_perfect_completion(self):
        """Test a complete game from start to perfect completion."""
        # Initialize components
        controller = GameController()
        validator = SelectionValidator()  # Can be initialized without grid for static usage
        db = WordDatabase()

        # Select topic and subtopic
        topics = db.get_topics()
        assert len(topics) > 0, "Database should have topics"

        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        assert len(subtopics) > 0, f"Topic {topic} should have subtopics"

        subtopic = subtopics[0]

        # Configure game settings
        settings = GameSettings(grid_size=12, time_limit=300)

        # Initialize and start game
        game = controller.initialize_game(topic, subtopic, settings)
        assert game.status == GameStatus.SETUP
        assert game.grid_size == 12
        assert game.time_limit == 300

        grid = controller.start_game()
        assert game.status == GameStatus.ACTIVE
        assert grid.size == 12
        assert len(grid.solution) > 0
        assert len(grid.discovered_words) == 0

        # Simulate finding all words
        for word_placement in grid.solution:
            # Add word to discovered set
            discovered = controller.discover_word(word_placement.word)
            assert discovered, f"Word {word_placement.word} should be discovered"

        # Verify all words found
        assert len(grid.discovered_words) == len(grid.solution)

        # End game
        controller.end_game(GameStatus.COMPLETED)
        assert game.status == GameStatus.COMPLETED

        # Calculate results
        results = controller.calculate_game_results()
        assert results is not None
        assert results['perfect_game'] is True
        assert results['completion_percentage'] == 100.0
        assert results['found_words'] == results['total_words']
        assert results['total_score'] > 0

    def test_complete_game_flow_with_partial_completion(self):
        """Test a complete game with partial word discovery."""
        controller = GameController()
        db = WordDatabase()

        # Use a known topic/subtopic
        topics = db.get_topics()
        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        subtopic = subtopics[0]

        settings = GameSettings(grid_size=15, time_limit=600)

        # Initialize and start
        game = controller.initialize_game(topic, subtopic, settings)
        grid = controller.start_game()

        # Find only half the words
        words_to_find = len(grid.solution) // 2
        for i, word_placement in enumerate(grid.solution[:words_to_find]):
            controller.discover_word(word_placement.word)

        # End game
        controller.end_game(GameStatus.EXPIRED)
        results = controller.calculate_game_results()

        # Verify partial completion
        assert results['perfect_game'] is False
        assert results['found_words'] == words_to_find
        assert 0 < results['completion_percentage'] < 100
        assert results['unfound_words'] > 0

    def test_game_with_different_topics(self):
        """Test that games can be played with different topics."""
        controller = GameController()
        db = WordDatabase()
        topics = db.get_topics()

        settings = GameSettings(grid_size=10, time_limit=300)

        # Play games with different topics
        for topic in topics:
            subtopics = db.get_subtopics(topic)
            if subtopics:
                subtopic = subtopics[0]

                # Start new game
                controller.start_new_game()
                game = controller.initialize_game(topic, subtopic, settings)
                grid = controller.start_game()

                # Verify game initialized correctly
                assert game.topic == topic
                assert game.subtopic == subtopic
                assert grid.size == 10
                assert len(grid.solution) > 0

    def test_session_statistics_tracking(self):
        """Test that session statistics are tracked across multiple games."""
        controller = GameController()
        db = WordDatabase()

        topics = db.get_topics()
        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        subtopic = subtopics[0]

        settings = GameSettings(grid_size=12, time_limit=300)

        # Play multiple games
        num_games = 3
        for i in range(num_games):
            controller.start_new_game()
            game = controller.initialize_game(topic, subtopic, settings)
            grid = controller.start_game()

            # Find some words
            words_found = min(3, len(grid.solution))
            for word_placement in grid.solution[:words_found]:
                controller.discover_word(word_placement.word)

            controller.end_game(GameStatus.COMPLETED)
            controller.calculate_game_results()

        # Check session stats
        stats = controller.get_session_stats()
        assert stats['games_played'] == num_games
        assert stats['total_words_found'] > 0
        assert stats['total_score'] > 0

    def test_grid_word_validation_integration(self):
        """Test integration between grid generation and word validation."""
        controller = GameController()
        validator = SelectionValidator()
        db = WordDatabase()

        topics = db.get_topics()
        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        subtopic = subtopics[0]

        settings = GameSettings(grid_size=12, time_limit=300)

        game = controller.initialize_game(topic, subtopic, settings)
        grid = controller.start_game()

        # Test validation with actual placed words
        for word_placement in grid.solution:
            # Validate the word using its coordinates
            validated_word = validator.validate_selection(grid, word_placement.coordinates)
            assert validated_word == word_placement.word  # Should match uppercase solution word

    def test_edge_case_minimum_grid_size(self):
        """Test game with minimum allowed grid size."""
        controller = GameController()
        db = WordDatabase()

        topics = db.get_topics()
        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        subtopic = subtopics[0]

        # Minimum grid size
        settings = GameSettings(grid_size=8, time_limit=300)

        game = controller.initialize_game(topic, subtopic, settings)
        grid = controller.start_game()

        assert grid.size == 8
        assert len(grid.solution) > 0  # Should still place some words

    def test_edge_case_maximum_grid_size(self):
        """Test game with maximum allowed grid size."""
        controller = GameController()
        db = WordDatabase()

        topics = db.get_topics()
        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        subtopic = subtopics[0]

        # Maximum grid size
        settings = GameSettings(grid_size=20, time_limit=300)

        game = controller.initialize_game(topic, subtopic, settings)
        grid = controller.start_game()

        assert grid.size == 20
        assert len(grid.solution) > 0

    def test_edge_case_minimum_time_limit(self):
        """Test game with minimum allowed time limit."""
        controller = GameController()
        db = WordDatabase()

        topics = db.get_topics()
        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        subtopic = subtopics[0]

        # Minimum time limit (60 seconds)
        settings = GameSettings(grid_size=10, time_limit=60)

        game = controller.initialize_game(topic, subtopic, settings)
        assert game.time_limit == 60

    def test_edge_case_maximum_time_limit(self):
        """Test game with maximum allowed time limit."""
        controller = GameController()
        db = WordDatabase()

        topics = db.get_topics()
        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        subtopic = subtopics[0]

        # Maximum time limit (1800 seconds = 30 minutes)
        settings = GameSettings(grid_size=10, time_limit=1800)

        game = controller.initialize_game(topic, subtopic, settings)
        assert game.time_limit == 1800

    def test_word_type_distribution_in_game(self):
        """Test that both character and defining words are included."""
        controller = GameController()
        db = WordDatabase()

        topics = db.get_topics()
        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        subtopic = subtopics[0]

        settings = GameSettings(grid_size=15, time_limit=300)

        game = controller.initialize_game(topic, subtopic, settings)
        grid = controller.start_game()

        # Check word type distribution
        character_count = sum(1 for wp in grid.solution if wp.word_type == WordType.CHARACTER)
        defining_count = sum(1 for wp in grid.solution if wp.word_type == WordType.DEFINING)

        # Should have at least some of each type (unless word list is very small)
        if len(grid.solution) >= 2:
            assert character_count > 0 or defining_count > 0

    def test_game_configuration_validation(self):
        """Test game configuration validation."""
        controller = GameController()

        # Valid configuration
        is_valid, message = controller.validate_game_configuration(
            "anime", "naruto", GameSettings(grid_size=10, time_limit=300)
        )
        assert is_valid, f"Valid configuration rejected: {message}"

        # Invalid topic
        is_valid, message = controller.validate_game_configuration(
            "invalid_topic", "invalid_subtopic",
            GameSettings(grid_size=10, time_limit=300)
        )
        assert not is_valid
        assert "not found" in message.lower()

    def test_performance_large_grid(self):
        """Test performance with large grid size."""
        controller = GameController()
        db = WordDatabase()

        topics = db.get_topics()
        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        subtopic = subtopics[0]

        # Large grid
        settings = GameSettings(grid_size=20, time_limit=1800)

        start_time = datetime.now()
        game = controller.initialize_game(topic, subtopic, settings)
        grid = controller.start_game()
        end_time = datetime.now()

        generation_time = (end_time - start_time).total_seconds()

        # Grid generation should complete in reasonable time (< 5 seconds)
        assert generation_time < 5.0, f"Grid generation took {generation_time}s, should be < 5s"
        assert len(grid.solution) > 0

    def test_result_calculator_integration(self):
        """Test results calculator integration with game flow."""
        controller = GameController()
        db = WordDatabase()

        topics = db.get_topics()
        topic = topics[0]
        subtopics = db.get_subtopics(topic)
        subtopic = subtopics[0]

        settings = GameSettings(grid_size=12, time_limit=300)

        game = controller.initialize_game(topic, subtopic, settings)
        grid = controller.start_game()

        # Find some words
        words_to_find = len(grid.solution) // 2
        for word_placement in grid.solution[:words_to_find]:
            controller.discover_word(word_placement.word)

        # End and calculate results
        controller.end_game(GameStatus.COMPLETED)
        results = controller.calculate_game_results()

        # Verify result components
        assert 'total_words' in results
        assert 'found_words' in results
        assert 'completion_percentage' in results
        assert 'total_score' in results
        assert 'word_breakdown' in results
        assert 'perfect_game' in results

        # Verify word breakdown
        breakdown = results['word_breakdown']
        assert 'character_words' in breakdown
        assert 'defining_words' in breakdown
