"""Property-based tests for word list completeness.

**Feature: themed-word-search-game, Property 2: Word list completeness**
**Validates: Requirements 1.4, 6.1, 6.2**
"""

import pytest
from hypothesis import given, strategies as st
from src.data import WordDatabase


class TestWordListCompleteness:
    """Property tests for word list completeness."""

    def setup_method(self):
        """Set up test database."""
        self.db = WordDatabase()

    @given(
        topic=st.sampled_from(["anime", "movies", "shows"])
    )
    def test_word_list_completeness(self, topic: str):
        """
        Property 2: Word list completeness
        For any retrieved subtopic, the word list should contain both character 
        words and defining words with minimum counts.
        
        **Feature: themed-word-search-game, Property 2: Word list completeness**
        **Validates: Requirements 1.4, 6.1, 6.2**
        """
        subtopics = self.db.get_subtopics(topic)
        
        for subtopic in subtopics:
            word_data = self.db.get_words(topic, subtopic)
            
            # Verify both character and defining words are present
            assert isinstance(word_data.character_words, list)
            assert isinstance(word_data.defining_words, list)
            
            # Verify minimum word counts (Requirements 6.1, 6.2)
            assert len(word_data.character_words) >= 5, f"Topic {topic}, subtopic {subtopic} has insufficient character words"
            assert len(word_data.defining_words) >= 5, f"Topic {topic}, subtopic {subtopic} has insufficient defining words"
            
            # Verify words are non-empty strings
            for word in word_data.character_words:
                assert isinstance(word, str)
                assert len(word) > 0
            
            for word in word_data.defining_words:
                assert isinstance(word, str)
                assert len(word) > 0
            
            # Verify combined word list meets requirements (Requirement 1.4)
            all_words = word_data.character_words + word_data.defining_words
            assert len(all_words) >= 10, f"Topic {topic}, subtopic {subtopic} has insufficient total words"

    def test_all_subtopics_have_complete_word_lists(self):
        """
        Verify all subtopics in the database have complete word lists.
        
        **Feature: themed-word-search-game, Property 2: Word list completeness**
        **Validates: Requirements 1.4, 6.1, 6.2**
        """
        topics = self.db.get_topics()
        
        for topic in topics:
            subtopics = self.db.get_subtopics(topic)
            
            for subtopic in subtopics:
                # Should be able to get valid word data
                word_data = self.db.get_words(topic, subtopic)
                
                # Verify completeness
                assert len(word_data.character_words) >= 5
                assert len(word_data.defining_words) >= 5
                
                # Verify validation passes
                assert self.db.validate_subtopic_data(topic, subtopic)
                assert self.db.has_sufficient_words(topic, subtopic)

    @given(
        topic=st.sampled_from(["anime", "movies", "shows"])
    )
    def test_word_list_validation_methods(self, topic: str):
        """
        Verify word list validation methods work correctly.
        
        **Feature: themed-word-search-game, Property 2: Word list completeness**
        **Validates: Requirements 6.1, 6.2**
        """
        subtopics = self.db.get_subtopics(topic)
        
        for subtopic in subtopics:
            word_data = self.db.get_words(topic, subtopic)
            
            # Test individual word list validation
            assert self.db.validate_word_list(word_data.character_words)
            assert self.db.validate_word_list(word_data.defining_words)
            
            # Test combined validation
            assert self.db.validate_subtopic_data(topic, subtopic)
            
            # Test sufficient words check
            assert self.db.has_sufficient_words(topic, subtopic, min_words=10)
            
            # Test get_all_words method
            all_words = self.db.get_all_words(topic, subtopic)
            expected_total = len(word_data.character_words) + len(word_data.defining_words)
            assert len(all_words) == expected_total

    def test_word_list_validation_edge_cases(self):
        """
        Test word list validation with edge cases.
        
        **Feature: themed-word-search-game, Property 2: Word list completeness**
        **Validates: Requirements 6.1, 6.2**
        """
        # Test empty list
        assert not self.db.validate_word_list([])
        
        # Test insufficient words
        assert not self.db.validate_word_list(["apple", "banana", "cherry", "date"])  # Only 4 words
        
        # Test valid minimum list
        assert self.db.validate_word_list(["apple", "banana", "cherry", "date", "elderberry"])  # Exactly 5 words
        
        # Test non-string items
        assert not self.db.validate_word_list(["apple", "banana", "cherry", "date", 123])
        
        # Test words with numbers (should fail)
        assert not self.db.validate_word_list(["apple", "banana", "cherry", "date", "word1"])
        
        # Test words too short
        assert not self.db.validate_word_list(["apple", "banana", "cherry", "date", "ab"])
        
        # Test words too long
        assert not self.db.validate_word_list(["apple", "banana", "cherry", "date", "verylongwordname"])
        
        # Test words with special characters
        assert not self.db.validate_word_list(["apple", "banana", "cherry", "date", "word!"])
        
        # Test words with spaces (should pass)
        assert self.db.validate_word_list(["apple", "banana", "cherry", "date", "ice cream"])
        
        # Words with invalid length (tested in separate property test)
        # This is covered by the WordData validation in core.py