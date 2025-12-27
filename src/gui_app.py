"""Main GUI application for the themed word search game."""

import tkinter as tk
from tkinter import messagebox
import traceback

from .ui.gui_main_window import MainWindow
from .ui.gui_topic_screen import TopicSelectionScreen
from .ui.gui_settings_screen import SettingsScreen
from .ui.gui_game_screen import GameScreen
from .ui.gui_results_screen import ResultsScreen
from .ui.hint_system import HintSystem
from .ui.sound_manager import SoundManager
from .services.game_controller import GameController
from .services.selection_validator import SelectionValidator
from .services.results_calculator import ResultsCalculator
from .data.word_database import WordDatabase
from .models.core import GameSettings, GameStatus
from .exceptions import (
    WordSearchError,
    DatabaseError,
    TopicNotFoundError,
    SubtopicNotFoundError,
    GridGenerationError
)


class WordSearchGUIApp:
    """Main GUI application controller."""

    def __init__(self):
        """Initialize the GUI application."""
        try:
            # Initialize window
            self.window = MainWindow()
            self.window.title("Talron Word Search")

            # Initialize game components
            self.game_controller = GameController()
            self.word_database = WordDatabase()
            self.selection_validator = None
            self.results_calculator = ResultsCalculator()

            # Set game controller in window
            self.window.set_game_controller(self.game_controller)

            # Current game state
            self.current_topic = None
            self.current_subtopic = None
            self.current_settings = None

            # Sound and hints
            self.sound_manager = SoundManager(enabled=True)
            self.hint_system = None

            # Create screens
            self._create_screens()

            # Show topic selection screen
            self.topic_screen.show()

        except DatabaseError as e:
            messagebox.showerror(
                "Database Error",
                f"Failed to load game database:\n{e.user_message}\n\nThe application will now close."
            )
            raise

    def _create_screens(self):
        """Create all application screens."""
        # Topic selection screen
        self.topic_screen = TopicSelectionScreen(
            self.window,
            self.word_database,
            self._on_topic_selected
        )

        # Settings screen
        self.settings_screen = SettingsScreen(
            self.window,
            self._on_settings_complete
        )
        self.settings_screen.set_back_callback(self._show_topic_screen)

        # Game and results screens will be created dynamically

    def _on_topic_selected(self, topic: str, subtopic: str):
        """Handle topic and subtopic selection.

        Args:
            topic: Selected topic.
            subtopic: Selected subtopic.
        """
        self.current_topic = topic
        self.current_subtopic = subtopic

        # Update settings screen with topic info
        self.settings_screen.set_topic(topic, subtopic)

        # Show settings screen
        self.settings_screen.show()

    def _on_settings_complete(self, settings: GameSettings):
        """Handle settings confirmation.

        Args:
            settings: Configured game settings.
        """
        self.current_settings = settings

        # Validate configuration
        is_valid, message = self.game_controller.validate_game_configuration(
            self.current_topic,
            self.current_subtopic,
            settings
        )

        if not is_valid:
            self.window.show_error("Invalid Configuration", message)
            return

        # Start game
        self._start_game()

    def _start_game(self):
        """Initialize and start the game."""
        try:
            # Initialize game
            game = self.game_controller.initialize_game(
                self.current_topic,
                self.current_subtopic,
                self.current_settings
            )

            # Generate grid
            grid = self.game_controller.start_game()

            # Create selection validator for this grid
            self.selection_validator = SelectionValidator(grid)

            # Initialize hint system with configured max hints
            max_hints = self.settings_screen.get_max_hints()
            self.hint_system = HintSystem(max_hints=max_hints)

            # Create game screen
            game_screen = GameScreen(
                self.window,
                game,
                grid,
                self.selection_validator,
                self._on_word_discovered,
                self._on_game_complete,
                sound_enabled=self.sound_manager.enabled,
                hint_system=self.hint_system
            )

            # Show game screen
            game_screen.show()

        except GridGenerationError as e:
            self.window.show_error("Grid Generation Error",
                                  f"{e.user_message}\n\nPlease try different settings.")
            self.settings_screen.show()

        except WordSearchError as e:
            self.window.show_error("Game Error",
                                  f"{e.user_message}\n\nReturning to topic selection.")
            self.topic_screen.show()

        except Exception as e:
            # Catch any unexpected errors
            self.window.show_error("Unexpected Error",
                                  f"An unexpected error occurred while starting the game:\n{str(e)}\n\nPlease try again.")
            self.settings_screen.show()

    def _on_word_discovered(self, word: str) -> bool:
        """Handle word discovery.

        Args:
            word: The word that was found.

        Returns:
            True if word was newly discovered, False if already found.
        """
        return self.game_controller.discover_word(word)

    def _on_game_complete(self):
        """Handle game completion."""
        try:
            # End game
            if len(self.game_controller.current_grid.discovered_words) == len(self.game_controller.current_grid.solution):
                self.game_controller.end_game(GameStatus.COMPLETED)
            else:
                self.game_controller.end_game(GameStatus.EXPIRED)

            # Calculate results
            results = self.game_controller.calculate_game_results()

            # Show results screen
            results_screen = ResultsScreen(
                self.window,
                self.game_controller.current_game,
                self.game_controller.current_grid,
                results,
                self._on_play_again,
                self._on_new_topic,
                self._on_quit,
                sound_manager=self.sound_manager
            )

            results_screen.show()

        except Exception as e:
            # Handle any errors in game completion gracefully
            self.window.show_error("Error",
                                  f"An error occurred while calculating results:\n{str(e)}\n\nReturning to topic selection.")
            self.topic_screen.show()

    def _on_play_again(self):
        """Handle play again request."""
        # Reset game state
        self.game_controller.start_new_game()

        # Reset hint system
        if self.hint_system:
            self.hint_system.reset()

        # Start new game with same topic and settings
        self._start_game()

    def _on_new_topic(self):
        """Handle new topic request."""
        # Reset game state
        self.game_controller.start_new_game()

        # Reset screens
        self.topic_screen.reset()
        self.settings_screen.reset()

        # Show topic selection
        self.topic_screen.show()

    def _show_topic_screen(self):
        """Show the topic selection screen."""
        self.topic_screen.show()

    def _on_quit(self):
        """Handle quit request."""
        # Show session stats if any games were played
        session_stats = self.game_controller.get_session_stats()

        if session_stats['games_played'] > 0:
            stats_message = (
                f"Session Statistics:\n\n"
                f"Games Played: {session_stats['games_played']}\n"
                f"Total Words Found: {session_stats['total_words_found']}\n"
                f"Total Score: {session_stats['total_score']}\n\n"
                f"Thanks for playing!"
            )
            self.window.show_info("Session Summary", stats_message)

        self.window.destroy()

    def run(self):
        """Run the application."""
        try:
            self.window.mainloop()
        except Exception as e:
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred:\n{str(e)}\n\n{traceback.format_exc()}"
            )
            raise


def main():
    """Main entry point for GUI application."""
    try:
        app = WordSearchGUIApp()
        app.run()
    except DatabaseError:
        # Already handled in __init__
        pass
    except Exception as e:
        messagebox.showerror(
            "Fatal Error",
            f"A fatal error occurred:\n{str(e)}\n\nThe application will now close."
        )
        raise


if __name__ == '__main__':
    main()
