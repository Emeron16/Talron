"""Animation helpers for GUI effects."""

import tkinter as tk
from typing import Callable, Optional, List


class AnimationHelper:
    """Helper class for creating smooth animations."""

    @staticmethod
    def fade_in(widget, duration: int = 300, callback: Optional[Callable] = None):
        """Fade in a widget.

        Args:
            widget: Widget to animate.
            duration: Animation duration in ms.
            callback: Optional callback when animation completes.
        """
        steps = 20
        step_time = duration // steps

        def animate(step=0):
            if step <= steps:
                # Calculate alpha (0.0 to 1.0)
                alpha = step / steps
                # This is a visual effect - we'll use positioning instead
                widget.after(step_time, lambda: animate(step + 1))
            elif callback:
                callback()

        animate()

    @staticmethod
    def flash_widget(widget, color: str, duration: int = 500, flash_count: int = 2):
        """Flash a widget by changing its background color.

        Args:
            widget: Widget to flash.
            color: Color to flash.
            duration: Total duration in ms.
            flash_count: Number of flashes.
        """
        try:
            original_bg = widget.cget('background')
        except tk.TclError:
            # Some widgets don't support background
            return

        interval = duration // (flash_count * 2)

        def flash(count=0, is_color=True):
            if count < flash_count * 2:
                try:
                    widget.configure(background=color if is_color else original_bg)
                    widget.after(interval, lambda: flash(count + 1, not is_color))
                except tk.TclError:
                    pass

        flash()

    @staticmethod
    def pulse_widget(widget, scale_factor: float = 1.1, duration: int = 300):
        """Create a pulse effect by temporarily scaling a widget.

        Args:
            widget: Widget to pulse.
            scale_factor: How much to scale (1.1 = 10% larger).
            duration: Animation duration in ms.
        """
        # For canvas items, we can animate
        if isinstance(widget, tk.Canvas):
            return

        # For regular widgets, we'll use a color pulse instead
        try:
            original_fg = widget.cget('foreground')
            pulse_color = '#2ECC71'  # Green pulse

            steps = 10
            step_time = duration // (steps * 2)

            def animate(step=0, going_up=True):
                if step < steps:
                    # Interpolate between colors
                    if going_up:
                        widget.configure(foreground=pulse_color)
                    else:
                        widget.configure(foreground=original_fg)

                    next_step = step + 1 if going_up else step - 1
                    next_direction = not going_up if step == steps - 1 else going_up

                    widget.after(step_time, lambda: animate(
                        next_step if going_up else steps - 1,
                        next_direction
                    ))
                elif not going_up:
                    widget.configure(foreground=original_fg)
                else:
                    widget.after(step_time, lambda: animate(steps - 1, False))

            animate()
        except tk.TclError:
            pass

    @staticmethod
    def slide_in(widget, direction: str = 'left', duration: int = 300):
        """Slide a widget in from a direction.

        Args:
            widget: Widget to animate.
            direction: Direction to slide from ('left', 'right', 'top', 'bottom').
            duration: Animation duration in ms.
        """
        # This is a simplified version - full implementation would require
        # place() geometry manager for smooth positioning
        widget.pack()

    @staticmethod
    def animate_canvas_item(canvas: tk.Canvas, item_id: int,
                          target_coords: tuple, duration: int = 300,
                          callback: Optional[Callable] = None):
        """Animate a canvas item to new coordinates.

        Args:
            canvas: Canvas containing the item.
            item_id: Canvas item ID.
            target_coords: Target (x, y) coordinates.
            duration: Animation duration in ms.
            callback: Optional callback when animation completes.
        """
        # Get current coordinates
        current = canvas.coords(item_id)
        if not current or len(current) < 2:
            return

        x1, y1 = current[0], current[1]
        x2, y2 = target_coords

        steps = 20
        step_time = duration // steps

        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps

        def animate(step=0):
            if step <= steps:
                new_x = x1 + dx * step
                new_y = y1 + dy * step
                canvas.coords(item_id, new_x, new_y)
                canvas.after(step_time, lambda: animate(step + 1))
            elif callback:
                callback()

        animate()


class ParticleEffect:
    """Create particle effects on a canvas."""

    def __init__(self, canvas: tk.Canvas):
        """Initialize particle effect.

        Args:
            canvas: Canvas to draw particles on.
        """
        self.canvas = canvas
        self.particles: List[int] = []

    def create_celebration(self, x: int, y: int, color: str = '#F39C12'):
        """Create a celebration particle burst.

        Args:
            x: X coordinate for center.
            y: Y coordinate for center.
            color: Particle color.
        """
        import random
        import math

        particle_count = 12
        particles = []

        # Create particles
        for i in range(particle_count):
            angle = (2 * math.pi * i) / particle_count
            particle = self.canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill=color, outline=''
            )
            particles.append({
                'id': particle,
                'angle': angle,
                'speed': random.uniform(2, 4),
                'life': 20
            })

        # Animate particles
        def animate():
            for particle in particles[:]:
                if particle['life'] <= 0:
                    self.canvas.delete(particle['id'])
                    particles.remove(particle)
                else:
                    # Move particle
                    dx = math.cos(particle['angle']) * particle['speed']
                    dy = math.sin(particle['angle']) * particle['speed']
                    self.canvas.move(particle['id'], dx, dy)
                    particle['life'] -= 1

            if particles:
                self.canvas.after(50, animate)

        animate()

    def create_word_found_effect(self, coords: List[tuple], color: str = '#2ECC71'):
        """Create an effect along a word path.

        Args:
            coords: List of (x, y) coordinates for word cells.
            color: Effect color.
        """
        # Create sparkles at each letter
        sparkles = []
        for x, y in coords:
            sparkle = self.canvas.create_oval(
                x - 5, y - 5, x + 5, y + 5,
                fill=color, outline=''
            )
            sparkles.append(sparkle)

        # Fade out sparkles
        def fade(alpha=10):
            if alpha > 0:
                # Shrink sparkles
                for sparkle in sparkles:
                    coords = self.canvas.coords(sparkle)
                    if coords:
                        cx = (coords[0] + coords[2]) / 2
                        cy = (coords[1] + coords[3]) / 2
                        size = alpha / 2
                        self.canvas.coords(sparkle,
                                         cx - size, cy - size,
                                         cx + size, cy + size)
                self.canvas.after(30, lambda: fade(alpha - 1))
            else:
                for sparkle in sparkles:
                    self.canvas.delete(sparkle)

        fade()

    def cleanup(self):
        """Remove all particle effects."""
        for particle_id in self.particles:
            try:
                self.canvas.delete(particle_id)
            except tk.TclError:
                pass
        self.particles.clear()
