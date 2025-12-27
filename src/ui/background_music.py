"""Background music manager for GUI."""

import threading
from pathlib import Path
from typing import Optional
import platform


class BackgroundMusicManager:
    """Manages background music playback.

    To use with actual music:
    1. Place your music file in: src/ui/assets/background_music.mp3
    2. Install pygame: pip install pygame
    3. The manager will automatically detect and play the music
    """

    def __init__(self):
        """Initialize the background music manager."""
        self.music_path = Path(__file__).parent / "assets" / "background_music.mp3"
        self.is_playing = False
        self.is_muted = False
        self.volume = 0.5  # 50% volume by default

        # Try to load pygame for music playback
        self.has_pygame = self._check_pygame()

        if self.has_pygame and self.music_path.exists():
            self._setup_pygame()

    def _check_pygame(self) -> bool:
        """Check if pygame is available.

        Returns:
            True if pygame is installed, False otherwise.
        """
        try:
            import pygame
            return True
        except ImportError:
            return False

    def _setup_pygame(self):
        """Setup pygame mixer for music playback."""
        try:
            import pygame

            pygame.mixer.init()
            pygame.mixer.music.load(str(self.music_path))
            pygame.mixer.music.set_volume(self.volume)

        except Exception as e:
            print(f"Error setting up background music: {e}")
            self.has_pygame = False

    def play(self):
        """Start playing background music."""
        if self.has_pygame and self.music_path.exists():
            try:
                import pygame

                if not self.is_playing:
                    pygame.mixer.music.play(-1)  # Loop indefinitely
                    self.is_playing = True
                    if self.is_muted:
                        pygame.mixer.music.set_volume(0.0)
                    else:
                        pygame.mixer.music.set_volume(self.volume)

            except Exception as e:
                print(f"Error playing background music: {e}")

    def stop(self):
        """Stop background music."""
        if self.has_pygame and self.is_playing:
            try:
                import pygame
                pygame.mixer.music.stop()
                self.is_playing = False
            except Exception as e:
                print(f"Error stopping background music: {e}")

    def pause(self):
        """Pause background music."""
        if self.has_pygame and self.is_playing:
            try:
                import pygame
                pygame.mixer.music.pause()
            except Exception as e:
                print(f"Error pausing background music: {e}")

    def unpause(self):
        """Unpause background music."""
        if self.has_pygame and self.is_playing:
            try:
                import pygame
                pygame.mixer.music.unpause()
            except Exception as e:
                print(f"Error unpausing background music: {e}")

    def toggle_mute(self):
        """Toggle mute on/off."""
        self.is_muted = not self.is_muted

        if self.has_pygame and self.is_playing:
            try:
                import pygame
                if self.is_muted:
                    pygame.mixer.music.set_volume(0.0)
                else:
                    pygame.mixer.music.set_volume(self.volume)
            except Exception as e:
                print(f"Error toggling mute: {e}")

    def set_volume(self, volume: float):
        """Set music volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))

        if self.has_pygame and self.is_playing and not self.is_muted:
            try:
                import pygame
                pygame.mixer.music.set_volume(self.volume)
            except Exception as e:
                print(f"Error setting volume: {e}")

    def cleanup(self):
        """Cleanup music resources."""
        self.stop()
        if self.has_pygame:
            try:
                import pygame
                pygame.mixer.quit()
            except Exception as e:
                print(f"Error cleaning up music: {e}")

    def is_available(self) -> bool:
        """Check if background music is available.

        Returns:
            True if pygame and music file are available, False otherwise.
        """
        return self.has_pygame and self.music_path.exists()
