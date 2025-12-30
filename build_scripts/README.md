# Build Scripts

This folder contains all scripts and configuration files needed to build the macOS application.

## Quick Start

**Build the app:**
```bash
./build_scripts/build_pyinstaller.sh
```

**Add a custom icon:**
```bash
# 1. Get a PNG image (1024x1024 recommended)
# 2. Run:
./build_scripts/create_icon.sh path/to/your_icon.png

# 3. Rebuild:
./build_scripts/build_pyinstaller.sh
```

## Files in This Folder

- **build_pyinstaller.sh** - Main build script (PyInstaller) - **USE THIS**
- **create_icon.sh** - Helper to create app icon from PNG
- **build_mac_app.sh** - Alternative build script (py2app)
- **setup_app.py** - Configuration for py2app
- **Talron Word Search.spec** - PyInstaller specification file (auto-generated)
- **README_BUILD.md** - Complete documentation

## Custom App Icon

To set a custom icon for your app:

### Step 1: Get/Create an Icon
- PNG format
- 1024x1024 pixels (recommended)
- Square image
- Clear, simple design works best

### Step 2: Convert to .icns
```bash
./build_scripts/create_icon.sh your_icon.png
```

This creates `app_icon.icns` in the project root.

### Step 3: Rebuild
```bash
./build_scripts/build_pyinstaller.sh
```

The build script automatically detects and uses `app_icon.icns` if it exists.

### Icon Tips
- Keep it simple - complex icons can look blurry at small sizes
- Test at different sizes (16x16, 32x32, 128x128, etc.)
- Use bold colors and clear shapes
- Avoid text if possible (hard to read when small)

## Output

After building, you'll find:
- `dist/Talron Word Search.app` - The application
- `Talron-Word-Search-Installer.dmg` - DMG installer

## Testing

```bash
# Test the app directly
open "dist/Talron Word Search.app"

# Or test the DMG
open Talron-Word-Search-Installer.dmg
```

## Full Documentation

See [README_BUILD.md](README_BUILD.md) for complete build instructions, troubleshooting, and distribution options.
