"""Property-based tests for database validation constraints.

**Feature: themed-word-search-game, Property 13: Database validation constraints**
**Validates: Requirements 6.5**
"""

import pytest
from hypothesis import given, strategies as st
from src.data import WordDatabase
from src.models.core import WordData


class TestDatabaseValidationConstraints:
    """Property tests for database validation constraints."""

    def setup_method(self):
        """Set up test database."""
        self.db = WordDatabase()

    @given(
        topic=st.sampled_from(["anime", "movies", "shows"])
    )
    def test_database_validation_constraints(self, topic: str):
        """
        Property 13: Database validation constraints
        For any new subtopic data, the word lists should meet minimum 
        requirements before being accepted into the database.
        
        **Feature: themed-word-search-game, Property 13: Database validation constraints**
        **Validates: Requirements 6.5**
        """
        subtopics = self.db.get_subtopics(topic)
        
        for subtopic in subtopics:
            # All existing subtopics should pass validation
            assert self.db.validate_subtopic_data(topic, subtopic), f"Subtopic {topic}/{subtopic} fails validation"
            
            # Get the word data and verify it meets constraints
            word_data = self.db.get_words(topic, subtopic)
            
            # Verify minimum word counts
            assert len(word_data.character_words) >= 5, f"Insufficient character words in {topic}/{subtopic}"
            assert len(word_data.defining_words) >= 5, f"Insufficient defining words in {topic}/{subtopic}"
            
            # Verify individual word list validation
            assert self.db.validate_word_list(word_data.character_words), f"Character words fail validation in {topic}/{subtopic}"
            assert self.db.validate_word_list(word_data.defining_words), f"Defining words fail validation in {topic}/{subtopic}"

    def test_all_database_entries_meet_validation_constraints(self):
        """
        Verify all entries in the database meet validation constraints.
        
        **Feature: themed-word-search-game, Property 13: Database validation constraints**
        **Validates: Requirements 6.5**
        """
        topics = self.db.get_topics()
        
        for topic in topics:
            subtopics = self.db.get_subtopics(topic)
            
            for subtopic in subtopics:
                # Each subtopic should pass all validation constraints
                assert self.db.validate_subtopic_data(topic, subtopic)
                assert self.db.has_sufficient_words(topic, subtopic, min_words=10)
                
                # Verify WordData can be created without errors (enforces constraints)
                word_data = self.db.get_words(topic, subtopic)
                assert isinstance(word_data, WordData)

    @given(
        character_word_count=st.integers(min_value=5, max_value=15),
        defining_word_count=st.integers(min_value=5, max_value=15)
    )
    def test_valid_word_data_meets_constraints(self, character_word_count: int, defining_word_count: int):
        """
        Verify that valid word data meets all database constraints.
        
        **Feature: themed-word-search-game, Property 13: Database validation constraints**
        **Validates: Requirements 6.5**
        """
        # Generate valid character words (using alphabetic base words)
        base_char_words = ["hero", "villain", "warrior", "mage", "knight", "archer", "rogue", "paladin", "wizard", "fighter", "ranger", "bard", "cleric", "druid", "monk"]
        character_words = base_char_words[:character_word_count]
        
        # Generate valid defining words
        base_def_words = ["sword", "magic", "battle", "quest", "castle", "dragon", "treasure", "kingdom", "forest", "mountain", "river", "ocean", "fire", "water", "earth"]
        defining_words = base_def_words[:defining_word_count]
        
        # Both lists should pass validation
        assert self.db.validate_word_list(character_words)
        assert self.db.validate_word_list(defining_words)
        
        # WordData should be creatable without errors
        word_data = WordData(
            topic="test",
            subtopic="test",
            character_words=character_words,
            defining_words=defining_words
        )
        
        assert len(word_data.character_words) == character_word_count
        assert len(word_data.defining_words) == defining_word_count

    def test_insufficient_word_data_fails_constraints(self):
        """
        Verify that insufficient word data fails validation constraints.
        
        **Feature: themed-word-search-game, Property 13: Database validation constraints**
        **Validates: Requirements 6.5**
        """
        # Test insufficient character words
        with pytest.raises(ValueError, match="Must have at least 5 character words"):
            WordData(
                topic="test",
                subtopic="test",
                character_words=["apple", "banana", "cherry", "date"],  # Only 4 words
                defining_words=["sword", "magic", "battle", "quest", "castle"]
            )
        
        # Test insufficient defining words
        with pytest.raises(ValueError, match="Must have at least 5 defining words"):
            WordData(
                topic="test",
                subtopic="test",
                character_words=["apple", "banana", "cherry", "date", "elderberry"],
                defining_words=["sword", "magic", "battle", "quest"]  # Only 4 words
            )

    def test_word_list_validation_constraints(self):
        """
        Test specific word list validation constraints.
        
        **Feature: themed-word-search-game, Property 13: Database validation constraints**
        **Validates: Requirements 6.5**
        """
        # Valid word list should pass
        valid_words = ["apple", "banana", "cherry", "date", "elderberry"]
        assert self.db.validate_word_list(valid_words)
        
        # Too few words should fail
        insufficient_words = ["apple", "banana", "cherry", "date"]
        assert not self.db.validate_word_list(insufficient_words)
        
        # Words with invalid characters should fail
        invalid_chars = ["apple", "banana", "cherry", "date", "word!"]
        assert not self.db.validate_word_list(invalid_chars)
        
        # Words with numbers should fail
        with_numbers = ["apple", "banana", "cherry", "date", "word1"]
        assert not self.db.validate_word_list(with_numbers)
        
        # Words too short should fail
        too_short = ["apple", "banana", "cherry", "date", "ab"]
        assert not self.db.validate_word_list(too_short)
        
        # Words too long should fail
        too_long = ["apple", "banana", "cherry", "date", "verylongwordname"]
        assert not self.db.validate_word_list(too_long)
        
        # Non-string items should fail
        non_strings = ["apple", "banana", "cherry", "date", 123]
        assert not self.db.validate_word_list(non_strings)

    def test_database_stats_reflect_constraints(self):
        """
        Verify database statistics reflect that all entries meet constraints.
        
        **Feature: themed-word-search-game, Property 13: Database validation constraints**
        **Validates: Requirements 6.5**
        """
        stats = self.db.get_database_stats()
        
        # Should have expected structure
        assert "total_topics" in stats
        assert "total_subtopics" in stats
        assert "total_words" in stats
        
        # Should have reasonable values
        assert stats["total_topics"] >= 3  # anime, movies, shows
        assert stats["total_subtopics"] >= 9  # At least 3 per topic
        assert stats["total_words"] >= 180  # At least 10 words per subtopic * 9 subtopics
        
        # Verify each topic has valid subtopics
        topics = self.db.get_topics()
        assert len(topics) == stats["total_topics"]
        
        total_subtopics = 0
        for topic in topics:
            subtopics = self.db.get_subtopics(topic)
            total_subtopics += len(subtopics)
            
            # Each subtopic should meet constraints
            for subtopic in subtopics:
                assert self.db.validate_subtopic_data(topic, subtopic)
        
        assert total_subtopics == stats["total_subtopics"]