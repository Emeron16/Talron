"""Word database management for the themed word search game."""

import json
import os
from typing import List, Dict, Optional, Set
from pathlib import Path

from ..models.core import WordData
from ..exceptions import (
    DatabaseNotFoundError,
    DatabaseCorruptedError,
    TopicNotFoundError,
    SubtopicNotFoundError,
    InsufficientWordsError
)


class WordDatabase:
    """Manages word data for topics and subtopics."""
    
    def __init__(self, data_file: Optional[str] = None):
        """Initialize the word database.
        
        Args:
            data_file: Path to the JSON data file. If None, uses default location.
        """
        if data_file is None:
            # Default to the JSON file in the same directory
            current_dir = Path(__file__).parent
            data_file = current_dir / "word_database.json"
        
        self.data_file = Path(data_file)
        self._data: Dict = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Load data from the JSON file.

        Raises:
            DatabaseNotFoundError: If the database file doesn't exist.
            DatabaseCorruptedError: If the database file is invalid.
        """
        try:
            if not self.data_file.exists():
                raise DatabaseNotFoundError(str(self.data_file))

            with open(self.data_file, 'r', encoding='utf-8') as f:
                self._data = json.load(f)

            # Validate basic structure
            if not isinstance(self._data, dict):
                raise DatabaseCorruptedError("Database must be a JSON object")

            # Validate each topic has valid structure
            for topic, subtopics in self._data.items():
                if not isinstance(subtopics, dict):
                    raise DatabaseCorruptedError(f"Topic '{topic}' must contain subtopics")

                for subtopic, data in subtopics.items():
                    if not isinstance(data, dict):
                        raise DatabaseCorruptedError(
                            f"Subtopic '{subtopic}' in '{topic}' must be an object"
                        )
                    if "character_words" not in data or "defining_words" not in data:
                        raise DatabaseCorruptedError(
                            f"Subtopic '{subtopic}' in '{topic}' missing required word lists"
                        )

        except FileNotFoundError:
            raise DatabaseNotFoundError(str(self.data_file))
        except json.JSONDecodeError as e:
            raise DatabaseCorruptedError(f"Invalid JSON format: {str(e)}")
        except (KeyError, TypeError) as e:
            raise DatabaseCorruptedError(f"Invalid database structure: {str(e)}")
    
    def get_topics(self) -> List[str]:
        """Get all available topics.
        
        Returns:
            List of topic names.
        """
        return list(self._data.keys())
    
    def get_subtopics(self, topic: str) -> List[str]:
        """Get all subtopics for a given topic.

        Args:
            topic: The topic name.

        Returns:
            List of subtopic names for the given topic.

        Raises:
            TopicNotFoundError: If topic is not found.
        """
        if topic not in self._data:
            raise TopicNotFoundError(topic)

        return list(self._data[topic].keys())
    
    def get_words(self, topic: str, subtopic: str) -> WordData:
        """Get word data for a specific topic and subtopic.

        Args:
            topic: The topic name.
            subtopic: The subtopic name.

        Returns:
            WordData object containing character and defining words.

        Raises:
            TopicNotFoundError: If topic is not found.
            SubtopicNotFoundError: If subtopic is not found.
        """
        if topic not in self._data:
            raise TopicNotFoundError(topic)

        if subtopic not in self._data[topic]:
            raise SubtopicNotFoundError(topic, subtopic)

        subtopic_data = self._data[topic][subtopic]

        try:
            return WordData(
                topic=topic,
                subtopic=subtopic,
                character_words=subtopic_data["character_words"],
                defining_words=subtopic_data["defining_words"]
            )
        except (KeyError, ValueError) as e:
            raise DatabaseCorruptedError(
                f"Invalid data for {topic}/{subtopic}: {str(e)}"
            )
    
    def validate_word_list(self, words: List[str]) -> bool:
        """Validate that a word list meets requirements.
        
        Args:
            words: List of words to validate.
            
        Returns:
            True if word list is valid, False otherwise.
        """
        if len(words) < 5:
            return False
        
        for word in words:
            if not isinstance(word, str):
                return False
            if len(word) < 3 or len(word) > 12:
                return False
            # Check for valid characters (letters only, spaces allowed)
            if not word.replace(" ", "").isalpha():
                return False
        
        return True
    
    def validate_subtopic_data(self, topic: str, subtopic: str) -> bool:
        """Validate that a subtopic has complete and valid data.
        
        Args:
            topic: The topic name.
            subtopic: The subtopic name.
            
        Returns:
            True if subtopic data is valid, False otherwise.
        """
        try:
            word_data = self.get_words(topic, subtopic)
            return (self.validate_word_list(word_data.character_words) and 
                   self.validate_word_list(word_data.defining_words))
        except (ValueError, KeyError):
            return False
    
    def get_all_words(self, topic: str, subtopic: str) -> List[str]:
        """Get all words (character + defining) for a subtopic.
        
        Args:
            topic: The topic name.
            subtopic: The subtopic name.
            
        Returns:
            Combined list of character and defining words.
        """
        word_data = self.get_words(topic, subtopic)
        return word_data.character_words + word_data.defining_words
    
    def has_sufficient_words(self, topic: str, subtopic: str, min_words: int = 10) -> bool:
        """Check if a subtopic has sufficient words for gameplay.
        
        Args:
            topic: The topic name.
            subtopic: The subtopic name.
            min_words: Minimum number of total words required.
            
        Returns:
            True if subtopic has sufficient words, False otherwise.
        """
        try:
            all_words = self.get_all_words(topic, subtopic)
            return len(all_words) >= min_words
        except ValueError:
            return False
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get statistics about the database.
        
        Returns:
            Dictionary with database statistics.
        """
        stats = {
            "total_topics": len(self._data),
            "total_subtopics": 0,
            "total_words": 0
        }
        
        for topic in self._data:
            stats["total_subtopics"] += len(self._data[topic])
            for subtopic in self._data[topic]:
                subtopic_data = self._data[topic][subtopic]
                stats["total_words"] += len(subtopic_data.get("character_words", []))
                stats["total_words"] += len(subtopic_data.get("defining_words", []))
        
        return stats