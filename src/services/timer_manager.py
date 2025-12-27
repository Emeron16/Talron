"""Timer management service for the word search game."""

import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable
from ..models.core import Game, GameStatus, Grid


class TimerManager:
    """Manages game timer with countdown functionality and automatic termination."""
    
    def __init__(self):
        """Initialize the timer manager."""
        self.current_game: Optional[Game] = None
        self.timer_thread: Optional[threading.Thread] = None
        self.is_running: bool = False
        self.update_callback: Optional[Callable[[Game, int], None]] = None
        self.expiration_callback: Optional[Callable[[Game], None]] = None
        self.completion_callback: Optional[Callable[[Game, Grid], None]] = None
        self._stop_event = threading.Event()
    
    def start_timer(self, game: Game, 
                   update_callback: Optional[Callable[[Game, int], None]] = None,
                   expiration_callback: Optional[Callable[[Game], None]] = None) -> None:
        """
        Start the countdown timer for a game.
        
        Args:
            game: The game instance to time.
            update_callback: Optional callback for timer updates (game, remaining_seconds).
            expiration_callback: Optional callback when timer expires (game).
        """
        if self.is_running:
            self.stop_timer()
        
        self.current_game = game
        self.update_callback = update_callback
        self.expiration_callback = expiration_callback
        self.is_running = True
        self._stop_event.clear()
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
    
    def stop_timer(self) -> None:
        """Stop the current timer."""
        self.is_running = False
        self._stop_event.set()
        
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1.0)
        
        self.timer_thread = None
        self.current_game = None
        self.update_callback = None
        self.expiration_callback = None
    
    def pause_timer(self) -> None:
        """Pause the current timer."""
        self.is_running = False
    
    def resume_timer(self) -> None:
        """Resume the paused timer."""
        if self.current_game and not self.is_running:
            self.is_running = True
    
    def get_remaining_time(self) -> int:
        """
        Get remaining time in seconds.
        
        Returns:
            Remaining time in seconds, or 0 if no active timer or time expired.
        """
        if not self.current_game:
            return 0
        
        elapsed = (datetime.now() - self.current_game.start_time).total_seconds()
        remaining = self.current_game.time_limit - elapsed
        return max(0, int(remaining))
    
    def get_elapsed_time(self) -> int:
        """
        Get elapsed time in seconds.
        
        Returns:
            Elapsed time in seconds, or 0 if no active timer.
        """
        if not self.current_game:
            return 0
        
        elapsed = (datetime.now() - self.current_game.start_time).total_seconds()
        return int(elapsed)
    
    def is_time_expired(self) -> bool:
        """
        Check if the current game time has expired.
        
        Returns:
            True if time has expired or no active timer.
        """
        return self.get_remaining_time() == 0
    
    def format_time(self, seconds: int) -> str:
        """
        Format time in MM:SS format.
        
        Args:
            seconds: Time in seconds.
            
        Returns:
            Formatted time string.
        """
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def _timer_loop(self) -> None:
        """Internal timer loop that runs in a separate thread."""
        last_remaining = None
        
        while self.is_running and self.current_game and not self._stop_event.is_set():
            remaining = self.get_remaining_time()
            
            # Call update callback if remaining time changed
            if remaining != last_remaining and self.update_callback:
                try:
                    self.update_callback(self.current_game, remaining)
                except Exception as e:
                    # Log error but continue timer
                    print(f"Timer update callback error: {e}")
            
            last_remaining = remaining
            
            # Check if time expired
            if remaining == 0:
                self.is_running = False
                if self.expiration_callback:
                    try:
                        self.expiration_callback(self.current_game)
                    except Exception as e:
                        print(f"Timer expiration callback error: {e}")
                break
            
            # Wait for next update (check every second)
            if self._stop_event.wait(timeout=1.0):
                break
    
    def set_completion_callback(self, callback: Callable[[Game, Grid], None]) -> None:
        """
        Set callback for game completion.
        
        Args:
            callback: Function to call when game is completed (game, grid).
        """
        self.completion_callback = callback
    
    def check_game_completion(self, grid: Grid) -> bool:
        """
        Check if the game is complete and handle completion.
        
        Args:
            grid: Current game grid.
            
        Returns:
            True if game is complete.
        """
        if not self.current_game:
            return False
        
        total_words = len(grid.solution)
        found_words = len(grid.discovered_words)
        
        if found_words == total_words:
            # Game completed - stop timer and call completion callback
            self.stop_timer()
            if self.completion_callback:
                try:
                    self.completion_callback(self.current_game, grid)
                except Exception as e:
                    print(f"Game completion callback error: {e}")
            return True
        
        return False
    
    def get_timer_status(self) -> dict:
        """
        Get current timer status information.
        
        Returns:
            Dictionary with timer status information.
        """
        if not self.current_game:
            return {
                'active': False,
                'remaining': 0,
                'elapsed': 0,
                'total': 0,
                'formatted_remaining': '00:00',
                'formatted_elapsed': '00:00',
                'expired': True
            }
        
        remaining = self.get_remaining_time()
        elapsed = self.get_elapsed_time()
        
        return {
            'active': self.is_running,
            'remaining': remaining,
            'elapsed': elapsed,
            'total': self.current_game.time_limit,
            'formatted_remaining': self.format_time(remaining),
            'formatted_elapsed': self.format_time(elapsed),
            'expired': remaining == 0
        }


class ProgressTracker:
    """Tracks word discovery progress during gameplay."""
    
    def __init__(self):
        """Initialize the progress tracker."""
        self.progress_callback: Optional[Callable[[int, int, float], None]] = None
        self.word_found_callback: Optional[Callable[[str, int], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, int, float], None]) -> None:
        """
        Set callback for progress updates.
        
        Args:
            callback: Function to call on progress updates (found, total, percentage).
        """
        self.progress_callback = callback
    
    def set_word_found_callback(self, callback: Callable[[str, int], None]) -> None:
        """
        Set callback for word discovery.
        
        Args:
            callback: Function to call when word is found (word, remaining_count).
        """
        self.word_found_callback = callback
    
    def update_progress(self, grid: Grid, newly_found_word: Optional[str] = None) -> dict:
        """
        Update progress tracking and call callbacks.
        
        Args:
            grid: Current game grid.
            newly_found_word: Word that was just discovered (if any).
            
        Returns:
            Dictionary with current progress information.
        """
        total_words = len(grid.solution)
        found_words = len(grid.discovered_words)
        percentage = (found_words / total_words * 100) if total_words > 0 else 0
        remaining_words = total_words - found_words
        
        # Call progress callback
        if self.progress_callback:
            try:
                self.progress_callback(found_words, total_words, percentage)
            except Exception as e:
                print(f"Progress callback error: {e}")
        
        # Call word found callback if a new word was discovered
        if newly_found_word and self.word_found_callback:
            try:
                self.word_found_callback(newly_found_word, remaining_words)
            except Exception as e:
                print(f"Word found callback error: {e}")
        
        return {
            'found_words': found_words,
            'total_words': total_words,
            'remaining_words': remaining_words,
            'percentage': percentage,
            'complete': found_words == total_words
        }
    
    def get_progress_info(self, grid: Grid) -> dict:
        """
        Get current progress information without triggering callbacks.
        
        Args:
            grid: Current game grid.
            
        Returns:
            Dictionary with progress information.
        """
        total_words = len(grid.solution)
        found_words = len(grid.discovered_words)
        percentage = (found_words / total_words * 100) if total_words > 0 else 0
        remaining_words = total_words - found_words
        
        return {
            'found_words': found_words,
            'total_words': total_words,
            'remaining_words': remaining_words,
            'percentage': percentage,
            'complete': found_words == total_words
        }
    
    def get_word_breakdown(self, grid: Grid) -> dict:
        """
        Get breakdown of found words by type.
        
        Args:
            grid: Current game grid.
            
        Returns:
            Dictionary with word type breakdown.
        """
        character_words = []
        defining_words = []
        
        for word_placement in grid.solution:
            if word_placement.word_type.value == 'character':
                character_words.append(word_placement.word)
            else:
                defining_words.append(word_placement.word)
        
        char_found = sum(1 for word in character_words if word in grid.discovered_words)
        def_found = sum(1 for word in defining_words if word in grid.discovered_words)
        
        return {
            'character_words': {
                'total': len(character_words),
                'found': char_found,
                'remaining': len(character_words) - char_found,
                'percentage': (char_found / len(character_words) * 100) if character_words else 0
            },
            'defining_words': {
                'total': len(defining_words),
                'found': def_found,
                'remaining': len(defining_words) - def_found,
                'percentage': (def_found / len(defining_words) * 100) if defining_words else 0
            }
        }