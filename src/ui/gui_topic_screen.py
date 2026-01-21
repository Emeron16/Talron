"""Topic and subtopic selection screen for GUI."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from .gui_main_window import BaseScreen, MainWindow
from ..data.word_database import WordDatabase


class TopicSelectionScreen(BaseScreen):
    """Screen for selecting game topic and subtopic."""

    def __init__(self, parent: MainWindow, word_database: WordDatabase,
                 on_selection_complete: Callable[[str, str], None],
                 achievement_manager=None):
        """Initialize the topic selection screen.

        Args:
            parent: Parent MainWindow instance.
            word_database: Word database for available topics.
            on_selection_complete: Callback when topic and subtopic are selected.
            achievement_manager: Optional AchievementManager for displaying stars.
        """
        super().__init__(parent)
        self.word_database = word_database
        self.on_selection_complete = on_selection_complete
        self.achievement_manager = achievement_manager

        self.selected_topic: Optional[str] = None
        self.selected_subtopic: Optional[str] = None

        # Store button references for highlighting
        self.topic_buttons = {}
        self.subtopic_buttons = {}

        # Store current subtopics for dynamic resizing
        self.current_subtopics = []

        self._create_widgets()

        # Bind to window resize for dynamic column calculation
        self.bind('<Configure>', self._on_window_resize)

    def _create_widgets(self):
        """Create the screen widgets."""
        # Navigation buttons - pack at bottom FIRST to reserve space
        nav_container = ttk.Frame(self)
        nav_container.pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=20)

        nav_frame = ttk.Frame(nav_container)
        nav_frame.pack(fill=tk.X)

        # Configure grid to ensure buttons always visible
        nav_frame.grid_columnconfigure(0, weight=0)  # Quit button
        nav_frame.grid_columnconfigure(1, weight=0)  # Help button
        nav_frame.grid_columnconfigure(2, weight=0)  # Music button
        nav_frame.grid_columnconfigure(3, weight=0)  # Reset Achievements button
        nav_frame.grid_columnconfigure(4, weight=1)  # Spacer
        nav_frame.grid_columnconfigure(5, weight=0)  # Continue button

        # Create buttons with nav_frame as parent (not self) to avoid geometry manager conflict
        back_button = ttk.Button(
            nav_frame,
            text="← Quit",
            command=self._on_quit,
            style='Secondary.TButton'
        )
        back_button.grid(row=0, column=0, padx=5, sticky='w')

        # Help button
        help_button = ttk.Button(
            nav_frame,
            text="Help (F1)",
            command=self.show_help_popup,
            style='Secondary.TButton'
        )
        help_button.grid(row=0, column=1, padx=5, sticky='w')

        # Music button (if available)
        if hasattr(self.parent, 'music_button') and self.parent.music_button:
            self.parent.music_button.place_forget()  # Remove from previous position
            # Recreate as ttk button for consistency
            music_icon = "🎵 Music" if not self.parent.background_music.is_muted else "🔇 Music"
            music_btn = ttk.Button(
                nav_frame,
                text=music_icon,
                command=self._toggle_music_wrapper,
                style='Secondary.TButton'
            )
            music_btn.grid(row=0, column=2, padx=5, sticky='w')
            self.music_display_button = music_btn

        # Reset Achievements button (only if achievement manager exists)
        if self.achievement_manager:
            reset_button = ttk.Button(
                nav_frame,
                text="Reset Achievements",
                command=self._on_reset_achievements,
                style='Secondary.TButton'
            )
            reset_button.grid(row=0, column=3, padx=5, sticky='w')

        self.continue_button = ttk.Button(
            nav_frame,
            text="Continue to Settings →",
            command=self._on_continue,
            style='Primary.TButton'
        )
        self.continue_button.grid(row=0, column=5, padx=5, sticky='e')
        self.continue_button.configure(state='disabled')

        # Title - pack after nav
        title = self.create_title("Select Your Game Theme")
        title.pack(pady=20)

        # Main content frame - pack after title to fill remaining space
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 20))

        # Topic selection frame
        topic_frame = ttk.LabelFrame(content_frame, text="Step 1: Choose a Topic", padding=20)
        topic_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        self.topic_buttons_frame = ttk.Frame(topic_frame)
        self.topic_buttons_frame.pack(fill=tk.BOTH, expand=True)

        self._create_topic_buttons()

        # Subtopic selection frame with scrollbar
        self.subtopic_frame = ttk.LabelFrame(content_frame, text="Step 2: Choose a Subtopic", padding=20)
        self.subtopic_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas and scrollbar for subtopics
        self.subtopic_canvas = tk.Canvas(self.subtopic_frame, bg='#1a1a2e', highlightthickness=0)
        subtopic_scrollbar = ttk.Scrollbar(self.subtopic_frame, orient="vertical", command=self.subtopic_canvas.yview)
        self.subtopic_buttons_frame = ttk.Frame(self.subtopic_canvas)

        self.subtopic_buttons_frame.bind(
            "<Configure>",
            lambda e: self.subtopic_canvas.configure(scrollregion=self.subtopic_canvas.bbox("all"))
        )

        self.canvas_window = self.subtopic_canvas.create_window((0, 0), window=self.subtopic_buttons_frame, anchor="nw")
        self.subtopic_canvas.configure(yscrollcommand=subtopic_scrollbar.set)

        # Bind canvas width changes to update the frame width
        self.subtopic_canvas.bind('<Configure>', self._on_canvas_configure)

        self.subtopic_canvas.pack(side="left", fill=tk.BOTH, expand=True)
        subtopic_scrollbar.pack(side="right", fill="y")

    def _on_canvas_configure(self, event):
        """Handle canvas resize to update frame width.

        Args:
            event: Configure event.
        """
        # Set the canvas window width to match canvas width
        canvas_width = event.width
        if canvas_width > 1:
            self.subtopic_canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _toggle_music_wrapper(self):
        """Wrapper to toggle music and update button text."""
        self.parent._toggle_music()
        if hasattr(self, 'music_display_button'):
            music_icon = "🎵 Music" if not self.parent.background_music.is_muted else "🔇 Music"
            self.music_display_button.config(text=music_icon)

    def _create_topic_buttons(self):
        """Create buttons for each available topic."""
        topics = self.word_database.get_topics()

        for i, topic in enumerate(topics):
            btn = ttk.Button(
                self.topic_buttons_frame,
                text=topic.title(),
                command=lambda t=topic: self._on_topic_selected(t),
                style='Secondary.TButton'
            )
            btn.grid(row=i//3, column=i%3, padx=10, pady=10, sticky='ew')
            self.topic_buttons[topic] = btn

        # Configure column weights for equal spacing
        for i in range(3):
            self.topic_buttons_frame.grid_columnconfigure(i, weight=1)

    def _on_topic_selected(self, topic: str):
        """Handle topic selection.

        Args:
            topic: Selected topic name.
        """
        self.selected_topic = topic
        self.selected_subtopic = None

        # Highlight selected topic button
        self._highlight_selected_topic(topic)

        # Update subtopic buttons
        self._create_subtopic_buttons(topic)

        # Schedule a recalculation after widgets are fully rendered
        # Use longer delay to ensure canvas is properly sized
        self.after(100, lambda: self._recalculate_subtopic_layout(topic))

        # Disable continue button until subtopic is selected
        self.continue_button.configure(state='disabled')

    def _highlight_selected_topic(self, selected_topic: str):
        """Highlight the selected topic button.

        Args:
            selected_topic: Selected topic name.
        """
        for topic, btn in self.topic_buttons.items():
            if topic == selected_topic:
                btn.configure(style='Primary.TButton')
            else:
                btn.configure(style='Secondary.TButton')

    def _format_subtopic_name(self, subtopic: str) -> str:
        """Format subtopic name with proper capitalization and spacing.

        Args:
            subtopic: Raw subtopic name.

        Returns:
            Formatted subtopic name.
        """
        # Special cases mapping
        special_cases = {
            'attackontitan': 'Attack on Titan',
            'deathnote': 'Death Note',
            'fullmetalalchemist': 'Fullmetal Alchemist',
            'jujutsukaisen': 'Jujutsu Kaisen',
            'myheroacademia': 'My Hero Academia',
            'cowboybebop': 'Cowboy Bebop',
            'hunterxhunter': 'Hunter x Hunter',
            'onepunchman': 'One Punch Man',
            'onepiece': 'One Piece',
            'dragonball': 'Dragon Ball',
            'starwars': 'Star Wars',
            'harrypotter': 'Harry Potter',
            'lordoftherings': 'Lord of the Rings',
            'thematrix': 'The Matrix',
            'jamesbond': 'James Bond',
            'jurassicpark': 'Jurassic Park',
            'indianajones': 'Indiana Jones',
            'backtothefuture': 'Back to the Future',
            'missionimpossible': 'Mission Impossible',
            'thegodfather': 'The Godfather',
            'piratesofthecaribbean': 'Pirates of the Caribbean',
            'gameofthrones': 'Game of Thrones',
            'theoffice': 'The Office',
            'breakingbad': 'Breaking Bad',
            'strangerthings': 'Stranger Things',
            'thesimpsons': 'The Simpsons',
            'thesopranos': 'The Sopranos',
            'thewire': 'The Wire',
            'themandolorian': 'The Mandalorian',
            'thebigbangtheory': 'The Big Bang Theory',
        }

        # Check if we have a special case
        if subtopic.lower() in special_cases:
            return special_cases[subtopic.lower()]

        # Default: just capitalize
        return subtopic.title()

    def _format_star_display(self, achievement: dict) -> str:
        """Format star display for achievement.

        Args:
            achievement: Achievement dictionary with 'highest_star_level' and 'star_color'.

        Returns:
            Formatted star string (e.g., "⭐⭐⭐" or "☆☆").
        """
        star_level = achievement.get('highest_star_level', 0)
        star_color = achievement.get('star_color', 'none')

        # Use emoji stars for visual appeal
        # Gold: ⭐ (U+2B50) - filled star emoji
        # Silver: ☆ (U+2606) - white star
        star_char = '⭐' if star_color == 'gold' else '☆'

        return star_char * star_level

    def _create_subtopic_buttons(self, topic: str, num_columns: Optional[int] = None):
        """Create buttons for subtopics of the selected topic.

        Args:
            topic: Topic to get subtopics for.
            num_columns: Number of columns to use (auto-calculate if None).
        """
        # Get and store subtopics
        self.current_subtopics = self.word_database.get_subtopics(topic)

        # Calculate optimal number of columns based on frame width
        if num_columns is None:
            num_columns = self._calculate_optimal_columns()

        # Clear existing buttons
        for widget in self.subtopic_buttons_frame.winfo_children():
            widget.destroy()

        # Clear subtopic button references
        self.subtopic_buttons = {}

        for i, subtopic in enumerate(self.current_subtopics):
            # Check if subtopic has sufficient words
            has_words = self.word_database.has_sufficient_words(topic, subtopic)

            # Format subtopic name for display
            display_name = self._format_subtopic_name(subtopic)

            # Add stars if achievement exists
            if self.achievement_manager and self.selected_topic:
                achievement = self.achievement_manager.get_achievement(
                    self.selected_topic, subtopic
                )
                if achievement:
                    star_display = self._format_star_display(achievement)
                    display_name = f"{display_name} {star_display}"

            btn = ttk.Button(
                self.subtopic_buttons_frame,
                text=display_name,
                command=lambda st=subtopic: self._on_subtopic_selected(st),
                style='Secondary.TButton'
            )
            btn.grid(row=i//num_columns, column=i%num_columns, padx=10, pady=10, sticky='ew')

            if not has_words:
                btn.configure(state='disabled')
            else:
                # Only store reference for enabled buttons
                self.subtopic_buttons[subtopic] = btn

        # Configure column weights dynamically with uniform sizing
        for i in range(num_columns):
            self.subtopic_buttons_frame.grid_columnconfigure(i, weight=1, uniform='subtopic_col')

    def _calculate_optimal_columns(self) -> int:
        """Calculate optimal number of columns based on available width.

        Returns:
            Number of columns to use (minimum 2, maximum 6).
        """
        # Update to get current width from the canvas (not the frame inside it)
        self.subtopic_canvas.update_idletasks()
        canvas_width = self.subtopic_canvas.winfo_width()

        # If canvas width not available, try getting from subtopic_frame
        if canvas_width <= 1:
            self.subtopic_frame.update_idletasks()
            frame_width = self.subtopic_frame.winfo_width()
            # Subtract padding from LabelFrame (20 on each side = 40 total)
            canvas_width = frame_width - 40 if frame_width > 40 else 800

        # Also subtract scrollbar width when getting from canvas
        if canvas_width > 20:
            canvas_width -= 20

        # Each button needs ~150 pixels minimum (button + padding)
        button_width = 150
        optimal_columns = max(2, min(6, canvas_width // button_width))

        return optimal_columns

    def _recalculate_subtopic_layout(self, topic: str):
        """Recalculate subtopic layout after widgets are rendered.

        Args:
            topic: Topic to recalculate layout for.
        """
        if not self.current_subtopics or self.selected_topic != topic:
            return

        # Force update to get accurate dimensions
        self.subtopic_canvas.update_idletasks()
        self.subtopic_frame.update_idletasks()
        canvas_width = self.subtopic_canvas.winfo_width()

        # Only recalculate if we now have valid dimensions
        if canvas_width > 1:
            new_columns = self._calculate_optimal_columns()
            current_columns = len([w for w in self.subtopic_buttons_frame.grid_slaves(row=0)])

            # Recreate if column count changed OR if we initially had invalid dimensions
            # This ensures proper layout even if column count happens to be the same
            if current_columns > 0 and new_columns != current_columns:
                self._create_subtopic_buttons(topic, num_columns=new_columns)
                # Restore selection highlighting if there was one
                if self.selected_subtopic:
                    self._highlight_selected_subtopic(self.selected_subtopic)
            elif current_columns == 0:
                # No buttons found, recreate anyway
                self._create_subtopic_buttons(topic, num_columns=new_columns)

    def _on_window_resize(self, event):
        """Handle window resize to adjust subtopic columns dynamically.

        Args:
            event: Configure event.
        """
        # Only recalculate if we have subtopics displayed and event is for this widget
        if event.widget == self and self.current_subtopics and self.selected_topic:
            new_columns = self._calculate_optimal_columns()
            # Only recreate if column count changed
            current_columns = len([w for w in self.subtopic_buttons_frame.grid_slaves(row=0)])
            if current_columns > 0 and new_columns != current_columns:
                self._create_subtopic_buttons(self.selected_topic, num_columns=new_columns)
                # Restore selection highlighting if there was one
                if self.selected_subtopic:
                    self._highlight_selected_subtopic(self.selected_subtopic)

    def _on_subtopic_selected(self, subtopic: str):
        """Handle subtopic selection.

        Args:
            subtopic: Selected subtopic name.
        """
        self.selected_subtopic = subtopic

        # Highlight selected subtopic button
        self._highlight_selected_subtopic(subtopic)

        # Enable continue button
        self.continue_button.configure(state='normal')

    def _highlight_selected_subtopic(self, selected_subtopic: str):
        """Highlight the selected subtopic button.

        Args:
            selected_subtopic: Selected subtopic name.
        """
        for subtopic, btn in self.subtopic_buttons.items():
            if subtopic == selected_subtopic:
                btn.configure(style='Primary.TButton')
            else:
                btn.configure(style='Secondary.TButton')

    def _on_continue(self):
        """Handle continue button click."""
        if self.selected_topic and self.selected_subtopic:
            self.on_selection_complete(self.selected_topic, self.selected_subtopic)

    def _on_quit(self):
        """Handle quit button click."""
        if self.parent.ask_yes_no("Quit", "Are you sure you want to quit?"):
            self.parent.destroy()

    def _on_reset_achievements(self):
        """Handle reset achievements button click."""
        if not self.achievement_manager:
            return

        # Show confirmation popup
        self._show_reset_confirmation_popup()

    def _show_reset_confirmation_popup(self):
        """Display reset confirmation in an overlay window."""
        # Create overlay frame
        overlay = tk.Frame(self, bg='#000000', bd=2, relief=tk.RAISED)
        overlay.place(relx=0.5, rely=0.5, anchor='center', width=500, height=300)

        # Inner frame with dark background
        inner_frame = tk.Frame(overlay, bg='#1a1a2e', padx=30, pady=30)
        inner_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            inner_frame,
            text="⚠️ Reset Achievements",
            style='Header.TLabel',
            font=('Segoe UI', 18, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # Warning message
        message_label = ttk.Label(
            inner_frame,
            text="Are you sure you want to reset all achievements?\n\n"
                 "This will delete all your progress and cannot be undone.",
            font=('Segoe UI', 12),
            justify=tk.CENTER,
            wraplength=400
        )
        message_label.pack(pady=(0, 30))

        # Button frame
        button_frame = tk.Frame(inner_frame, bg='#1a1a2e')
        button_frame.pack()

        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=lambda: overlay.destroy(),
            style='Secondary.TButton'
        )
        cancel_button.pack(side=tk.LEFT, padx=10)

        # Confirm button
        confirm_button = ttk.Button(
            button_frame,
            text="Reset All Achievements",
            command=lambda: self._perform_reset(overlay),
            style='Primary.TButton'
        )
        confirm_button.pack(side=tk.LEFT, padx=10)

        # Bind Escape to cancel
        overlay.bind('<Escape>', lambda e: overlay.destroy())
        overlay.focus_set()

    def _perform_reset(self, overlay):
        """Perform the actual reset and show success message.

        Args:
            overlay: The confirmation overlay to destroy.
        """
        overlay.destroy()

        success = self.achievement_manager.reset_achievements()
        if success:
            # Refresh the display to remove stars
            if self.selected_topic:
                self._create_subtopic_buttons(self.selected_topic)
            self._show_reset_success_popup()
        else:
            self._show_reset_error_popup()

    def _show_reset_success_popup(self):
        """Display success message in an overlay window."""
        # Create overlay frame
        overlay = tk.Frame(self, bg='#000000', bd=2, relief=tk.RAISED)
        overlay.place(relx=0.5, rely=0.5, anchor='center', width=400, height=200)

        # Inner frame with dark background
        inner_frame = tk.Frame(overlay, bg='#1a1a2e', padx=30, pady=30)
        inner_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            inner_frame,
            text="✓ Reset Complete",
            style='Header.TLabel',
            font=('Segoe UI', 18, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # Message
        message_label = ttk.Label(
            inner_frame,
            text="All achievements have been reset.",
            font=('Segoe UI', 12),
            justify=tk.CENTER
        )
        message_label.pack(pady=(0, 20))

        # Close button
        close_button = ttk.Button(
            inner_frame,
            text="OK",
            command=lambda: overlay.destroy(),
            style='Primary.TButton'
        )
        close_button.pack()

        # Auto-dismiss after 3 seconds
        self.after(3000, lambda: overlay.destroy() if overlay.winfo_exists() else None)

        # Bind Escape and Enter to close
        overlay.bind('<Escape>', lambda e: overlay.destroy())
        overlay.bind('<Return>', lambda e: overlay.destroy())
        overlay.focus_set()

    def _show_reset_error_popup(self):
        """Display error message in an overlay window."""
        # Create overlay frame
        overlay = tk.Frame(self, bg='#000000', bd=2, relief=tk.RAISED)
        overlay.place(relx=0.5, rely=0.5, anchor='center', width=400, height=200)

        # Inner frame with dark background
        inner_frame = tk.Frame(overlay, bg='#1a1a2e', padx=30, pady=30)
        inner_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            inner_frame,
            text="❌ Error",
            style='Header.TLabel',
            font=('Segoe UI', 18, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # Message
        message_label = ttk.Label(
            inner_frame,
            text="Failed to reset achievements.\nPlease check the console for details.",
            font=('Segoe UI', 12),
            justify=tk.CENTER
        )
        message_label.pack(pady=(0, 20))

        # Close button
        close_button = ttk.Button(
            inner_frame,
            text="OK",
            command=lambda: overlay.destroy(),
            style='Primary.TButton'
        )
        close_button.pack()

        # Bind Escape and Enter to close
        overlay.bind('<Escape>', lambda e: overlay.destroy())
        overlay.bind('<Return>', lambda e: overlay.destroy())
        overlay.focus_set()

    def reset(self):
        """Reset the screen to initial state."""
        self.selected_topic = None
        self.selected_subtopic = None
        self.continue_button.configure(state='disabled')

        # Clear subtopic buttons
        for widget in self.subtopic_buttons_frame.winfo_children():
            widget.destroy()
