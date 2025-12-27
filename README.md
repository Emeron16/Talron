# Themed Word Search Game

A Python-based word search puzzle game featuring themed content from anime, movies, and TV shows with a modern GUI interface.

## Project Structure

```
├── src/
│   ├── models/          # Data models and core interfaces
│   ├── services/        # Game services and business logic
│   ├── data/           # Data storage and management
│   ├── ui/             # GUI components and screens
│   └── gui_app.py      # Main GUI application
├── tests/              # Test files
├── requirements.txt    # Python dependencies
├── setup.py           # Package setup
└── pytest.ini        # Test configuration
```

## Setup

### Option 1: Quick Setup (Recommended)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run tests:
   ```bash
   python -m pytest
   ```

### Option 2: Install as Package

Install the game as a package (allows running from anywhere):

```bash
pip install -e .
```

After installation, you can run:
```bash
word-search-gui  # Launch GUI version
```

## How to Play

### GUI Version

Interactive graphical interface with mouse-based word selection:

```bash
# Option 1: Using the GUI launcher (recommended)
python run_game_gui.py

# Option 2: Running GUI as a module
python -m src.gui_app
```

### Game Flow

1. **Select Topic** - Choose from Anime, Movies, Shows, or Cartoons
2. **Select Subtopic** - Pick a specific title within your chosen topic
3. **Configure Settings** - Set grid size (8-20) and time limit (1-30 minutes)
4. **Play** - Find words by selecting connected letters in the grid
5. **View Results** - See your score, unfound words, and performance rating

### GUI Controls

- **Mouse**: Click and drag to select words on the grid
- **Buttons**: Navigate through screens with on-screen buttons
- **Sliders**: Adjust grid size, time limit, and hints with visual sliders
- **Difficulty Presets**: Quick select Easy, Medium, Hard, or Expert modes
- **Hints**: Request hints during gameplay (letter, word location, or area hints)
- **Sound Toggle**: Enable/disable sound effects with the sound button
- **Music Toggle**: Mute/unmute background music (top-right corner 🎵 button)
- **Pause/Resume**: Pause the game at any time
- **Help Button**: Access game instructions from any screen
- Words are automatically validated when you release the mouse
- Visual particle effects celebrate word discoveries
- **Animated Background**: Video or gradient background for immersive experience

### Keyboard Shortcuts

- **ESC**: Quit the game
- **F1**: Show help dialog with game instructions

### Enhanced Visual Features

The GUI includes several visual enhancements:
- **Video Background**: Looping background video (place `background_video.mp4` in `src/ui/assets/`)
- **Background Music**: Continuous looping music (place `background_music.mp3` in `src/ui/assets/`)
- **Modern Typography**: Enhanced fonts (Segoe UI) with better readability
- **Gradient Effects**: Smooth color transitions and modern styling
- **Animated Placeholders**: Beautiful gradient animation when media files not present

#### To Enable Full Features:
```bash
pip install opencv-python pillow pygame
```

Then place your media files:
- `src/ui/assets/background_video.mp4` - Background video (1920x1080 or 1280x720)
- `src/ui/assets/background_music.mp3` - Background music

See [src/ui/assets/README.md](src/ui/assets/README.md) for detailed instructions.

### Game Features

- **Adjacent-cell word connectivity** - Words can be formed horizontally or vertically
- **Word overlap prevention** - Each word uses unique cells for fair gameplay
- **Timer countdown** - Race against the clock to find all words
- **Progress tracking** - See discovered words and completion percentage
- **Results analysis** - Performance ratings and detailed statistics
- **Session tracking** - Stats across multiple games in one session
- **Difficulty presets** - Easy, Medium, Hard, and Expert configurations
- **Hint system** - Get help with letter clues, word patterns, or location hints
- **Sound effects** - Audio feedback for discoveries and game events
- **Visual animations** - Particle effects and celebrations for word discoveries

## Core Models

- **Game**: Represents a game session with settings and state
- **Grid**: The N×N letter grid with word placements
- **WordPlacement**: Words placed in the grid with coordinates
- **WordData**: Topic/subtopic word collections
- **GameSettings**: Configuration for grid size and time limits
- **Coordinate**: Position in the grid

## Testing

The project uses:
- **pytest** for unit testing
- **Hypothesis** for property-based testing

Property-based tests validate universal properties across randomized inputs, ensuring robust correctness guarantees.

## Database

The game includes 130 themed subtopics across 4 categories:
- **Anime**: 36 subtopics (Naruto, One Piece, Attack on Titan, etc.)
- **Movies**: 31 subtopics (Star Wars, Marvel, Harry Potter, etc.)
- **Shows**: 33 subtopics (Game of Thrones, Breaking Bad, The Office, etc.)
- **Cartoons**: 30 subtopics (SpongeBob, Avatar, Ben 10, etc.)

Each subtopic contains 10 character words and 9-10 defining words, totaling 2,600 words.
