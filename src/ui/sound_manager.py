"""Sound effects manager for GUI."""

import math
import wave
import struct
import os
import tempfile
from typing import Optional


class SoundManager:
    """Manages sound effects for the game."""

    def __init__(self, enabled: bool = True):
        """Initialize the sound manager.

        Args:
            enabled: Whether sound effects are enabled.
        """
        self.enabled = enabled
        self.temp_dir = tempfile.mkdtemp()
        self._sound_files = {}

        # Generate sound effects
        if self.enabled:
            self._generate_sounds()

    def _generate_sounds(self):
        """Generate all sound effect files."""
        # Word discovered - pleasant ascending tone
        self._sound_files['word_found'] = self._generate_tone(
            frequency=800, duration=0.15, volume=0.3
        )

        # Invalid selection - short low beep
        self._sound_files['invalid'] = self._generate_tone(
            frequency=200, duration=0.1, volume=0.2
        )

        # Game complete - cheerful multi-tone
        self._sound_files['game_complete'] = self._generate_chord(
            frequencies=[523, 659, 784], duration=0.3, volume=0.3
        )

        # Timer warning - attention beep
        self._sound_files['timer_warning'] = self._generate_tone(
            frequency=600, duration=0.1, volume=0.25
        )

        # Perfect game - victory fanfare
        self._sound_files['perfect'] = self._generate_chord(
            frequencies=[523, 659, 784, 1047], duration=0.4, volume=0.3
        )

    def _generate_tone(self, frequency: int, duration: float, volume: float) -> str:
        """Generate a simple tone.

        Args:
            frequency: Tone frequency in Hz.
            duration: Duration in seconds.
            volume: Volume (0.0-1.0).

        Returns:
            Path to generated WAV file.
        """
        sample_rate = 44100
        num_samples = int(sample_rate * duration)

        # Generate sine wave
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            # Apply envelope to avoid clicks
            envelope = 1.0
            if i < 100:  # Fade in
                envelope = i / 100
            elif i > num_samples - 100:  # Fade out
                envelope = (num_samples - i) / 100

            value = int(32767 * volume * envelope * math.sin(2 * math.pi * frequency * t))
            samples.append(struct.pack('<h', value))

        # Write WAV file
        filename = os.path.join(self.temp_dir, f'tone_{frequency}_{int(duration*1000)}.wav')
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(samples))

        return filename

    def _generate_chord(self, frequencies: list, duration: float, volume: float) -> str:
        """Generate a chord (multiple frequencies).

        Args:
            frequencies: List of frequencies in Hz.
            duration: Duration in seconds.
            volume: Volume (0.0-1.0).

        Returns:
            Path to generated WAV file.
        """
        sample_rate = 44100
        num_samples = int(sample_rate * duration)

        # Generate combined sine waves
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            # Apply envelope
            envelope = 1.0
            if i < 100:
                envelope = i / 100
            elif i > num_samples - 100:
                envelope = (num_samples - i) / 100

            # Combine frequencies
            value = 0
            for freq in frequencies:
                value += math.sin(2 * math.pi * freq * t)
            value = int(32767 * volume * envelope * value / len(frequencies))

            samples.append(struct.pack('<h', value))

        # Write WAV file
        freq_str = '_'.join(map(str, frequencies))
        filename = os.path.join(self.temp_dir, f'chord_{freq_str}_{int(duration*1000)}.wav')
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(samples))

        return filename

    def play_sound(self, sound_name: str):
        """Play a sound effect.

        Args:
            sound_name: Name of sound to play (word_found, invalid, game_complete, etc).
        """
        if not self.enabled:
            return

        if sound_name not in self._sound_files:
            return

        try:
            # Platform-specific sound playback
            import platform
            system = platform.system()

            if system == 'Darwin':  # macOS
                os.system(f'afplay "{self._sound_files[sound_name]}" &')
            elif system == 'Linux':
                os.system(f'aplay "{self._sound_files[sound_name]}" &')
            elif system == 'Windows':
                import winsound
                winsound.PlaySound(self._sound_files[sound_name],
                                 winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            # Silently fail if sound playback isn't available
            pass

    def toggle_sounds(self):
        """Toggle sound effects on/off."""
        self.enabled = not self.enabled

    def cleanup(self):
        """Clean up temporary sound files."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass
