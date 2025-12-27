"""Property-based tests for topic-subtopic relationships.

**Feature: themed-word-search-game, Property 1: Topic-subtopic relationship consistency**
**Validates: Requirements 1.2, 1.3**
"""

import pytest
from hypothesis import given, strategies as st
from src.data import WordDatabase


class TestTopicSubtopicRelationships:
    """Property tests for topic-subtopic relationship consistency."""

    def setup_method(self):
        """Set up test database."""
        self.db = WordDatabase()

    @given(st.sampled_from(["anime", "movies", "shows"]))
    def test_topic_subtopic_relationship_consistency(self, topic: str):
        """
        Property 1: Topic-subtopic relationship consistency
        For any selected topic, all returned subtopics should belong to that 
        topic category and contain valid word data.
        
        **Feature: themed-word-search-game, Property 1: Topic-subtopic relationship consistency**
        **Validates: Requirements 1.2, 1.3**
        """
        # Get subtopics for the topic
        subtopics = self.db.get_subtopics(topic)
        
        # Verify subtopics exist and are non-empty
        assert isinstance(subtopics, list)
        assert len(subtopics) > 0
        
        # For each subtopic, verify it belongs to the topic and has valid data
        for subtopic in subtopics:
            # Should be able to get word data without error
            word_data = self.db.get_words(topic, subtopic)
            
            # Verify the word data belongs to the correct topic/subtopic
            assert word_data.topic == topic
            assert word_data.subtopic == subtopic
            
            # Verify word data has required structure
            assert isinstance(word_data.character_words, list)
            assert isinstance(word_data.defining_words, list)
            assert len(word_data.character_words) >= 5
            assert len(word_data.defining_words) >= 5

    def test_all_topics_available(self):
        """
        Verify all expected topics are available in the database.
        
        **Feature: themed-word-search-game, Property 1: Topic-subtopic relationship consistency**
        **Validates: Requirements 1.2**
        """
        topics = self.db.get_topics()
        expected_topics = {"anime", "movies", "shows"}
        
        assert isinstance(topics, list)
        assert set(topics) == expected_topics

    def test_invalid_topic_raises_error(self):
        """
        Verify that requesting subtopics for invalid topic raises appropriate error.

        **Feature: themed-word-search-game, Property 1: Topic-subtopic relationship consistency**
        **Validates: Requirements 1.2**
        """
        from src.exceptions import TopicNotFoundError
        with pytest.raises(TopicNotFoundError):
            self.db.get_subtopics("invalid_topic")

    @given(
        topic=st.sampled_from(["anime", "movies", "shows"]),
        invalid_subtopic=st.text(min_size=1).filter(
            lambda x: x not in ["naruto", "onepiece", "dragonball", "starwars", "marvel",
                               "harrypotter", "gameofthrones", "friends", "theoffice"]
        )
    )
    def test_invalid_subtopic_raises_error(self, topic: str, invalid_subtopic: str):
        """
        Verify that requesting words for invalid subtopic raises appropriate error.

        **Feature: themed-word-search-game, Property 1: Topic-subtopic relationship consistency**
        **Validates: Requirements 1.3**
        """
        from src.exceptions import SubtopicNotFoundError
        with pytest.raises(SubtopicNotFoundError):
            self.db.get_words(topic, invalid_subtopic)