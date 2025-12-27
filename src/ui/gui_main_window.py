"""Main GUI window for the themed word search game."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from ..models.core import Game, Grid, GameSettings
from .video_background import VideoBackground
from .background_music import BackgroundMusicManager


class MainWindow(tk.Tk):
    """Main application window for the word search game."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Window configuration
        self.title("Talron Word Search Game")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # Configure window icon and styling
        self._configure_window()

        # Current game state
        self.current_screen = None
        self.game_controller = None

        # Background music manager
        self.background_music = BackgroundMusicManager()

        # Create video background using place to fill entire window
        self.video_background = VideoBackground(self, bg='#1a1a2e')
        self.video_background.place(x=0, y=0, relwidth=1, relheight=1)

        # Configure grid weights for responsive layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Screens will be placed directly on the video_background canvas
        # Store reference for BaseScreen to use
        self.main_container_frame = self.video_background

        # Start background music
        if self.background_music.is_available():
            self.background_music.play()
            self._create_music_control()

    def _configure_window(self):
        """Configure window appearance and behavior."""
        # Set color scheme
        self.configure(bg='#1a1a2e')

        # Configure styles
        style = ttk.Style(self)
        style.theme_use('clam')

        # Transparent frame style - use actual color that matches video background
        style.configure('Transparent.TFrame',
                       background='#1a1a2e')

        # Default TFrame style to match background
        style.configure('TFrame',
                       background='#1a1a2e')

        # Enhanced title style with transparent background
        style.configure('Title.TLabel',
                       font=('Segoe UI', 32, 'bold'),
                       foreground='#ffffff',
                       background='#1a1a2e')

        # Modern header style
        style.configure('Header.TLabel',
                       font=('Segoe UI', 18, 'bold'),
                       foreground='#ecf0f1',
                       background='#1a1a2e')

        # Refined info label style
        style.configure('Info.TLabel',
                       font=('Segoe UI', 13),
                       foreground='#bdc3c7',
                       background='#1a1a2e')

        # Modern primary button with rounded corners
        style.configure('Primary.TButton',
                       font=('Segoe UI', 13, 'bold'),
                       padding=12,
                       relief='flat',
                       borderwidth=0)
        style.map('Primary.TButton',
                 background=[('active', '#3498db'), ('!active', '#2980b9')],
                 foreground=[('active', '#ffffff'), ('!active', '#ecf0f1')])

        # Secondary button style with rounded corners
        style.configure('Secondary.TButton',
                       font=('Segoe UI', 11),
                       padding=8,
                       relief='flat',
                       borderwidth=0)
        style.map('Secondary.TButton',
                 background=[('active', '#95a5a6'), ('!active', '#7f8c8d')],
                 foreground=[('active', '#ffffff'), ('!active', '#ecf0f1')])

        # Set window protocol for closing
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Bind keyboard shortcuts
        self.bind('<Escape>', lambda e: self._on_closing())
        self.bind('<F1>', lambda e: self._show_help())

    def _create_music_control(self):
        """Create music control button."""
        # Store reference for screens to access
        music_icon = "🎵" if not self.background_music.is_muted else "🔇"
        self.music_button = tk.Button(
            self,
            text=music_icon,
            command=self._toggle_music,
            font=('Segoe UI', 16),
            bg='#2c3e50',
            fg='#ecf0f1',
            relief='flat',
            bd=0,
            padx=10,
            pady=5,
            cursor='hand2',
            activebackground='#34495e',
            activeforeground='#ffffff'
        )
        # Music button will be placed by individual screens next to their help button
        # Don't place it here - let screens control placement

    def _toggle_music(self):
        """Toggle background music mute."""
        self.background_music.toggle_mute()
        music_icon = "🎵" if not self.background_music.is_muted else "🔇"
        self.music_button.config(text=music_icon)

    def _on_closing(self):
        """Handle window closing event."""
        if messagebox.askokcancel("Quit", "Do you want to quit the game?"):
            # Cleanup resources
            self.video_background.stop()
            self.background_music.cleanup()
            self.destroy()

    def _show_help(self):
        """Show help dialog with game instructions."""
        help_text = """THEMED WORD SEARCH GAME - HELP

OBJECTIVE:
Find all hidden words in the grid before time runs out!

HOW TO PLAY:
• Click and drag across adjacent letters to form words
• Words can go in any direction (horizontal, vertical, diagonal)
• Letters must be adjacent (including diagonally)
• Release mouse to submit your selection

GAME FEATURES:
• Hints: Use hints to get clues about word locations
• Sound: Toggle sound effects on/off during gameplay
• Pause: Pause the game at any time
• Different difficulty levels with varying grid sizes and time limits

KEYBOARD SHORTCUTS:
• ESC - Close window/Quit game
• F1 - Show this help dialog

SCORING:
• Find more words for higher scores
• Complete all words for a perfect game!
• Bonus points for speed and difficulty level

WORD TYPES:
• Characters - Names of characters from the topic
• Defining - Words that define or relate to the topic

Good luck and have fun!"""

        messagebox.showinfo("Help - How to Play", help_text)

    def show_screen(self, screen_widget):
        """Show a new screen, hiding the current one.

        Args:
            screen_widget: The widget to display as the current screen.
        """
        # Hide current screen
        if self.current_screen:
            if hasattr(self.current_screen, 'place_forget'):
                self.current_screen.place_forget()

        # Show new screen using place on top of video background
        self.current_screen = screen_widget
        self.current_screen.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.95, relheight=0.95)

    def clear_screen(self):
        """Clear the current screen."""
        if self.current_screen:
            if hasattr(self.current_screen, 'place_forget'):
                self.current_screen.place_forget()
            self.current_screen = None

    def set_game_controller(self, controller):
        """Set the game controller for the application.

        Args:
            controller: GameController instance.
        """
        self.game_controller = controller

    def show_error(self, title: str, message: str):
        """Show an error dialog.

        Args:
            title: Error dialog title.
            message: Error message to display.
        """
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str):
        """Show an information dialog.

        Args:
            title: Info dialog title.
            message: Info message to display.
        """
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str):
        """Show a warning dialog.

        Args:
            title: Warning dialog title.
            message: Warning message to display.
        """
        messagebox.showwarning(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        """Show a yes/no dialog.

        Args:
            title: Dialog title.
            message: Question to ask.

        Returns:
            True if yes, False if no.
        """
        return messagebox.askyesno(title, message)


class BaseScreen(tk.Frame):
    """Base class for all game screens."""

    def __init__(self, parent: MainWindow):
        """Initialize the base screen.

        Args:
            parent: Parent MainWindow instance.
        """
        # Use tk.Frame with background matching video background
        super().__init__(parent.main_container_frame, bg='#1a1a2e')
        self.parent = parent
        self.game_controller = parent.game_controller

    def show(self):
        """Show this screen."""
        self.parent.show_screen(self)

    def create_title(self, text: str) -> ttk.Label:
        """Create a title label.

        Args:
            text: Title text.

        Returns:
            Configured title label.
        """
        label = ttk.Label(self, text=text, style='Title.TLabel')
        return label

    def create_header(self, text: str) -> ttk.Label:
        """Create a header label.

        Args:
            text: Header text.

        Returns:
            Configured header label.
        """
        label = ttk.Label(self, text=text, style='Header.TLabel')
        return label

    def create_button(self, text: str, command: Callable, style: str = 'Primary.TButton') -> ttk.Button:
        """Create a button with themed appearance.

        Args:
            text: Button text.
            command: Button click handler.
            style: Button style ('Primary.TButton' or 'Secondary.TButton').

        Returns:
            Configured button.
        """
        button = ttk.Button(self, text=text, command=command, style=style)
        return button
