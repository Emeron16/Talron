"""Achievement tracking and persistence manager."""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class AchievementManager:
    """Manages player achievements and persistence."""

    ACHIEVEMENT_FILE = Path.home() / '.talron' / 'achievements.json'
    SCHEMA_VERSION = "1.0"

    def __init__(self):
        """Initialize achievement manager and load achievements."""
        self.achievements = self._load_achievements()

    def _create_empty_achievements(self) -> dict:
        """Create empty achievements structure.

        Returns:
            Empty achievements dictionary with version.
        """
        return {
            "version": self.SCHEMA_VERSION,
            "achievements": {}
        }

    def _load_achievements(self) -> dict:
        """Load achievements from disk with error handling.

        Returns:
            Achievements dictionary.
        """
        try:
            # Create directory if it doesn't exist
            self.ACHIEVEMENT_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Load existing file
            if self.ACHIEVEMENT_FILE.exists():
                with open(self.ACHIEVEMENT_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Validate schema version
                if data.get('version') != self.SCHEMA_VERSION:
                    print(f"Warning: Achievement schema version mismatch. "
                          f"Expected {self.SCHEMA_VERSION}, got {data.get('version')}")
                    # Could implement migration here in the future
                    return data

                return data
            else:
                # Create new file
                return self._create_empty_achievements()

        except json.JSONDecodeError as e:
            # Corrupted JSON - backup and create fresh
            print(f"Warning: Corrupted achievements file detected: {e}")
            backup_path = self.ACHIEVEMENT_FILE.with_suffix('.json.bak')
            try:
                shutil.copy(self.ACHIEVEMENT_FILE, backup_path)
                print(f"Backed up corrupted file to: {backup_path}")
            except Exception as backup_error:
                print(f"Warning: Could not create backup: {backup_error}")

            return self._create_empty_achievements()

        except PermissionError as e:
            print(f"Warning: Permission error loading achievements: {e}")
            print("Running in memory-only mode (achievements won't be saved)")
            return self._create_empty_achievements()

        except Exception as e:
            print(f"Warning: Unexpected error loading achievements: {e}")
            return self._create_empty_achievements()

    def _save_achievements(self) -> None:
        """Save achievements to disk with atomic write."""
        try:
            # Ensure directory exists
            self.ACHIEVEMENT_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first (atomic operation)
            temp_file = self.ACHIEVEMENT_FILE.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.achievements, f, indent=2, ensure_ascii=False)

            # Atomic rename (safe on all platforms)
            temp_file.replace(self.ACHIEVEMENT_FILE)

        except PermissionError as e:
            print(f"Warning: Permission error saving achievements: {e}")
            print("Achievement not saved (running in memory-only mode)")

        except Exception as e:
            print(f"Warning: Error saving achievements: {e}")

    def get_star_level(self, grid_size: int) -> int:
        """Convert grid size to star level.

        Args:
            grid_size: Grid size (8-20).

        Returns:
            Star level (0-4).
                4★ for grid 20+
                3★ for grid 18-19
                2★ for grid 15-17
                1★ for grid 10-14
                0★ for grid < 10
        """
        if grid_size >= 20:
            return 4
        elif grid_size >= 18:
            return 3
        elif grid_size >= 15:
            return 2
        elif grid_size >= 10:
            return 1
        else:
            return 0

    def get_star_color(self, completion_percentage: float) -> str:
        """Determine star color from completion percentage.

        Args:
            completion_percentage: Completion percentage (0-100).

        Returns:
            Star color: 'gold' (100%), 'silver' (80-99%), or 'none' (<80%).
        """
        if completion_percentage >= 100.0:
            return "gold"
        elif completion_percentage >= 80.0:
            return "silver"
        else:
            return "none"

    def get_achievement(self, topic: str, subtopic: str) -> Optional[dict]:
        """Get achievement for a topic/subtopic.

        Args:
            topic: Topic name.
            subtopic: Subtopic name.

        Returns:
            Achievement dictionary or None if not found.
        """
        return self.achievements['achievements'].get(topic, {}).get(subtopic)

    def should_save_achievement(self, topic: str, subtopic: str,
                               star_level: int, star_color: str) -> bool:
        """Check if new achievement is better than existing.

        Args:
            topic: Topic name.
            subtopic: Subtopic name.
            star_level: New star level (1-4).
            star_color: New star color ('gold', 'silver', or 'none').

        Returns:
            True if achievement should be saved.
        """
        # Don't save if no stars earned
        if star_level == 0:
            return False

        existing = self.get_achievement(topic, subtopic)

        # Save if no existing achievement
        if not existing:
            return True

        existing_level = existing.get('highest_star_level', 0)
        existing_color = existing.get('star_color', 'none')

        # Save if higher star level
        if star_level > existing_level:
            return True

        # Save if same level but better color (gold > silver)
        if star_level == existing_level and star_color == 'gold' and existing_color == 'silver':
            return True

        return False

    def save_achievement(self, topic: str, subtopic: str, results: Dict[str, Any]) -> bool:
        """Save achievement if it's better than existing.

        Args:
            topic: Topic name.
            subtopic: Subtopic name.
            results: Game results dictionary containing:
                - grid_size: int
                - completion_percentage: float
                - total_score: int

        Returns:
            True if achievement was saved, False otherwise.
        """
        # Calculate star level and color
        star_level = self.get_star_level(results.get('grid_size', 0))
        star_color = self.get_star_color(results.get('completion_percentage', 0.0))

        # Check if should save
        if not self.should_save_achievement(topic, subtopic, star_level, star_color):
            return False

        # Create nested structure if needed
        if topic not in self.achievements['achievements']:
            self.achievements['achievements'][topic] = {}

        # Save achievement
        self.achievements['achievements'][topic][subtopic] = {
            'highest_star_level': star_level,
            'star_color': star_color,
            'completion_percentage': results.get('completion_percentage', 0.0),
            'grid_size': results.get('grid_size', 0),
            'date_achieved': datetime.now().isoformat(),
            'total_score': results.get('total_score', 0)
        }

        # Persist to disk
        self._save_achievements()

        return True

    def get_all_achievements(self) -> dict:
        """Get all achievements.

        Returns:
            Dictionary of all achievements by topic and subtopic.
        """
        return self.achievements['achievements']

    def get_achievement_count(self) -> int:
        """Get total number of achievements earned.

        Returns:
            Total achievement count across all topics.
        """
        count = 0
        for topic_achievements in self.achievements['achievements'].values():
            count += len(topic_achievements)
        return count

    def get_total_stars(self) -> int:
        """Get total star count across all achievements.

        Returns:
            Sum of all star levels earned.
        """
        total = 0
        for topic_achievements in self.achievements['achievements'].values():
            for achievement in topic_achievements.values():
                total += achievement.get('highest_star_level', 0)
        return total

    def reset_achievements(self) -> bool:
        """Reset all achievements (delete all progress).

        Returns:
            True if reset successful, False otherwise.
        """
        try:
            # Reset to empty achievements
            self.achievements = self._create_empty_achievements()
            self._save_achievements()
            print("All achievements have been reset.")
            return True

        except Exception as e:
            print(f"Error resetting achievements: {e}")
            return False
