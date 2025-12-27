# Assets Directory

This directory contains media assets for the themed word search game.

## Required Files

### Background Video
- **File**: `background_video.mp4`
- **Format**: MP4 video file
- **Recommended**: 1920x1080 or 1280x720 resolution
- **Purpose**: Animated background for the game interface
- **Requirements**: Install `opencv-python` to enable video playback
  ```bash
  pip install opencv-python pillow
  ```

### Background Music
- **File**: `background_music.mp3`
- **Format**: MP3 audio file
- **Purpose**: Looping background music
- **Requirements**: Install `pygame` to enable audio playback
  ```bash
  pip install pygame
  ```

## Fallback Behavior

If the files are not present or dependencies are not installed:
- **Video**: Shows an animated gradient placeholder
- **Music**: Silently disabled (game functions normally without it)

## Installation

1. Place your media files in this directory
2. Install dependencies:
   ```bash
   pip install opencv-python pillow pygame
   ```
3. Restart the application

The game will automatically detect and use the media files!
