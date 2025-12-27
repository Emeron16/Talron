"""Game controller for managing game state and logic."""

import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Callable, Dict, Any
from ..models.core import Game, GameStatus, GameSettings, WordData, Grid, WordType
from ..data.word_database import WordDatabase
from ..services.grid_generator import GridGenerator
from ..services.timer_manager import TimerManager, ProgressTracker
from ..services.results_calculator import ResultsCalculator


class GameController:
    """Manages game state, initialization, and word capacity calculations."""
    
    def __init__(self, word_database: Optional[WordDatabase] = None,
                 grid_generator: Optional[GridGenerator] = None):
        """Initialize the game controller.

        Args:
            word_database: Word database instance. If None, creates a new one.
            grid_generator: Grid generator instance. If None, creates a new one.
        """
        self.word_database = word_database or WordDatabase()
        self.grid_generator = grid_generator or GridGenerator()
        self.current_game: Optional[Game] = None
        self.current_grid: Optional[Grid] = None
        self.timer_manager = TimerManager()
        self.progress_tracker = ProgressTracker()
        self.results_calculator = ResultsCalculator()
        self.game_results: Optional[Dict[str, Any]] = None
        self.session_results: List[Dict[str, Any]] = []

        # Set up timer callbacks
        self.timer_manager.set_completion_callback(self._on_game_completion)
        self.progress_tracker.set_progress_callback(self._on_progress_update)
        self.progress_tracker.set_word_found_callback(self._on_word_found)
    
    def calculate_word_capacity(self, grid_size: int, word_list: List[str]) -> int:
        """
        Calculate the maximum number of words that can fit in a grid.
        
        This method determines how many words from the given list can theoretically
        be placed in a grid of the specified size, accounting for placement constraints
        and overlap possibilities.
        
        Args:
            grid_size: Size of the N×N grid
            word_list: List of words to potentially place
            
        Returns:
            Maximum number of words that can fit in the grid
            
        Raises:
            ValueError: If grid_size is invalid or word_list is empty
        """
        if grid_size < 8 or grid_size > 20:
            raise ValueError("Grid size must be between 8 and 20")
        
        if not word_list:
            return 0
        
        # Get word lengths for capacity calculation
        word_lengths = [len(word) for word in word_list]
        
        # Use grid generator's capacity calculation
        return self.grid_generator.calculate_word_capacity(grid_size, word_lengths)
    
    def adjust_word_count_for_grid(self, word_list: List[str], grid_size: int) -> List[str]:
        """
        Automatically adjust word count to fit grid constraints.
        
        Args:
            word_list: Original list of words
            grid_size: Size of the N×N grid
            
        Returns:
            Adjusted word list that can fit in the grid
        """
        max_capacity = self.calculate_word_capacity(grid_size, word_list)
        
        if len(word_list) <= max_capacity:
            return word_list
        
        # Sort by length (shorter words first for better placement success)
        sorted_words = sorted(word_list, key=len)
        return sorted_words[:max_capacity]
    
    def initialize_game(self, topic: str, subtopic: str, settings: GameSettings) -> Game:
        """
        Initialize a new game with the given parameters.
        
        Args:
            topic: Selected topic
            subtopic: Selected subtopic
            settings: Game configuration settings
            
        Returns:
            Initialized Game object
            
        Raises:
            ValueError: If topic/subtopic not found or insufficient words
        """
        # Validate topic and subtopic exist
        if topic not in self.word_database.get_topics():
            raise ValueError(f"Topic '{topic}' not found")
        
        if subtopic not in self.word_database.get_subtopics(topic):
            raise ValueError(f"Subtopic '{subtopic}' not found in topic '{topic}'")
        
        # Get word data
        word_data = self.word_database.get_words(topic, subtopic)
        all_words = word_data.character_words + word_data.defining_words
        
        # Check if subtopic has sufficient words
        if not self.word_database.has_sufficient_words(topic, subtopic):
            raise ValueError(f"Subtopic '{subtopic}' has insufficient words for gameplay")
        
        # Calculate maximum words that can fit
        max_words = self.calculate_word_capacity(settings.grid_size, all_words)
        
        # Create game instance
        game = Game(
            id=str(uuid.uuid4()),
            topic=topic,
            subtopic=subtopic,
            grid_size=settings.grid_size,
            time_limit=settings.time_limit,
            max_words=max_words,
            start_time=datetime.now(),
            status=GameStatus.SETUP
        )
        
        self.current_game = game
        return game
    
    def start_game(self) -> Grid:
        """
        Start the current game by generating the grid.
        
        Returns:
            Generated grid for the game
            
        Raises:
            RuntimeError: If no game is initialized
        """
        if not self.current_game:
            raise RuntimeError("No game initialized. Call initialize_game first.")
        
        # Get word data for the current game
        word_data = self.word_database.get_words(
            self.current_game.topic, 
            self.current_game.subtopic
        )
        
        # Combine and adjust words for grid capacity
        all_words = word_data.character_words + word_data.defining_words
        adjusted_words = self.adjust_word_count_for_grid(
            all_words, 
            self.current_game.grid_size
        )
        
        # Create word types list
        word_types = []
        char_count = len(word_data.character_words)
        for i, word in enumerate(adjusted_words):
            if word in word_data.character_words:
                word_types.append(WordType.CHARACTER)
            else:
                word_types.append(WordType.DEFINING)
        
        # Generate grid with adaptive success rate based on grid size
        # Smaller grids need lower success rate due to placement difficulty
        min_success_rate = 0.7 if self.current_game.grid_size <= 10 else 0.8
        self.current_grid = self.grid_generator.generate_grid(
            adjusted_words,
            word_types,
            self.current_game.grid_size,
            min_success_rate=min_success_rate
        )
        
        # Update game status and start timer
        self.current_game.status = GameStatus.ACTIVE
        self.current_game.start_time = datetime.now()
        
        # Start timer with callbacks
        self.timer_manager.start_timer(
            self.current_game,
            update_callback=self._on_timer_update,
            expiration_callback=self._on_timer_expiration
        )
        
        return self.current_grid
    
    def get_current_game(self) -> Optional[Game]:
        """Get the current game instance."""
        return self.current_game
    
    def get_current_grid(self) -> Optional[Grid]:
        """Get the current grid instance."""
        return self.current_grid
    
    def validate_game_configuration(self, topic: str, subtopic: str, 
                                  settings: GameSettings) -> Tuple[bool, str]:
        """
        Validate a game configuration before initialization.
        
        Args:
            topic: Topic to validate
            subtopic: Subtopic to validate
            settings: Game settings to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if topic exists
            if topic not in self.word_database.get_topics():
                return False, f"Topic '{topic}' not found"
            
            # Check if subtopic exists
            if subtopic not in self.word_database.get_subtopics(topic):
                return False, f"Subtopic '{subtopic}' not found in topic '{topic}'"
            
            # Check if subtopic has sufficient words
            if not self.word_database.has_sufficient_words(topic, subtopic):
                return False, f"Subtopic '{subtopic}' has insufficient words for gameplay"
            
            # Get word data and check capacity
            word_data = self.word_database.get_words(topic, subtopic)
            all_words = word_data.character_words + word_data.defining_words
            capacity = self.calculate_word_capacity(settings.grid_size, all_words)
            
            if capacity == 0:
                return False, f"Grid size {settings.grid_size} is too small for available words"
            
            return True, "Configuration is valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def end_game(self, status: GameStatus = GameStatus.COMPLETED) -> None:
        """
        End the current game with the specified status.
        
        Args:
            status: Final game status
        """
        if self.current_game:
            self.current_game.status = status
            self.timer_manager.stop_timer()
    
    def discover_word(self, word: str) -> bool:
        """
        Mark a word as discovered and update progress.
        
        Args:
            word: The word that was discovered.
            
        Returns:
            True if word was newly discovered, False if already found.
        """
        if not self.current_grid or word in self.current_grid.discovered_words:
            return False
        
        # Check if word exists in solution
        valid_words = {wp.word for wp in self.current_grid.solution}
        if word not in valid_words:
            return False
        
        # Add to discovered words
        self.current_grid.discovered_words.add(word)
        
        # Update progress tracking
        self.progress_tracker.update_progress(self.current_grid, word)
        
        # Check for game completion
        if self.timer_manager.check_game_completion(self.current_grid):
            self.end_game(GameStatus.COMPLETED)
        
        return True
    
    def get_timer_status(self) -> dict:
        """Get current timer status."""
        return self.timer_manager.get_timer_status()
    
    def get_progress_info(self) -> dict:
        """Get current progress information."""
        if not self.current_grid:
            return {'found_words': 0, 'total_words': 0, 'percentage': 0, 'complete': False}
        return self.progress_tracker.get_progress_info(self.current_grid)
    
    def get_word_breakdown(self) -> dict:
        """Get breakdown of found words by type."""
        if not self.current_grid:
            return {'character_words': {'total': 0, 'found': 0}, 'defining_words': {'total': 0, 'found': 0}}
        return self.progress_tracker.get_word_breakdown(self.current_grid)
    
    def pause_game(self) -> None:
        """Pause the current game timer."""
        self.timer_manager.pause_timer()
    
    def resume_game(self) -> None:
        """Resume the paused game timer."""
        self.timer_manager.resume_timer()
    
    def is_game_active(self) -> bool:
        """Check if a game is currently active."""
        return (self.current_game is not None and 
                self.current_game.status == GameStatus.ACTIVE and
                not self.timer_manager.is_time_expired())
    
    def set_timer_update_callback(self, callback: Callable[[Game, int], None]) -> None:
        """Set callback for timer updates."""
        self._external_timer_callback = callback
    
    def set_progress_update_callback(self, callback: Callable[[int, int, float], None]) -> None:
        """Set callback for progress updates."""
        self._external_progress_callback = callback
    
    def set_word_found_callback(self, callback: Callable[[str, int], None]) -> None:
        """Set callback for word discovery."""
        self._external_word_found_callback = callback
    
    def set_game_completion_callback(self, callback: Callable[[Game, Grid], None]) -> None:
        """Set callback for game completion."""
        self._external_completion_callback = callback
    
    def set_game_expiration_callback(self, callback: Callable[[Game], None]) -> None:
        """Set callback for game expiration."""
        self._external_expiration_callback = callback
    
    # Internal callback methods
    def _on_timer_update(self, game: Game, remaining_seconds: int) -> None:
        """Internal callback for timer updates."""
        if hasattr(self, '_external_timer_callback') and self._external_timer_callback:
            self._external_timer_callback(game, remaining_seconds)
    
    def _on_timer_expiration(self, game: Game) -> None:
        """Internal callback for timer expiration."""
        self.end_game(GameStatus.EXPIRED)
        if hasattr(self, '_external_expiration_callback') and self._external_expiration_callback:
            self._external_expiration_callback(game)
    
    def _on_game_completion(self, game: Game, grid: Grid) -> None:
        """Internal callback for game completion."""
        if hasattr(self, '_external_completion_callback') and self._external_completion_callback:
            self._external_completion_callback(game, grid)
    
    def _on_progress_update(self, found: int, total: int, percentage: float) -> None:
        """Internal callback for progress updates."""
        if hasattr(self, '_external_progress_callback') and self._external_progress_callback:
            self._external_progress_callback(found, total, percentage)
    
    def _on_word_found(self, word: str, remaining: int) -> None:
        """Internal callback for word discovery."""
        if hasattr(self, '_external_word_found_callback') and self._external_word_found_callback:
            self._external_word_found_callback(word, remaining)

    def calculate_game_results(self) -> Dict[str, Any]:
        """Calculate and store results for the current game.

        Returns:
            Dictionary containing all game results.

        Raises:
            RuntimeError: If no game is active or game is not ended.
        """
        if not self.current_game or not self.current_grid:
            raise RuntimeError("No game active to calculate results")

        if self.current_game.status not in [GameStatus.COMPLETED, GameStatus.EXPIRED]:
            raise RuntimeError("Game must be completed or expired to calculate results")

        # Calculate results
        self.game_results = self.results_calculator.calculate_results(
            self.current_game,
            self.current_grid,
            datetime.now()
        )

        # Add to session results
        self.session_results.append(self.game_results)

        return self.game_results

    def get_game_results(self) -> Optional[Dict[str, Any]]:
        """Get the current game results.

        Returns:
            Results dictionary if available, None otherwise.
        """
        return self.game_results

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session.

        Returns:
            Dictionary with session statistics.
        """
        return self.results_calculator.calculate_session_stats(self.session_results)

    def get_performance_rating(self) -> str:
        """Get performance rating for the current game.

        Returns:
            Performance rating string.

        Raises:
            RuntimeError: If no results are available.
        """
        if not self.game_results:
            raise RuntimeError("No game results available")

        time_percentage = (self.game_results['elapsed_time'] /
                          self.game_results['time_limit'] * 100)

        return self.results_calculator.get_performance_rating(
            self.game_results['completion_percentage'],
            self.game_results['perfect_game'],
            time_percentage
        )

    def reset_session(self) -> None:
        """Reset session statistics (clear all game results)."""
        self.session_results = []
        self.game_results = None

    def start_new_game(self) -> None:
        """Prepare for a new game by clearing current game state."""
        self.current_game = None
        self.current_grid = None
        self.game_results = None
        self.timer_manager = TimerManager()
        self.progress_tracker = ProgressTracker()

        # Re-set up timer callbacks
        self.timer_manager.set_completion_callback(self._on_game_completion)
        self.progress_tracker.set_progress_callback(self._on_progress_update)
        self.progress_tracker.set_word_found_callback(self._on_word_found)