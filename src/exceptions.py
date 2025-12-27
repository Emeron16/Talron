"""Custom exceptions for the themed word search game."""


class WordSearchError(Exception):
    """Base exception for all word search game errors."""

    def __init__(self, message: str, user_message: str = None):
        """Initialize the exception.

        Args:
            message: Technical error message for logging.
            user_message: User-friendly message to display. If None, uses message.
        """
        super().__init__(message)
        self.user_message = user_message or message


class DatabaseError(WordSearchError):
    """Raised when database operations fail."""
    pass


class DatabaseNotFoundError(DatabaseError):
    """Raised when the word database file is not found."""

    def __init__(self, file_path: str):
        super().__init__(
            f"Word database file not found: {file_path}",
            "Unable to load word database. Please ensure the game is properly installed."
        )
        self.file_path = file_path


class DatabaseCorruptedError(DatabaseError):
    """Raised when the database file is corrupted or invalid."""

    def __init__(self, details: str):
        super().__init__(
            f"Database file is corrupted: {details}",
            "The word database is corrupted. Please reinstall the game."
        )


class TopicNotFoundError(DatabaseError):
    """Raised when a topic is not found in the database."""

    def __init__(self, topic: str):
        super().__init__(
            f"Topic '{topic}' not found in database",
            f"The topic '{topic}' is not available. Please select a different topic."
        )
        self.topic = topic


class SubtopicNotFoundError(DatabaseError):
    """Raised when a subtopic is not found in the database."""

    def __init__(self, topic: str, subtopic: str):
        super().__init__(
            f"Subtopic '{subtopic}' not found in topic '{topic}'",
            f"The subtopic '{subtopic}' is not available. Please select a different subtopic."
        )
        self.topic = topic
        self.subtopic = subtopic


class InsufficientWordsError(DatabaseError):
    """Raised when a subtopic doesn't have enough words for gameplay."""

    def __init__(self, topic: str, subtopic: str, word_count: int, min_required: int):
        super().__init__(
            f"Subtopic '{subtopic}' has only {word_count} words, need {min_required}",
            f"The selected content doesn't have enough words for this game size. "
            f"Please choose a different topic or reduce the grid size."
        )
        self.topic = topic
        self.subtopic = subtopic
        self.word_count = word_count
        self.min_required = min_required


class GridGenerationError(WordSearchError):
    """Raised when grid generation fails."""
    pass


class WordPlacementError(GridGenerationError):
    """Raised when words cannot be placed in the grid."""

    def __init__(self, failed_words: int, total_words: int):
        super().__init__(
            f"Failed to place {failed_words} out of {total_words} words in grid",
            "Unable to create a valid game board. The grid is too small for all the words.\n\n"
            "Please increase the grid size settings or choose a different topic."
        )
        self.failed_words = failed_words
        self.total_words = total_words


class GridTooSmallError(GridGenerationError):
    """Raised when the grid is too small for the word list."""

    def __init__(self, grid_size: int, word_count: int):
        super().__init__(
            f"Grid size {grid_size}x{grid_size} is too small for {word_count} words",
            f"The {grid_size}x{grid_size} grid is too small for the selected content. "
            f"Please choose a larger grid size."
        )
        self.grid_size = grid_size
        self.word_count = word_count


class GameStateError(WordSearchError):
    """Raised when an invalid game state operation is attempted."""
    pass


class NoActiveGameError(GameStateError):
    """Raised when trying to perform an operation without an active game."""

    def __init__(self, operation: str):
        super().__init__(
            f"Cannot {operation}: no active game",
            "There is no active game. Please start a new game first."
        )
        self.operation = operation


class InvalidGameStatusError(GameStateError):
    """Raised when trying to perform an operation in the wrong game status."""

    def __init__(self, operation: str, current_status: str, required_status: str):
        super().__init__(
            f"Cannot {operation} in status {current_status}, requires {required_status}",
            f"This operation cannot be performed right now. The game must be {required_status}."
        )
        self.operation = operation
        self.current_status = current_status
        self.required_status = required_status


class ValidationError(WordSearchError):
    """Raised when validation fails."""
    pass


class InvalidSettingsError(ValidationError):
    """Raised when game settings are invalid."""

    def __init__(self, field: str, value: any, reason: str):
        super().__init__(
            f"Invalid {field}: {value} - {reason}",
            f"Invalid {field}: {reason}"
        )
        self.field = field
        self.value = value
        self.reason = reason


class InvalidSelectionError(ValidationError):
    """Raised when a player selection is invalid."""

    def __init__(self, reason: str):
        super().__init__(
            f"Invalid selection: {reason}",
            reason
        )


class TimerError(WordSearchError):
    """Raised when timer operations fail."""
    pass


class TimerNotStartedError(TimerError):
    """Raised when trying to access timer that hasn't been started."""

    def __init__(self):
        super().__init__(
            "Timer has not been started",
            "The game timer is not running."
        )


class UIError(WordSearchError):
    """Raised when UI operations fail."""
    pass


class InputError(UIError):
    """Raised when user input is invalid or cannot be processed."""

    def __init__(self, expected: str, received: str = None):
        message = f"Expected {expected}"
        if received:
            message += f", got: {received}"
        super().__init__(
            message,
            f"Invalid input. {expected}"
        )
        self.expected = expected
        self.received = received
