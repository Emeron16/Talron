"""Game results display screen for GUI."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Any, Optional
from .gui_main_window import BaseScreen, MainWindow
from ..models.core import Grid, Game
from .sound_manager import SoundManager
from .gui_grid_widget import LetterGridWidget


class ResultsScreen(BaseScreen):
    """Screen for displaying game results."""

    def __init__(self, parent: MainWindow, game: Game, game_grid: Grid,
                 results: Dict[str, Any],
                 on_play_again: Callable,
                 on_new_topic: Callable,
                 on_quit: Callable,
                 sound_manager: Optional[SoundManager] = None):
        """Initialize the results screen.

        Args:
            parent: Parent MainWindow instance.
            game: Completed game instance.
            game_grid: Game grid.
            results: Game results dictionary.
            on_play_again: Callback to play again with same topic.
            on_new_topic: Callback to choose new topic.
            on_quit: Callback to quit application.
            sound_manager: Optional sound manager for playing completion sounds.
        """
        super().__init__(parent)
        self.game = game
        self.game_grid = game_grid
        self.results = results
        self.on_play_again = on_play_again
        self.on_new_topic = on_new_topic
        self.on_quit = on_quit
        self.sound_manager = sound_manager

        # Play completion sound
        if self.sound_manager:
            if results.get('perfect_game'):
                self.sound_manager.play_sound('perfect')
            else:
                self.sound_manager.play_sound('game_complete')

        self._create_widgets()

    def _create_widgets(self):
        """Create the results screen widgets."""
        # Action buttons - pack at bottom FIRST to reserve space and ensure visibility
        button_container = ttk.Frame(self)
        button_container.pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=20)

        # Use grid layout for centered buttons
        button_container.grid_columnconfigure(0, weight=1)  # Left spacer
        button_container.grid_columnconfigure(1, weight=0)  # Play Again button
        button_container.grid_columnconfigure(2, weight=0)  # New Topic button
        button_container.grid_columnconfigure(3, weight=0)  # Quit button
        button_container.grid_columnconfigure(4, weight=1)  # Right spacer

        # Create buttons using grid to center them - buttons are children of button_container
        play_again_btn = ttk.Button(
            button_container,
            text="Play Again (Same Topic)",
            command=self.on_play_again,
            style='Primary.TButton'
        )
        play_again_btn.grid(row=0, column=1, padx=10)

        new_topic_btn = ttk.Button(
            button_container,
            text="Choose New Topic",
            command=self.on_new_topic,
            style='Primary.TButton'
        )
        new_topic_btn.grid(row=0, column=2, padx=10)

        quit_btn = ttk.Button(
            button_container,
            text="Quit",
            command=self.on_quit,
            style='Secondary.TButton'
        )
        quit_btn.grid(row=0, column=3, padx=10)

        # Title with completion status - pack AFTER buttons so it appears at top
        if self.results['perfect_game']:
            title_text = "🎉 PERFECT GAME! 🎉"
            title_color = '#2ECC71'
        elif self.results['completion_percentage'] >= 80:
            title_text = "Excellent Work!"
            title_color = '#3498DB'
        elif self.results['completion_percentage'] >= 50:
            title_text = "Good Effort!"
            title_color = '#F39C12'
        else:
            title_text = "Game Complete"
            title_color = '#FFFFFF'  # White for better visibility

        title = ttk.Label(self, text=title_text, font=('Arial', 28, 'bold'),
                         foreground=title_color, background='#1a1a2e')  # Match window background
        title.pack(pady=(20, 10))

        # Create scrollable container for content
        scroll_container = ttk.Frame(self)
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Create canvas and scrollbar
        canvas = tk.Canvas(scroll_container, bg='#1a1a2e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)

        # Scrollable frame inside canvas
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Create window without fixed width - will auto-size to canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Bind canvas width changes to update the frame width
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind('<Configure>', on_canvas_configure)

        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

        # Main results area inside scrollable frame - using grid for better control
        results_frame = ttk.Frame(scrollable_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Configure grid weights for 60/40 split
        results_frame.grid_columnconfigure(0, weight=3)  # Grid takes 60%
        results_frame.grid_columnconfigure(1, weight=2)  # Stats takes 40%
        results_frame.grid_rowconfigure(0, weight=1)

        # Left side - Grid showing unfound words
        left_frame = ttk.Frame(results_frame)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))

        # Grid section
        grid_label = ttk.Label(left_frame, text="Words Location (Missed words shown in color)",
                              style='Header.TLabel')
        grid_label.pack(pady=(0, 10))

        self.grid_widget = LetterGridWidget(
            left_frame,
            self.game_grid,
            lambda coords: None  # No-op callback since game is over
        )
        self.grid_widget.pack(pady=10, anchor='center')

        # Show all words on the grid (both found and unfound)
        # First show found words
        for word in self.game_grid.discovered_words:
            self.grid_widget.mark_word_discovered(word)

        # Then show unfound words in different color
        if len(self.game_grid.discovered_words) < len(self.game_grid.solution):
            self.grid_widget.show_all_unfound_words()

        # Right side - Stats and word breakdown
        right_frame = ttk.Frame(results_frame)
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))

        # Stats section
        stats_frame = ttk.LabelFrame(right_frame, text="Game Statistics", padding=15)
        stats_frame.pack(fill=tk.X, pady=(0, 15))

        self._create_stats_display(stats_frame)

        # Word breakdown section
        breakdown_frame = ttk.LabelFrame(right_frame, text="Word Breakdown", padding=15)
        breakdown_frame.pack(fill=tk.BOTH, expand=True)

        self._create_word_breakdown(breakdown_frame)

    def _create_stats_display(self, parent):
        """Create the statistics display.

        Args:
            parent: Parent widget.
        """
        # Create grid layout for stats
        stats_grid = ttk.Frame(parent)
        stats_grid.pack(fill=tk.X)

        # Words found
        ttk.Label(stats_grid, text="Words Found:", style='Info.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=5
        )
        ttk.Label(stats_grid,
                 text=f"{self.results['found_words']} / {self.results['total_words']}",
                 style='Header.TLabel').grid(
            row=0, column=1, sticky=tk.E, padx=10, pady=5
        )

        # Completion percentage
        ttk.Label(stats_grid, text="Completion:", style='Info.TLabel').grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=5
        )
        ttk.Label(stats_grid,
                 text=f"{self.results['completion_percentage']:.1f}%",
                 style='Header.TLabel').grid(
            row=1, column=1, sticky=tk.E, padx=10, pady=5
        )

        # Total score
        ttk.Label(stats_grid, text="Score:", style='Info.TLabel').grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=5
        )
        ttk.Label(stats_grid,
                 text=str(self.results['total_score']),
                 style='Header.TLabel').grid(
            row=2, column=1, sticky=tk.E, padx=10, pady=5
        )

        # Time (removed Rating row)
        elapsed = self.results.get('elapsed_time', 0)
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        ttk.Label(stats_grid, text="Time:", style='Info.TLabel').grid(
            row=3, column=0, sticky=tk.W, padx=10, pady=5
        )
        ttk.Label(stats_grid,
                 text=f"{minutes}:{seconds:02d}",
                 style='Header.TLabel').grid(
            row=3, column=1, sticky=tk.E, padx=10, pady=5
        )

        # Configure column weights
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)

    def _create_word_breakdown(self, parent):
        """Create the word breakdown display.

        Args:
            parent: Parent widget.
        """
        # Create two columns for found and unfound words using grid for equal sizing
        columns_frame = ttk.Frame(parent)
        columns_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid columns with equal weight
        columns_frame.grid_columnconfigure(0, weight=1)
        columns_frame.grid_columnconfigure(1, weight=1)
        columns_frame.grid_rowconfigure(0, weight=0)  # Header row
        columns_frame.grid_rowconfigure(1, weight=1)  # List row

        # Found words column
        ttk.Label(columns_frame, text="✓ Found Words", style='Header.TLabel').grid(
            row=0, column=0, pady=5, sticky='w'
        )

        found_frame = ttk.Frame(columns_frame)
        found_frame.grid(row=1, column=0, sticky='nsew', padx=(0, 5))

        found_scroll = ttk.Scrollbar(found_frame)
        found_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        found_list = tk.Listbox(found_frame, yscrollcommand=found_scroll.set,
                               font=('Arial', 10), bg='#D5F4E6', fg='#000000', selectmode=tk.NONE)
        found_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        found_scroll.config(command=found_list.yview)

        for word in sorted(self.game_grid.discovered_words):
            found_list.insert(tk.END, word)

        # Unfound words column
        ttk.Label(columns_frame, text="✗ Missed Words", style='Header.TLabel').grid(
            row=0, column=1, pady=5, sticky='w', padx=(5, 0)
        )

        unfound_frame = ttk.Frame(columns_frame)
        unfound_frame.grid(row=1, column=1, sticky='nsew', padx=(5, 0))

        unfound_scroll = ttk.Scrollbar(unfound_frame)
        unfound_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        unfound_list = tk.Listbox(unfound_frame, yscrollcommand=unfound_scroll.set,
                                  font=('Arial', 10), bg='#FADBD8', fg='#000000', selectmode=tk.NONE)
        unfound_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        unfound_scroll.config(command=unfound_list.yview)

        # Get unfound words
        all_words = {p.word for p in self.game_grid.solution}
        unfound_words = all_words - self.game_grid.discovered_words

        for word in sorted(unfound_words):
            unfound_list.insert(tk.END, word)
