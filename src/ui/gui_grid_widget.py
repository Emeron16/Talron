"""Interactive letter grid widget for word selection."""

import tkinter as tk
from tkinter import ttk, font
from typing import List, Callable, Optional, Set
from ..models.core import Grid, Coordinate, WordPlacement
from .animation_helper import ParticleEffect


class LetterGridWidget(tk.Canvas):
    """Interactive grid widget for displaying and selecting words."""

    def __init__(self, parent, grid: Grid, on_word_selected: Callable[[List[Coordinate]], None]):
        """Initialize the letter grid widget.

        Args:
            parent: Parent widget.
            grid: Game grid to display.
            on_word_selected: Callback when word selection is complete.
        """
        self.grid = grid
        self.on_word_selected = on_word_selected

        # Calculate cell size based on grid size
        self.cell_size = max(40, min(60, 600 // grid.size))
        canvas_size = self.cell_size * grid.size

        super().__init__(parent, width=canvas_size, height=canvas_size,
                        bg='#ECF0F1', highlightthickness=2, highlightbackground='#34495E')

        # Selection state
        self.selection: List[Coordinate] = []
        self.is_selecting = False
        self.discovered_words: Set[str] = set()
        self.last_mouse_pos = None  # Track last mouse position for direction

        # Cell visual elements
        self.cell_rects = {}  # (row, col) -> rectangle id
        self.cell_texts = {}  # (row, col) -> text id

        # Colors
        self.colors = {
            'default': '#ECF0F1',
            'selected': '#3498DB',
            'discovered': '#2ECC71',
            'highlighted': '#F39C12',
            'text_default': '#2C3E50',
            'text_selected': '#FFFFFF',
            'text_discovered': '#FFFFFF',
            # Colors for missed words (multiple colors to differentiate overlapping words)
            'missed_1': '#E74C3C',  # Red
            'missed_2': '#9B59B6',  # Purple
            'missed_3': '#E67E22',  # Orange
            'missed_4': '#1ABC9C',  # Turquoise
            'missed_5': '#34495E',  # Dark gray
            'missed_6': '#F1C40F',  # Yellow
            'missed_7': '#16A085',  # Green sea
            'missed_8': '#8E44AD',  # Wisteria
        }

        # Particle effects
        self.particle_effect = ParticleEffect(self)

        # Draw the grid
        self._draw_grid()

        # Bind mouse events
        self.bind('<Button-1>', self._on_mouse_down)
        self.bind('<B1-Motion>', self._on_mouse_drag)
        self.bind('<ButtonRelease-1>', self._on_mouse_up)

    def _draw_grid(self):
        """Draw the letter grid."""
        # Get font for letters
        letter_font = font.Font(family='Arial', size=max(12, self.cell_size // 3), weight='bold')

        for row in range(self.grid.size):
            for col in range(self.grid.size):
                x = col * self.cell_size
                y = row * self.cell_size

                # Draw cell rectangle
                rect_id = self.create_rectangle(
                    x, y, x + self.cell_size, y + self.cell_size,
                    fill=self.colors['default'],
                    outline='#95A5A6',
                    width=1
                )
                self.cell_rects[(row, col)] = rect_id

                # Draw letter text
                letter = self.grid.letters[row][col]
                text_id = self.create_text(
                    x + self.cell_size / 2,
                    y + self.cell_size / 2,
                    text=letter,
                    font=letter_font,
                    fill=self.colors['text_default']
                )
                self.cell_texts[(row, col)] = text_id

    def _get_cell_at_position(self, x: int, y: int) -> Optional[Coordinate]:
        """Get grid coordinate at mouse position.

        Args:
            x: Mouse x coordinate.
            y: Mouse y coordinate.

        Returns:
            Grid Coordinate if valid, None otherwise.
        """
        col = x // self.cell_size
        row = y // self.cell_size

        if 0 <= row < self.grid.size and 0 <= col < self.grid.size:
            return Coordinate(row=row, col=col)
        return None

    def _is_adjacent(self, coord1: Coordinate, coord2: Coordinate) -> bool:
        """Check if two coordinates are adjacent (8-directional).

        Args:
            coord1: First coordinate.
            coord2: Second coordinate.

        Returns:
            True if adjacent, False otherwise.
        """
        row_diff = abs(coord1.row - coord2.row)
        col_diff = abs(coord1.col - coord2.col)
        return row_diff <= 1 and col_diff <= 1 and not (row_diff == 0 and col_diff == 0)

    def _on_mouse_down(self, event):
        """Handle mouse button press."""
        coord = self._get_cell_at_position(event.x, event.y)
        if coord:
            self.is_selecting = True
            self.selection = [coord]
            self.last_mouse_pos = (event.x, event.y)
            self._update_selection_display()

    def _on_mouse_drag(self, event):
        """Handle mouse drag for word selection."""
        if not self.is_selecting:
            return

        coord = self._get_cell_at_position(event.x, event.y)
        if not coord:
            return

        # Check if this is a new cell
        if coord in self.selection:
            self.last_mouse_pos = (event.x, event.y)
            return

        # Check if adjacent to last selected cell
        if self.selection and self._is_adjacent(self.selection[-1], coord):
            last_coord = self.selection[-1]

            # Calculate if this is a diagonal move
            row_diff = coord.row - last_coord.row
            col_diff = coord.col - last_coord.col
            is_diagonal = abs(row_diff) == 1 and abs(col_diff) == 1

            if is_diagonal and self.last_mouse_pos:
                # Use mouse movement direction to determine if this is the intended cell
                mouse_dx = event.x - self.last_mouse_pos[0]
                mouse_dy = event.y - self.last_mouse_pos[1]

                # Get centers of current and candidate cells
                last_center_x = last_coord.col * self.cell_size + self.cell_size / 2
                last_center_y = last_coord.row * self.cell_size + self.cell_size / 2
                new_center_x = coord.col * self.cell_size + self.cell_size / 2
                new_center_y = coord.row * self.cell_size + self.cell_size / 2

                # Vector from last cell to new cell
                cell_dx = new_center_x - last_center_x
                cell_dy = new_center_y - last_center_y

                # Calculate dot product to see if mouse direction matches cell direction
                dot_product = mouse_dx * cell_dx + mouse_dy * cell_dy

                # If mouse is moving away from the diagonal cell, skip it
                if dot_product < 0:
                    self.last_mouse_pos = (event.x, event.y)
                    return

                # For diagonal moves, require mouse to be past the midpoint
                # between the last cell and new cell
                mid_x = (last_center_x + new_center_x) / 2
                mid_y = (last_center_y + new_center_y) / 2

                # Check if mouse is closer to new cell than to midpoint
                dist_to_new = ((event.x - new_center_x)**2 + (event.y - new_center_y)**2)**0.5
                dist_to_mid = ((event.x - mid_x)**2 + (event.y - mid_y)**2)**0.5

                if dist_to_new > dist_to_mid:
                    # Mouse hasn't reached the new cell yet
                    self.last_mouse_pos = (event.x, event.y)
                    return

            self.selection.append(coord)
            self.last_mouse_pos = (event.x, event.y)
            self._update_selection_display()

    def _on_mouse_up(self, event):
        """Handle mouse button release."""
        if not self.is_selecting:
            return

        self.is_selecting = False

        # Notify callback with selection
        if len(self.selection) > 0:
            self.on_word_selected(self.selection.copy())

        # Clear selection display (callback will update if word was found)
        self._clear_selection()

    def _update_selection_display(self):
        """Update visual display of current selection."""
        # Reset all cells to default or discovered state
        for (row, col), rect_id in self.cell_rects.items():
            coord = Coordinate(row=row, col=col)
            if self._is_cell_discovered(coord):
                self.itemconfig(rect_id, fill=self.colors['discovered'])
                self.itemconfig(self.cell_texts[(row, col)], fill=self.colors['text_discovered'])
            elif coord in self.selection:
                self.itemconfig(rect_id, fill=self.colors['selected'])
                self.itemconfig(self.cell_texts[(row, col)], fill=self.colors['text_selected'])
            else:
                self.itemconfig(rect_id, fill=self.colors['default'])
                self.itemconfig(self.cell_texts[(row, col)], fill=self.colors['text_default'])

    def _clear_selection(self):
        """Clear the current selection."""
        self.selection = []
        self.last_mouse_pos = None
        self._update_selection_display()

    def _is_cell_discovered(self, coord: Coordinate) -> bool:
        """Check if a cell is part of a discovered word.

        Args:
            coord: Cell coordinate to check.

        Returns:
            True if cell is part of discovered word, False otherwise.
        """
        # Check each discovered word's placement
        for word in self.discovered_words:
            for placement in self.grid.solution:
                if placement.word == word and coord in placement.coordinates:
                    return True
        return False

    def mark_word_discovered(self, word: str):
        """Mark a word as discovered and update display.

        Args:
            word: The word that was discovered.
        """
        self.discovered_words.add(word.upper())

        # Create particle effect for discovered word
        word_coords = []
        for placement in self.grid.solution:
            if placement.word == word.upper():
                for coord in placement.coordinates:
                    x = coord.col * self.cell_size + self.cell_size / 2
                    y = coord.row * self.cell_size + self.cell_size / 2
                    word_coords.append((x, y))
                break

        if word_coords:
            self.particle_effect.create_word_found_effect(word_coords)

        self._update_selection_display()

    def update_grid(self, grid: Grid):
        """Update the grid being displayed.

        Args:
            grid: New grid to display.
        """
        # Clear canvas
        self.delete('all')

        # Update grid reference
        self.grid = grid
        self.discovered_words = grid.discovered_words.copy()

        # Redraw
        self._draw_grid()
        self._update_selection_display()

    def highlight_word(self, placement: WordPlacement, color: str = None):
        """Highlight a specific word on the grid.

        Args:
            placement: Word placement to highlight.
            color: Optional color to use (defaults to highlighted color).
        """
        color = color or self.colors['highlighted']
        for coord in placement.coordinates:
            rect_id = self.cell_rects.get((coord.row, coord.col))
            if rect_id:
                self.itemconfig(rect_id, fill=color)
                self.itemconfig(self.cell_texts[(coord.row, coord.col)],
                              fill=self.colors['text_selected'])

    def clear_highlights(self):
        """Clear all word highlights."""
        self._update_selection_display()

    def show_all_unfound_words(self):
        """Show all unfound words on the grid with different colors for each word.

        This method displays all words that weren't found during gameplay,
        using different colors to help distinguish overlapping words.
        """
        # Get unfound words
        all_words = {p.word for p in self.grid.solution}
        unfound_words = all_words - self.discovered_words

        if not unfound_words:
            return

        # Get placements for unfound words
        unfound_placements = [p for p in self.grid.solution if p.word in unfound_words]

        # Track which cells belong to which words (for handling overlaps)
        cell_to_words = {}  # coord -> list of (word_index, placement)

        for idx, placement in enumerate(unfound_placements):
            for coord in placement.coordinates:
                key = (coord.row, coord.col)
                if key not in cell_to_words:
                    cell_to_words[key] = []
                cell_to_words[key].append((idx, placement))

        # Assign colors to each word
        available_colors = [
            self.colors['missed_1'], self.colors['missed_2'],
            self.colors['missed_3'], self.colors['missed_4'],
            self.colors['missed_5'], self.colors['missed_6'],
            self.colors['missed_7'], self.colors['missed_8']
        ]

        # Color each cell based on which word(s) it belongs to
        for (row, col), word_list in cell_to_words.items():
            rect_id = self.cell_rects.get((row, col))
            if rect_id:
                # If cell belongs to multiple words, use a striped or gradient effect
                # For simplicity, we'll use the color of the first word
                word_idx = word_list[0][0]
                color = available_colors[word_idx % len(available_colors)]

                # If cell belongs to multiple unfound words, make it slightly darker
                if len(word_list) > 1:
                    # Darken the color by converting to RGB and reducing brightness
                    color = self._darken_color(color, 0.7)

                self.itemconfig(rect_id, fill=color)
                self.itemconfig(self.cell_texts[(row, col)], fill='#FFFFFF')

    def _darken_color(self, hex_color: str, factor: float) -> str:
        """Darken a hex color by a factor.

        Args:
            hex_color: Color in hex format (e.g., '#FF0000')
            factor: Darkening factor (0.0 to 1.0, where 1.0 is no change)

        Returns:
            Darkened color in hex format
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Darken
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)

        # Convert back to hex
        return f'#{r:02x}{g:02x}{b:02x}'
