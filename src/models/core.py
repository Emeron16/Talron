"""Core data models for the themed word search game."""

from dataclasses import dataclass
from typing import List, Set, Optional, Literal
from datetime import datetime
from enum import Enum


class GameStatus(Enum):
    """Game status enumeration."""
    SETUP = "setup"
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class WordType(Enum):
    """Word type enumeration."""
    CHARACTER = "character"
    DEFINING = "defining"


@dataclass
class Coordinate:
    """Represents a coordinate position in the grid."""
    row: int
    col: int

    def __post_init__(self):
        if self.row < 0 or self.col < 0:
            raise ValueError("Coordinates must be non-negative")


@dataclass
class WordPlacement:
    """Represents a word placed in the grid with its coordinates."""
    word: str
    coordinates: List[Coordinate]
    word_type: WordType

    def __post_init__(self):
        if not self.word:
            raise ValueError("Word cannot be empty")
        if not self.coordinates:
            raise ValueError("Coordinates cannot be empty")
        if len(self.word) != len(self.coordinates):
            raise ValueError("Word length must match coordinates length")


@dataclass
class Grid:
    """Represents the game grid with letters and solution."""
    size: int
    letters: List[List[str]]
    solution: List[WordPlacement]
    discovered_words: Set[str]

    def __post_init__(self):
        if self.size < 8 or self.size > 20:
            raise ValueError("Grid size must be between 8 and 20")
        if len(self.letters) != self.size:
            raise ValueError("Letters grid must match size")
        for row in self.letters:
            if len(row) != self.size:
                raise ValueError("All rows must have the same length as size")


@dataclass
class Game:
    """Represents a game session."""
    id: str
    topic: str
    subtopic: str
    grid_size: int
    time_limit: int  # 0 means no time limit
    max_words: int
    start_time: datetime
    status: GameStatus

    def __post_init__(self):
        if self.grid_size < 8 or self.grid_size > 20:
            raise ValueError("Grid size must be between 8 and 20")
        # Allow 0 for no time limit, or between 60 and 1800 for timed games
        if self.time_limit != 0 and (self.time_limit < 60 or self.time_limit > 1800):
            raise ValueError("Time limit must be 0 (no limit) or between 60 and 1800 seconds")
        if self.max_words < 1:
            raise ValueError("Max words must be at least 1")


@dataclass
class WordData:
    """Represents word data for a specific topic and subtopic."""
    topic: str
    subtopic: str
    character_words: List[str]
    defining_words: List[str]

    def __post_init__(self):
        if not self.topic or not self.subtopic:
            raise ValueError("Topic and subtopic cannot be empty")
        if len(self.character_words) < 5:
            raise ValueError("Must have at least 5 character words")
        if len(self.defining_words) < 5:
            raise ValueError("Must have at least 5 defining words")
        
        # Validate word lengths (3-12 characters)
        all_words = self.character_words + self.defining_words
        for word in all_words:
            if len(word) < 3 or len(word) > 12:
                raise ValueError(f"Word '{word}' must be between 3 and 12 characters")


@dataclass
class GameSettings:
    """Represents game configuration settings."""
    grid_size: int
    time_limit: int  # 0 means no time limit

    def __post_init__(self):
        if self.grid_size < 8 or self.grid_size > 20:
            raise ValueError("Grid size must be between 8 and 20")
        # Allow 0 for no time limit, or between 60 and 1800 for timed games
        if self.time_limit != 0 and (self.time_limit < 60 or self.time_limit > 1800):
            raise ValueError("Time limit must be 0 (no limit) or between 60 and 1800 seconds")