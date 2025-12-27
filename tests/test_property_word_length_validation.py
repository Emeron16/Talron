"""Property-based tests for word length validation.

**Feature: themed-word-search-game, Property 12: Word length validation**
**Validates: Requirements 6.3**
"""

import pytest
from hypothesis import given, strategies as st
from src.data import WordDatabase


class TestWordLengthValidation:
    """Property tests for word length validation."""

    def setup_method(self):
        """Set up test database."""
        self.db = WordDatabase()

    @given(
        topic=st.sampled_from(["anime", "movies", "shows"])
    )
    def test_word_length_validation(self, topic: str):
        """
        Property 12: Word length validation
        For any word retrieved from the database, the length should be 
        between 3 and 12 characters inclusive.
        
        **Feature: themed-word-search-game, Property 12: Word length validation**
        **Validates: Requirements 6.3**
        """
        subtopics = self.db.get_subtopics(topic)
        
        for subtopic in subtopics:
            word_data = self.db.get_words(topic, subtopic)
            
            # Test all character words
            for word in word_data.character_words:
                assert isinstance(word, str)
                assert 3 <= len(word) <= 12, f"Character word '{word}' in {topic}/{subtopic} has invalid length: {len(word)}"
            
            # Test all defining words
            for word in word_data.defining_words:
                assert isinstance(word, str)
                assert 3 <= len(word) <= 12, f"Defining word '{word}' in {topic}/{subtopic} has invalid length: {len(word)}"

    def test_all_database_words_have_valid_length(self):
        """
        Verify all words in the database have valid length.
        
        **Feature: themed-word-search-game, Property 12: Word length validation**
        **Validates: Requirements 6.3**
        """
        topics = self.db.get_topics()
        
        for topic in topics:
            subtopics = self.db.get_subtopics(topic)
            
            for subtopic in subtopics:
                all_words = self.db.get_all_words(topic, subtopic)
                
                for word in all_words:
                    assert 3 <= len(word) <= 12, f"Word '{word}' in {topic}/{subtopic} has invalid length: {len(word)}"

    @given(
        word_length=st.integers(min_value=3, max_value=12)
    )
    def test_valid_length_words_pass_validation(self, word_length: int):
        """
        Verify that words with valid lengths pass validation.
        
        **Feature: themed-word-search-game, Property 12: Word length validation**
        **Validates: Requirements 6.3**
        """
        # Generate a word of the specified length
        valid_word = "a" * word_length
        word_list = ["apple", "banana", "cherry", "date", valid_word]
        
        # Should pass validation
        assert self.db.validate_word_list(word_list)

    @given(
        word_length=st.one_of(
            st.integers(max_value=2),      # Too short
            st.integers(min_value=13)      # Too long
        )
    )
    def test_invalid_length_words_fail_validation(self, word_length: int):
        """
        Verify that words with invalid lengths fail validation.
        
        **Feature: themed-word-search-game, Property 12: Word length validation**
        **Validates: Requirements 6.3**
        """
        # Skip negative lengths and extremely long lengths for practical reasons
        if word_length < 0 or word_length > 50:
            return
            
        # Generate a word of the specified invalid length
        invalid_word = "a" * word_length
        word_list = ["apple", "banana", "cherry", "date", invalid_word]
        
        # Should fail validation
        assert not self.db.validate_word_list(word_list)

    def test_boundary_length_validation(self):
        """
        Test boundary cases for word length validation.
        
        **Feature: themed-word-search-game, Property 12: Word length validation**
        **Validates: Requirements 6.3**
        """
        # Test minimum valid length (3 characters)
        min_valid_list = ["apple", "banana", "cherry", "date", "cat"]  # "cat" is 3 chars
        assert self.db.validate_word_list(min_valid_list)
        
        # Test maximum valid length (12 characters)
        max_valid_list = ["apple", "banana", "cherry", "date", "abcdefghijkl"]  # 12 chars
        assert self.db.validate_word_list(max_valid_list)
        
        # Test just below minimum (2 characters)
        too_short_list = ["apple", "banana", "cherry", "date", "ab"]  # "ab" is 2 chars
        assert not self.db.validate_word_list(too_short_list)
        
        # Test just above maximum (13 characters)
        too_long_list = ["apple", "banana", "cherry", "date", "abcdefghijklm"]  # 13 chars
        assert not self.db.validate_word_list(too_long_list)

    def test_word_data_validation_enforces_length(self):
        """
        Verify that WordData validation enforces word length requirements.
        
        **Feature: themed-word-search-game, Property 12: Word length validation**
        **Validates: Requirements 6.3**
        """
        from src.models.core import WordData
        
        # Valid word data should work
        valid_character_words = ["luke", "vader", "leia", "han", "solo"]
        valid_defining_words = ["force", "jedi", "sith", "empire", "rebel"]
        
        word_data = WordData(
            topic="movies",
            subtopic="starwars",
            character_words=valid_character_words,
            defining_words=valid_defining_words
        )
        
        # Should not raise an exception
        assert word_data.topic == "movies"
        
        # Invalid word data with too short word should fail
        with pytest.raises(ValueError, match="must be between 3 and 12 characters"):
            WordData(
                topic="movies",
                subtopic="test",
                character_words=["luke", "vader", "leia", "han", "ab"],  # "ab" is too short
                defining_words=valid_defining_words
            )
        
        # Invalid word data with too long word should fail
        with pytest.raises(ValueError, match="must be between 3 and 12 characters"):
            WordData(
                topic="movies",
                subtopic="test",
                character_words=valid_character_words,
                defining_words=["force", "jedi", "sith", "empire", "verylongwordname"]  # too long
            )