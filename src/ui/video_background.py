"""Video background widget for GUI."""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional
import threading
import time
import queue


class VideoBackground(tk.Canvas):
    """Canvas-based video background widget.

    This widget displays a looping video as the background.
    For now, it uses a placeholder pattern until the video file is provided.

    To use with actual video:
    1. Place your video file in: src/ui/assets/background_video.mp4
    2. Install opencv-python: pip install opencv-python
    3. The widget will automatically detect and play the video
    """

    def __init__(self, parent, **kwargs):
        """Initialize the video background.

        Args:
            parent: Parent widget.
            **kwargs: Additional canvas options.
        """
        super().__init__(parent, highlightthickness=0, **kwargs)

        self.video_path = Path(__file__).parent / "assets" / "background_video.mp4"
        self.is_playing = False
        self.video_thread = None

        # Cache dimensions for thread-safe access
        self.cached_width = 1200
        self.cached_height = 800

        # Thread-safe queue for frame updates
        self.frame_queue = queue.Queue(maxsize=2)

        # Try to load video if opencv is available
        self.has_opencv = self._check_opencv()

        if self.has_opencv and self.video_path.exists():
            self._setup_video()
        else:
            self._setup_placeholder()

        # Update cached dimensions periodically
        self._update_dimensions()

        # Start frame processing in main thread
        if self.has_opencv and self.video_path.exists():
            self._process_frame_queue()

    def _check_opencv(self) -> bool:
        """Check if opencv is available.

        Returns:
            True if opencv is installed, False otherwise.
        """
        try:
            import cv2
            return True
        except ImportError:
            return False

    def _setup_placeholder(self):
        """Setup placeholder background pattern."""
        # Create an animated gradient placeholder
        self.colors = ['#1a1a2e', '#16213e', '#0f3460', '#16213e', '#1a1a2e']
        self.color_index = 0
        self.configure(bg=self.colors[0])

        # Schedule text creation after widget is rendered
        self.after(100, self._create_placeholder_text)

        # Start animated gradient
        self._animate_placeholder()

    def _create_placeholder_text(self):
        """Create placeholder text after widget is rendered."""
        # Get actual widget dimensions
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()

        # Fallback if dimensions still not available
        if width <= 1 or height <= 1:
            width = 1200
            height = 800

        # Draw gradient rectangles for visual interest
        num_bars = 5
        bar_height = height // num_bars
        for i in range(num_bars):
            color = self.colors[i % len(self.colors)]
            self.create_rectangle(
                0, i * bar_height,
                width, (i + 1) * bar_height,
                fill=color, outline='',
                tags='gradient_bg'
            )

        # Add text indicating video placeholder
        self.create_text(
            width // 2, height // 2,
            text="Video Background Placeholder\n\nTo add video:\n"
                 "1. Install: pip install opencv-python pillow\n"
                 "2. Place video at: src/ui/assets/background_video.mp4",
            font=('Segoe UI', 14),
            fill='#ecf0f1',
            justify='center',
            tags='placeholder_text'
        )

    def _animate_placeholder(self):
        """Animate the placeholder background."""
        if not self.is_playing:
            self.is_playing = True
            self._update_placeholder_color()

    def _update_placeholder_color(self):
        """Update placeholder background color for animation."""
        if self.is_playing:
            self.color_index = (self.color_index + 1) % len(self.colors)

            # Update gradient bars if they exist
            gradient_items = self.find_withtag('gradient_bg')
            if gradient_items:
                for i, item in enumerate(gradient_items):
                    color = self.colors[(i + self.color_index) % len(self.colors)]
                    self.itemconfig(item, fill=color)
            else:
                # Fallback to background color
                self.configure(bg=self.colors[self.color_index])

            self.after(2000, self._update_placeholder_color)

    def _setup_video(self):
        """Setup video playback using opencv."""
        try:
            import cv2
            from PIL import Image, ImageTk

            self.cv2 = cv2
            self.Image = Image
            self.ImageTk = ImageTk

            self.cap = cv2.VideoCapture(str(self.video_path))
            self.is_playing = True

            # Start video playback in separate thread
            self.video_thread = threading.Thread(target=self._play_video, daemon=True)
            self.video_thread.start()

        except Exception as e:
            print(f"Error setting up video: {e}")
            self._setup_placeholder()

    def _update_dimensions(self):
        """Update cached dimensions from main thread."""
        if self.winfo_exists():
            width = self.winfo_width()
            height = self.winfo_height()

            # Only update if we have valid dimensions
            if width > 1 and height > 1:
                self.cached_width = width
                self.cached_height = height

        # Schedule next update
        if self.is_playing:
            self.after(500, self._update_dimensions)

    def _play_video(self):
        """Play video in loop."""
        while self.is_playing:
            ret, frame = self.cap.read()

            if not ret:
                # Loop video
                self.cap.set(self.cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            # Convert frame to PIL Image
            frame = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
            frame = self.Image.fromarray(frame)

            # Resize to canvas size using cached dimensions (thread-safe)
            frame = frame.resize((self.cached_width, self.cached_height), self.Image.Resampling.LANCZOS)

            # Put frame in queue for main thread (non-blocking)
            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                # Skip this frame if queue is full
                pass

            # Control frame rate
            time.sleep(0.033)  # ~30 FPS

    def _process_frame_queue(self):
        """Process frames from queue in main thread."""
        if not self.is_playing or not self.winfo_exists():
            return

        try:
            # Get frame from queue (non-blocking)
            pil_image = self.frame_queue.get_nowait()

            # Create PhotoImage and update canvas in main thread
            photo = self.ImageTk.PhotoImage(pil_image)
            self.delete('video_frame')
            self.create_image(0, 0, anchor='nw', image=photo, tags='video_frame')
            self.image = photo  # Keep reference to prevent garbage collection

        except queue.Empty:
            # No frame available, continue
            pass
        except Exception as e:
            print(f"Error updating video frame: {e}")

        # Schedule next frame processing
        if self.is_playing:
            self.after(16, self._process_frame_queue)  # ~60 FPS check rate

    def stop(self):
        """Stop video playback."""
        self.is_playing = False
        if hasattr(self, 'cap'):
            self.cap.release()

    def start(self):
        """Start video playback."""
        if not self.is_playing:
            if self.has_opencv and self.video_path.exists():
                self._setup_video()
            else:
                self._animate_placeholder()
