"""Game settings configuration screen for GUI."""

import tkinter as tk
from tkinter import ttk
from typing import Callable
from .gui_main_window import BaseScreen, MainWindow
from ..models.core import GameSettings
from .hint_system import DifficultySettings


class SettingsScreen(BaseScreen):
    """Screen for configuring game settings."""

    def __init__(self, parent: MainWindow, on_settings_complete: Callable[[GameSettings], None]):
        """Initialize the settings screen.

        Args:
            parent: Parent MainWindow instance.
            on_settings_complete: Callback when settings are confirmed.
        """
        super().__init__(parent)
        self.on_settings_complete = on_settings_complete
        self.back_callback = None

        # Configure slider style with blue color
        style = ttk.Style()
        style.configure('Blue.Horizontal.TScale', background='#2980b9')
        style.map('Blue.Horizontal.TScale',
                 background=[('active', '#3498db'), ('!active', '#2980b9')])

        # Topic information
        self.current_topic = None
        self.current_subtopic = None

        # Default settings
        self.grid_size_var = tk.IntVar(value=12)
        self.time_limit_var = tk.IntVar(value=5)  # Minutes
        self.no_time_limit_var = tk.BooleanVar(value=False)  # No time limit option
        self.difficulty_var = tk.StringVar(value='custom')
        self.max_hints_var = tk.IntVar(value=3)

        self._create_widgets()

    def _create_widgets(self):
        """Create the screen widgets."""
        # Navigation buttons - pack at bottom FIRST to reserve space
        nav_container = ttk.Frame(self)
        nav_container.pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=20)

        nav_frame = ttk.Frame(nav_container)
        nav_frame.pack(fill=tk.X)

        # Configure grid to ensure buttons always visible
        nav_frame.grid_columnconfigure(0, weight=0)  # Back button
        nav_frame.grid_columnconfigure(1, weight=0)  # Help button
        nav_frame.grid_columnconfigure(2, weight=0)  # Music button
        nav_frame.grid_columnconfigure(3, weight=1)  # Spacer
        nav_frame.grid_columnconfigure(4, weight=0)  # Start button

        # Create buttons with nav_frame as parent (not self) to avoid geometry manager conflict
        back_button = ttk.Button(
            nav_frame,
            text="← Back to Topics",
            command=self._on_back,
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

        start_button = ttk.Button(
            nav_frame,
            text="Start Game →",
            command=self._on_start_game,
            style='Primary.TButton'
        )
        start_button.grid(row=0, column=4, padx=5, sticky='e')

        # Title (will be updated when topic is set)
        self.title_label = self.create_title("Game Settings")
        self.title_label.pack(pady=20)

        # Subtopic info (will be updated when subtopic is set)
        self.info_label = ttk.Label(self, text="Configure your game difficulty and time constraints",
                        style='Info.TLabel')
        self.info_label.pack(pady=10)

        # Create container for scrollable content
        scroll_container = ttk.Frame(self)
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Create canvas and scrollbar for settings
        self.settings_canvas = tk.Canvas(scroll_container, bg='#1a1a2e', highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.settings_canvas.yview)

        # Main settings frame inside canvas
        settings_frame = ttk.Frame(self.settings_canvas)

        settings_frame.bind(
            "<Configure>",
            lambda e: self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all"))
        )

        self.canvas_window = self.settings_canvas.create_window((0, 0), window=settings_frame, anchor="nw")
        self.settings_canvas.configure(yscrollcommand=settings_scrollbar.set)

        # Bind canvas width changes to update the frame width
        self.settings_canvas.bind('<Configure>', self._on_canvas_configure)

        # Enable mouse wheel scrolling
        self.settings_canvas.bind('<Enter>', self._bind_mousewheel)
        self.settings_canvas.bind('<Leave>', self._unbind_mousewheel)

        self.settings_canvas.pack(side="left", fill=tk.BOTH, expand=True)
        settings_scrollbar.pack(side="right", fill="y")

        # Add padding frame inside settings_frame for better spacing
        content_frame = ttk.Frame(settings_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=60, pady=10)

        # Difficulty preset buttons
        self._create_difficulty_presets(content_frame)

        # Add spacing (reduced to fit content)
        ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Grid size setting
        self._create_grid_size_setting(content_frame)

        # Add spacing
        ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Time limit setting
        self._create_time_limit_setting(content_frame)

        # Add spacing
        ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Hints setting
        self._create_hints_setting(content_frame)

        # Settings summary (reduced padding)
        self.summary_label = ttk.Label(content_frame, text="", style='Info.TLabel',
                                      justify=tk.CENTER)
        self.summary_label.pack(pady=15)
        self._update_summary()

    def _on_canvas_configure(self, event):
        """Handle canvas resize to update frame width.

        Args:
            event: Configure event.
        """
        # Set the canvas window width to match canvas width
        canvas_width = event.width
        if canvas_width > 1:
            self.settings_canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _bind_mousewheel(self, event):
        """Bind mousewheel to canvas scrolling.

        Args:
            event: Enter event.
        """
        # Bind mousewheel for different platforms
        self.settings_canvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows/Mac
        self.settings_canvas.bind_all("<Button-4>", self._on_mousewheel)    # Linux scroll up
        self.settings_canvas.bind_all("<Button-5>", self._on_mousewheel)    # Linux scroll down

    def _unbind_mousewheel(self, event):
        """Unbind mousewheel from canvas scrolling.

        Args:
            event: Leave event.
        """
        self.settings_canvas.unbind_all("<MouseWheel>")
        self.settings_canvas.unbind_all("<Button-4>")
        self.settings_canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling.

        Args:
            event: Mouse wheel event.
        """
        # Determine scroll direction based on platform
        if event.num == 5 or event.delta < 0:
            # Scroll down
            self.settings_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            # Scroll up
            self.settings_canvas.yview_scroll(-1, "units")

    def _toggle_music_wrapper(self):
        """Wrapper to toggle music and update button text."""
        self.parent._toggle_music()
        if hasattr(self, 'music_display_button'):
            music_icon = "🎵 Music" if not self.parent.background_music.is_muted else "🔇 Music"
            self.music_display_button.config(text=music_icon)

    def _create_difficulty_presets(self, parent):
        """Create difficulty preset buttons.

        Args:
            parent: Parent widget.
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=10)

        label = ttk.Label(frame, text="Quick Presets", style='Header.TLabel')
        label.pack(anchor=tk.W, pady=5)

        desc = ttk.Label(frame,
                        text="Choose a difficulty preset or customize below",
                        style='Info.TLabel')
        desc.pack(anchor=tk.W, pady=2)

        # Buttons frame
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        # Store difficulty buttons for highlighting
        self.difficulty_buttons = {}

        difficulties = DifficultySettings.get_available_difficulties()
        for i, diff in enumerate(difficulties):
            btn = ttk.Button(
                buttons_frame,
                text=diff.capitalize(),
                command=lambda d=diff: self._apply_difficulty_preset(d),
                style='Secondary.TButton',
                width=12
            )
            btn.grid(row=0, column=i, padx=5, sticky='ew')
            self.difficulty_buttons[diff] = btn

        # Configure columns for equal spacing
        for i in range(len(difficulties)):
            buttons_frame.grid_columnconfigure(i, weight=1)

    def _apply_difficulty_preset(self, difficulty: str):
        """Apply a difficulty preset.

        Args:
            difficulty: Name of difficulty preset.
        """
        settings = DifficultySettings.get_difficulty_settings(difficulty)

        self.grid_size_var.set(settings['grid_size'])
        self.time_limit_var.set(settings['time_limit'] // 60)
        self.max_hints_var.set(settings['max_hints'])
        self.difficulty_var.set(difficulty)

        # Presets always have time limits, so turn off no time limit toggle
        self.no_time_limit_var.set(False)
        self.time_limit_slider.config(state='normal')
        self._draw_toggle_button()  # Redraw toggle in OFF position

        # Highlight selected difficulty button
        self._highlight_selected_difficulty(difficulty)

        self._on_setting_changed()

    def _highlight_selected_difficulty(self, selected_diff: str):
        """Highlight the selected difficulty button.

        Args:
            selected_diff: Selected difficulty name.
        """
        for diff, btn in self.difficulty_buttons.items():
            if diff == selected_diff:
                btn.configure(style='Primary.TButton')
            else:
                btn.configure(style='Secondary.TButton')

    def _create_hints_setting(self, parent):
        """Create hints setting controls.

        Args:
            parent: Parent widget.
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=10)

        label = ttk.Label(frame, text="Hints Available", style='Header.TLabel')
        label.pack(anchor=tk.W, pady=5)

        desc = ttk.Label(frame,
                        text="Number of hints available during the game (0-5)",
                        style='Info.TLabel')
        desc.pack(anchor=tk.W, pady=2)

        # Slider
        slider_frame = ttk.Frame(frame)
        slider_frame.pack(fill=tk.X, pady=10)

        self.hints_slider = ttk.Scale(
            slider_frame,
            from_=0,
            to=5,
            orient=tk.HORIZONTAL,
            variable=self.max_hints_var,
            command=lambda _: self._on_setting_changed(),
            style='Blue.Horizontal.TScale'
        )
        self.hints_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Value label
        self.hints_value_label = ttk.Label(slider_frame, text="3 hints",
                                          style='Info.TLabel', width=8)
        self.hints_value_label.pack(side=tk.RIGHT)

    def _create_grid_size_setting(self, parent):
        """Create grid size setting controls.

        Args:
            parent: Parent widget.
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=10)

        # Label
        label = ttk.Label(frame, text="Grid Size", style='Header.TLabel')
        label.pack(anchor=tk.W, pady=5)

        # Description
        desc = ttk.Label(frame,
                        text="Choose grid size from 8x8 (easier) to 20x20 (harder)",
                        style='Info.TLabel')
        desc.pack(anchor=tk.W, pady=2)

        # Slider
        slider_frame = ttk.Frame(frame)
        slider_frame.pack(fill=tk.X, pady=10)

        self.grid_size_slider = ttk.Scale(
            slider_frame,
            from_=8,
            to=20,
            orient=tk.HORIZONTAL,
            variable=self.grid_size_var,
            command=lambda _: self._on_setting_changed(),
            style='Blue.Horizontal.TScale'
        )
        self.grid_size_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Value label
        self.grid_size_value_label = ttk.Label(slider_frame, text="12x12",
                                              style='Info.TLabel', width=8)
        self.grid_size_value_label.pack(side=tk.RIGHT)

    def _create_time_limit_setting(self, parent):
        """Create time limit setting controls.

        Args:
            parent: Parent widget.
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=10)

        # Label
        label = ttk.Label(frame, text="Time Limit", style='Header.TLabel')
        label.pack(anchor=tk.W, pady=5)

        # Description
        desc = ttk.Label(frame,
                        text="Set time limit from 1 minute to 30 minutes, or disable time limit",
                        style='Info.TLabel')
        desc.pack(anchor=tk.W, pady=2)

        # No time limit toggle
        toggle_frame = ttk.Frame(frame)
        toggle_frame.pack(fill=tk.X, pady=5)

        # Label for toggle
        toggle_label = ttk.Label(toggle_frame, text="No Time Limit (Play until all words are found):",
                                style='Info.TLabel')
        toggle_label.pack(side=tk.LEFT, padx=(0, 10))

        # Create custom toggle button
        self.no_time_limit_toggle = tk.Canvas(toggle_frame, width=60, height=30,
                                              bg='#1a1a2e', highlightthickness=0,
                                              cursor='hand2')
        self.no_time_limit_toggle.pack(side=tk.LEFT)

        # Draw toggle background and slider
        self._draw_toggle_button()

        # Bind click and hover events
        self.no_time_limit_toggle.bind('<Button-1>', self._toggle_no_time_limit)
        self.no_time_limit_toggle.bind('<Enter>', lambda e: self._on_toggle_hover(True))
        self.no_time_limit_toggle.bind('<Leave>', lambda e: self._on_toggle_hover(False))

        # Slider
        slider_frame = ttk.Frame(frame)
        slider_frame.pack(fill=tk.X, pady=10)

        self.time_limit_slider = ttk.Scale(
            slider_frame,
            from_=1,
            to=30,
            orient=tk.HORIZONTAL,
            variable=self.time_limit_var,
            command=lambda _: self._on_setting_changed(),
            style='Blue.Horizontal.TScale'
        )
        self.time_limit_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Value label
        self.time_limit_value_label = ttk.Label(slider_frame, text="5 min",
                                               style='Info.TLabel', width=8)
        self.time_limit_value_label.pack(side=tk.RIGHT)

    def _draw_toggle_button(self, hover=False):
        """Draw the toggle button on the canvas.

        Args:
            hover: Whether the mouse is hovering over the toggle.
        """
        # Clear canvas
        self.no_time_limit_toggle.delete('all')

        is_on = self.no_time_limit_var.get()

        # Colors with hover effect
        if is_on:
            bg_color = '#27AE60' if hover else '#2ECC71'  # Darker green on hover
        else:
            bg_color = '#7F8C8D' if hover else '#95A5A6'  # Darker gray on hover
        slider_color = '#FFFFFF'  # White slider

        # Draw background rounded rectangle
        self.no_time_limit_toggle.create_oval(0, 0, 30, 30, fill=bg_color, outline='')
        self.no_time_limit_toggle.create_oval(30, 0, 60, 30, fill=bg_color, outline='')
        self.no_time_limit_toggle.create_rectangle(15, 0, 45, 30, fill=bg_color, outline='')

        # Draw slider circle
        if is_on:
            # Slider on right (ON position)
            self.no_time_limit_toggle.create_oval(33, 3, 57, 27, fill=slider_color, outline='')
        else:
            # Slider on left (OFF position)
            self.no_time_limit_toggle.create_oval(3, 3, 27, 27, fill=slider_color, outline='')

    def _on_toggle_hover(self, entering):
        """Handle mouse hover over toggle button.

        Args:
            entering: True if mouse is entering, False if leaving.
        """
        self._draw_toggle_button(hover=entering)

    def _toggle_no_time_limit(self, event=None):
        """Toggle the no time limit setting."""
        # Toggle the variable
        self.no_time_limit_var.set(not self.no_time_limit_var.get())

        # Redraw the toggle button
        self._draw_toggle_button()

        # Update the rest of the UI
        self._on_no_time_limit_changed()

    def _on_no_time_limit_changed(self):
        """Handle no time limit toggle change."""
        no_time_limit = self.no_time_limit_var.get()

        # Enable/disable time slider based on toggle
        if no_time_limit:
            self.time_limit_slider.config(state='disabled')
            self.time_limit_value_label.config(text="Disabled")
        else:
            self.time_limit_slider.config(state='normal')
            time_minutes = int(self.time_limit_var.get())
            self.time_limit_value_label.config(text=f"{time_minutes} min")

        # Mark as custom since no preset has no time limit
        self.difficulty_var.set('custom')
        for btn in self.difficulty_buttons.values():
            btn.configure(style='Secondary.TButton')

        self._update_summary()

    def _on_setting_changed(self):
        """Handle setting value change."""
        # Update value labels
        grid_size = int(self.grid_size_var.get())
        time_minutes = int(self.time_limit_var.get())
        max_hints = int(self.max_hints_var.get())

        self.grid_size_value_label.config(text=f"{grid_size}x{grid_size}")

        # Only update time limit label if not disabled
        if not self.no_time_limit_var.get():
            self.time_limit_value_label.config(text=f"{time_minutes} min")

        self.hints_value_label.config(text=f"{max_hints} hint{'s' if max_hints != 1 else ''}")

        # Mark as custom if manually changed
        current_difficulty = self.difficulty_var.get()
        if current_difficulty != 'custom':
            # Check if settings still match the current difficulty
            expected_settings = DifficultySettings.get_difficulty_settings(current_difficulty)
            if (grid_size != expected_settings['grid_size'] or
                time_minutes != expected_settings['time_limit'] // 60 or
                max_hints != expected_settings['max_hints'] or
                self.no_time_limit_var.get()):
                self.difficulty_var.set('custom')
                # Reset all difficulty buttons to secondary style
                for btn in self.difficulty_buttons.values():
                    btn.configure(style='Secondary.TButton')

        # Update summary
        self._update_summary()

    def _update_summary(self):
        """Update the settings summary display."""
        grid_size = int(self.grid_size_var.get())
        time_minutes = int(self.time_limit_var.get())
        max_hints = int(self.max_hints_var.get())
        difficulty = self.difficulty_var.get().capitalize()
        no_time_limit = self.no_time_limit_var.get()

        summary_text = f"Difficulty: {difficulty}\n"

        # Show appropriate time text
        if no_time_limit:
            time_text = "No Time Limit"
        else:
            time_text = f"{time_minutes} minute{'s' if time_minutes != 1 else ''}"

        summary_text += f"Grid: {grid_size}x{grid_size} | Time: {time_text} | Hints: {max_hints}"

        self.summary_label.config(text=summary_text)

    def _on_start_game(self):
        """Handle start game button click."""
        grid_size = int(self.grid_size_var.get())

        # If no time limit is checked, set time_limit to 0 (unlimited)
        if self.no_time_limit_var.get():
            time_seconds = 0
        else:
            time_seconds = int(self.time_limit_var.get()) * 60

        try:
            settings = GameSettings(grid_size=grid_size, time_limit=time_seconds)
            self.on_settings_complete(settings)
        except ValueError as e:
            self.parent.show_error("Invalid Settings", str(e))

    def _on_back(self):
        """Handle back button click."""
        if self.back_callback:
            self.back_callback()

    def set_back_callback(self, callback: Callable):
        """Set callback for back button.

        Args:
            callback: Function to call when back button is clicked.
        """
        self.back_callback = callback

    def get_max_hints(self) -> int:
        """Get the configured maximum hints.

        Returns:
            Maximum number of hints.
        """
        return int(self.max_hints_var.get())

    def set_topic(self, topic: str, subtopic: str):
        """Set the selected topic and subtopic.

        Args:
            topic: Selected topic name.
            subtopic: Selected subtopic name.
        """
        self.current_topic = topic
        self.current_subtopic = subtopic

        # Update title to show topic
        self.title_label.config(text=f"Game Settings - {topic}")

        # Update info to show subtopic
        self.info_label.config(text=f"Playing: {subtopic}")

    def reset(self):
        """Reset settings to defaults."""
        self.grid_size_var.set(12)
        self.time_limit_var.set(5)
        self.no_time_limit_var.set(False)
        self.max_hints_var.set(3)
        self.difficulty_var.set('custom')

        # Re-enable time slider and redraw toggle
        self.time_limit_slider.config(state='normal')
        self._draw_toggle_button()

        self._update_summary()
