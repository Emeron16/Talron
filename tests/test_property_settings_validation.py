"""Property-based tests for settings validation.

**Feature: themed-word-search-game, Property 3: Settings validation**
**Validates: Requirements 2.1, 2.2**
"""

import pytest
from hypothesis import given, strategies as st
from src.models.core import GameSettings


class TestSettingsValidation:
    """Property tests for game settings validation."""

    @given(
        grid_size=st.integers(min_value=8, max_value=20),
        time_limit=st.integers(min_value=60, max_value=1800)
    )
    def test_valid_settings_are_accepted(self, grid_size: int, time_limit: int):
        """
        Property 3: Settings validation
        For any valid game configuration input, the system should accept valid 
        grid sizes (8-20) and time limits (60-1800).
        
        **Feature: themed-word-search-game, Property 3: Settings validation**
        **Validates: Requirements 2.1, 2.2**
        """
        # Valid settings should be created without raising an exception
        settings = GameSettings(grid_size=grid_size, time_limit=time_limit)
        
        # Verify the settings were stored correctly
        assert settings.grid_size == grid_size
        assert settings.time_limit == time_limit

    @given(
        grid_size=st.one_of(
            st.integers(max_value=7),  # Below minimum
            st.integers(min_value=21)  # Above maximum
        ),
        time_limit=st.integers(min_value=60, max_value=1800)
    )
    def test_invalid_grid_size_rejected(self, grid_size: int, time_limit: int):
        """
        Property 3: Settings validation
        For any invalid grid size, the system should reject the configuration.
        
        **Feature: themed-word-search-game, Property 3: Settings validation**
        **Validates: Requirements 2.1**
        """
        with pytest.raises(ValueError, match="Grid size must be between 8 and 20"):
            GameSettings(grid_size=grid_size, time_limit=time_limit)

    @given(
        grid_size=st.integers(min_value=8, max_value=20),
        time_limit=st.one_of(
            st.integers(max_value=59),    # Below minimum
            st.integers(min_value=1801)   # Above maximum
        )
    )
    def test_invalid_time_limit_rejected(self, grid_size: int, time_limit: int):
        """
        Property 3: Settings validation
        For any invalid time limit, the system should reject the configuration.
        
        **Feature: themed-word-search-game, Property 3: Settings validation**
        **Validates: Requirements 2.2**
        """
        with pytest.raises(ValueError, match="Time limit must be between 60 and 1800 seconds"):
            GameSettings(grid_size=grid_size, time_limit=time_limit)

    @given(
        grid_size=st.one_of(
            st.integers(max_value=7),
            st.integers(min_value=21)
        ),
        time_limit=st.one_of(
            st.integers(max_value=59),
            st.integers(min_value=1801)
        )
    )
    def test_both_invalid_settings_rejected(self, grid_size: int, time_limit: int):
        """
        Property 3: Settings validation
        For any configuration with both invalid grid size and time limit,
        the system should reject the configuration.
        
        **Feature: themed-word-search-game, Property 3: Settings validation**
        **Validates: Requirements 2.1, 2.2**
        """
        with pytest.raises(ValueError):
            GameSettings(grid_size=grid_size, time_limit=time_limit)