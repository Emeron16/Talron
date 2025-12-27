"""Main game screen with grid, timer, and progress display."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from datetime import datetime, timedelta
from .gui_main_window import BaseScreen, MainWindow
from .gui_grid_widget import LetterGridWidget
from ..models.core import Grid, Game, Coordinate, GameStatus
from ..services.selection_validator import SelectionValidator
from .sound_manager import SoundManager
from .hint_system import HintSystem
from .animation_helper import AnimationHelper


class GameScreen(BaseScreen):
    """Main game playing screen."""

    def __init__(self, parent: MainWindow, game: Game, game_grid: Grid,
                 validator: SelectionValidator,
                 on_word_discovered: Callable[[str], bool],
                 on_game_complete: Callable,
                 sound_enabled: bool = True,
                 hint_system: Optional[HintSystem] = None):
        """Initialize the game screen.

        Args:
            parent: Parent MainWindow instance.
            game: Current game instance.
            game_grid: Game grid.
            validator: Selection validator.
            on_word_discovered: Callback when word is discovered.
            on_game_complete: Callback when game is complete.
            sound_enabled: Whether sound effects are enabled.
            hint_system: Optional hint system for providing hints.
        """
        super().__init__(parent)
        self.game = game
        self.game_grid = game_grid
        self.validator = validator
        self.on_word_discovered = on_word_discovered
        self.on_game_complete = on_game_complete

        # Sound and hints
        self.sound_manager = SoundManager(enabled=sound_enabled)
        self.hint_system = hint_system or HintSystem()

        # Timer state
        self.start_time = datetime.now()
        self.timer_running = True
        self.timer_job = None
        self.timer_warned = False

        self._create_widgets()
        self._start_timer()

    def _create_widgets(self):
        """Create the game screen widgets."""
        # Configure custom style for progress labels without background
        style = ttk.Style()
        style.configure('Progress.TLabel',
                       font=('Segoe UI', 13),
                       foreground='#000000',  # Black for better visibility
                       background='#1a1a2e')

        # Top panel with game info
        top_panel = ttk.Frame(self)
        top_panel.pack(side=tk.TOP, fill=tk.X, pady=10)

        # Game title
        title_text = f"{self.game.topic.title()} - {self.game.subtopic}"
        title = ttk.Label(top_panel, text=title_text, style='Header.TLabel')
        title.pack(side=tk.LEFT, padx=20)

        # Timer display
        self.timer_label = ttk.Label(top_panel, text="Time: 0:00", style='Header.TLabel')
        self.timer_label.pack(side=tk.RIGHT, padx=20)

        # Main game area
        game_frame = ttk.Frame(self)
        game_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left panel - Grid
        grid_frame = ttk.Frame(game_frame)
        grid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.grid_widget = LetterGridWidget(
            grid_frame,
            self.game_grid,
            self._on_word_selected
        )
        self.grid_widget.pack(pady=20)

        # Right panel - Progress and word list
        right_panel = ttk.Frame(game_frame, width=250)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        right_panel.pack_propagate(False)

        # Progress section
        progress_frame = ttk.LabelFrame(right_panel, text="Progress", padding=15)
        progress_frame.pack(fill=tk.X, pady=(0, 20))

        self.progress_label = tk.Label(progress_frame,
                                       text=f"0 / {len(self.game_grid.solution)} words",
                                       font=('Segoe UI', 16, 'bold'),
                                       fg='#000000',
                                       bg='#ECF0F1')  # Light gray background to match frame
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, length=200, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        # Word breakdown
        self.breakdown_label = tk.Label(progress_frame, text="",
                                        font=('Segoe UI', 13),
                                        fg='#000000',
                                        bg='#ECF0F1',
                                        justify=tk.LEFT)
        self.breakdown_label.pack(pady=5)
        self._update_progress()

        # Found words list
        words_frame = ttk.LabelFrame(right_panel, text="Found Words", padding=15)
        words_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable word list
        list_frame = ttk.Frame(words_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.words_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                        font=('Arial', 10), bg='#ECF0F1',
                                        selectmode=tk.NONE)
        self.words_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.words_listbox.yview)

        # Bottom panel with controls
        controls_frame = ttk.Frame(self)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # Hint button (if hints available)
        if self.hint_system.hints_remaining > 0:
            self.hint_button = self.create_button(
                f"Hint ({self.hint_system.hints_remaining})",
                self._on_hint_requested,
                'Primary.TButton'
            )
            self.hint_button.pack(side=tk.LEFT, padx=5)

        # Sound toggle button
        sound_text = "🔊 Sound" if self.sound_manager.enabled else "🔇 Sound"
        self.sound_button = self.create_button(
            sound_text,
            self._on_toggle_sound,
            'Secondary.TButton'
        )
        self.sound_button.pack(side=tk.LEFT, padx=5)

        # Music toggle button
        music_icon = "🎵 Music" if not self.parent.background_music.is_muted else "🔇 Music"
        self.music_button = self.create_button(
            music_icon,
            self._toggle_music_wrapper,
            'Secondary.TButton'
        )
        self.music_button.pack(side=tk.LEFT, padx=5)

        quit_button = self.create_button(
            "Quit Game",
            self._on_quit,
            'Secondary.TButton'
        )
        quit_button.pack(side=tk.RIGHT, padx=20)

    def _on_word_selected(self, coordinates: list):
        """Handle word selection from grid.

        Args:
            coordinates: List of selected coordinates.
        """
        # Validate selection
        word = self.validator.validate_selection(self.game_grid, coordinates)

        if word:
            # Check if word was already discovered
            was_discovered = self.on_word_discovered(word)

            if was_discovered:
                # Play success sound
                self.sound_manager.play_sound('word_found')

                # Update grid display
                self.grid_widget.mark_word_discovered(word)

                # Add to words list with animation
                self.words_listbox.insert(tk.END, word)
                AnimationHelper.pulse_widget(self.progress_label)

                # Update progress
                self._update_progress()

                # Check if game is complete
                if len(self.game_grid.discovered_words) == len(self.game_grid.solution):
                    self._on_game_finished()
            else:
                # Word already found
                self.sound_manager.play_sound('invalid')
                self.parent.show_info("Already Found", f"You already found '{word}'!")
        else:
            # Invalid selection
            if len(coordinates) > 1:
                self.sound_manager.play_sound('invalid')

    def _update_progress(self):
        """Update progress display."""
        found = len(self.game_grid.discovered_words)
        total = len(self.game_grid.solution)
        percentage = (found / total * 100) if total > 0 else 0

        # Update labels
        self.progress_label.config(text=f"{found} / {total} words")
        self.progress_bar['value'] = percentage

        # Update breakdown
        char_found = sum(1 for w in self.game_grid.discovered_words
                        if any(p.word == w and p.word_type.value == 'character'
                              for p in self.game_grid.solution))
        def_found = found - char_found

        self.breakdown_label.config(
            text=f"Characters: {char_found}\nDefining: {def_found}"
        )

    def _start_timer(self):
        """Start the game timer."""
        self.timer_running = True
        self._update_timer()

    def _update_timer(self):
        """Update timer display."""
        if not self.timer_running:
            return

        # Calculate elapsed time
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # Handle no time limit (time_limit = 0)
        if self.game.time_limit == 0:
            # Show elapsed time instead of countdown
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            time_str = f"Time: {minutes}:{seconds:02d}"
            self.timer_label.config(text=time_str, foreground='#FFFFFF')  # White

            # Schedule next update
            self.timer_job = self.after(1000, self._update_timer)
            return

        # Calculate remaining time for timed games
        remaining = max(0, self.game.time_limit - elapsed)

        # Format time
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        time_str = f"Time: {minutes}:{seconds:02d}"

        # Update label
        self.timer_label.config(text=time_str)

        # Change color if time is running low
        if remaining <= 60:
            self.timer_label.config(foreground='#E74C3C')  # Red
            if not self.timer_warned:
                self.sound_manager.play_sound('timer_warning')
                self.timer_warned = True
        elif remaining <= 120:
            self.timer_label.config(foreground='#F39C12')  # Orange

        # Check if time expired
        if remaining <= 0:
            self._on_time_expired()
            return

        # Schedule next update
        self.timer_job = self.after(1000, self._update_timer)

    def _on_time_expired(self):
        """Handle time expiration."""
        self.timer_running = False
        self.parent.show_warning("Time's Up!", "The time limit has been reached.")
        self._on_game_finished()

    def _on_game_finished(self):
        """Handle game completion."""
        self.timer_running = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
        self.on_game_complete()

    def _on_quit(self):
        """Handle quit button click."""
        if self.parent.ask_yes_no("Quit Game", "Are you sure you want to quit this game?"):
            self.timer_running = False
            if self.timer_job:
                self.after_cancel(self.timer_job)
            self._on_game_finished()

    def _on_hint_requested(self):
        """Handle hint button click."""
        hint = self.hint_system.get_hint(self.game_grid)

        if hint:
            # Display hint in custom in-game window
            self._show_hint_window(hint)

            # Update hint button
            if hasattr(self, 'hint_button'):
                self.hint_button.config(text=f"Hint ({self.hint_system.hints_remaining})")
                if self.hint_system.hints_remaining == 0:
                    self.hint_button.config(state='disabled')

            # Highlight word if it's a reveal hint
            if hint['type'] == 'reveal':
                for placement in self.game_grid.solution:
                    if placement.word == hint['word']:
                        self.grid_widget.highlight_word(placement)
                        # Clear highlight after 3 seconds
                        self.after(3000, self.grid_widget.clear_highlights)
                        break
        else:
            self.parent.show_info("No Hints", "No hints remaining!")

    def _show_hint_window(self, hint: dict):
        """Display hint in an overlay window within the game screen.

        Args:
            hint: Hint dictionary with type, message, and metadata.
        """
        # Create overlay frame that covers the center of the screen
        overlay = tk.Frame(self, bg='#000000', bd=2, relief=tk.RAISED)
        overlay.place(relx=0.5, rely=0.5, anchor='center', width=500, height=300)

        # Inner frame with dark background
        inner_frame = tk.Frame(overlay, bg='#1a1a2e', padx=20, pady=20)
        inner_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            inner_frame,
            text="💡 Hint",
            style='Header.TLabel',
            font=('Segoe UI', 20, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # Hint message
        message_label = tk.Label(
            inner_frame,
            text=hint['message'],
            font=('Segoe UI', 14),
            fg='#ECF0F1',
            bg='#1a1a2e',
            wraplength=450,
            justify=tk.CENTER
        )
        message_label.pack(pady=10)

        # Additional hint details based on type
        if hint['type'] == 'letter' and 'hint_detail' in hint:
            detail_label = tk.Label(
                inner_frame,
                text=hint['hint_detail'],
                font=('Segoe UI', 12, 'italic'),
                fg='#BDC3C7',
                bg='#1a1a2e'
            )
            detail_label.pack(pady=5)

        # Close button
        close_button = ttk.Button(
            inner_frame,
            text="Got It!",
            command=lambda: overlay.destroy(),
            style='Primary.TButton'
        )
        close_button.pack(pady=(20, 0))

        # Auto-dismiss after 10 seconds
        self.after(10000, lambda: overlay.destroy() if overlay.winfo_exists() else None)

        # Focus on close button for keyboard interaction
        close_button.focus_set()

        # Bind Escape and Enter to close
        overlay.bind('<Escape>', lambda e: overlay.destroy())
        overlay.bind('<Return>', lambda e: overlay.destroy())

    def _on_toggle_sound(self):
        """Handle sound toggle button click."""
        self.sound_manager.toggle_sounds()
        sound_text = "🔊 Sound" if self.sound_manager.enabled else "🔇 Sound"
        self.sound_button.config(text=sound_text)

    def _toggle_music_wrapper(self):
        """Wrapper to toggle music and update button text."""
        self.parent._toggle_music()
        if hasattr(self, 'music_button'):
            music_icon = "🎵 Music" if not self.parent.background_music.is_muted else "🔇 Music"
            self.music_button.config(text=music_icon)

    def cleanup(self):
        """Clean up resources."""
        self.timer_running = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
        self.sound_manager.cleanup()
