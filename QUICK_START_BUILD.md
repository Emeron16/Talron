# Quick Start: Building macOS App

## Build the App

```bash
./build_scripts/build_pyinstaller.sh
```

Output:
- `dist/Talron Word Search.app` - Application
- `Talron-Word-Search-Installer.dmg` - Installer

## Add Custom Icon

```bash
# 1. Create icon from your PNG (1024x1024 recommended)
./build_scripts/create_icon.sh src/ui/assets/word_icon.png

# 2. Rebuild
./build_scripts/build_pyinstaller.sh
```

## Test the App

```bash
open "dist/Talron Word Search.app"
```

---

**Full documentation:** [build_scripts/README_BUILD.md](build_scripts/README_BUILD.md)
