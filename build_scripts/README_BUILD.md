# Building Talron Word Search for macOS

This guide explains how to build a standalone macOS application (.app) and DMG installer for Talron Word Search.

## Prerequisites

1. **macOS System**: You must be on a Mac to build macOS applications
2. **Python 3.8+**: Ensure Python is installed
3. **Xcode Command Line Tools**: Install with `xcode-select --install`

## Quick Build (Automated)

The easiest way to build the app is using the automated build script:

```bash
# Make the script executable
chmod +x build_mac_app.sh

# Run the build script
./build_mac_app.sh
```

This will:
1. Clean previous builds
2. Install py2app
3. Build the .app bundle
4. Create a DMG installer

## Manual Build Steps

If you prefer to build manually:

### Step 1: Install Dependencies

```bash
pip install py2app
pip install -r requirements.txt
```

### Step 2: Build the .app Bundle

```bash
python setup_app.py py2app
```

This creates `dist/Talron Word Search.app`

### Step 3: Create DMG Installer (Optional)

```bash
hdiutil create -volname "Talron Word Search" \
  -srcfolder dist \
  -ov -format UDZO \
  Talron-Word-Search-Installer.dmg
```

## Testing the Application

### Test the .app Bundle

```bash
open "dist/Talron Word Search.app"
```

### Test the DMG Installer

```bash
open Talron-Word-Search-Installer.dmg
```

Then drag the app to the Applications folder.

## Adding an Icon (Optional)

To add a custom icon to your app:

1. Create or obtain a 1024x1024 PNG icon
2. Convert it to .icns format:
   ```bash
   # Create iconset directory
   mkdir app_icon.iconset

   # Generate different sizes (requires your icon.png)
   sips -z 16 16     icon.png --out app_icon.iconset/icon_16x16.png
   sips -z 32 32     icon.png --out app_icon.iconset/icon_16x16@2x.png
   sips -z 32 32     icon.png --out app_icon.iconset/icon_32x32.png
   sips -z 64 64     icon.png --out app_icon.iconset/icon_32x32@2x.png
   sips -z 128 128   icon.png --out app_icon.iconset/icon_128x128.png
   sips -z 256 256   icon.png --out app_icon.iconset/icon_128x128@2x.png
   sips -z 256 256   icon.png --out app_icon.iconset/icon_256x256.png
   sips -z 512 512   icon.png --out app_icon.iconset/icon_256x256@2x.png
   sips -z 512 512   icon.png --out app_icon.iconset/icon_512x512.png
   sips -z 1024 1024 icon.png --out app_icon.iconset/icon_512x512@2x.png

   # Convert to icns
   iconutil -c icns app_icon.iconset
   ```

3. The `app_icon.icns` file is already referenced in [setup_app.py](setup_app.py)
4. Rebuild the app

## Troubleshooting

### Missing tkinter

If you get a tkinter error, ensure you're using a Python installation that includes tkinter:

```bash
python -m tkinter  # Should open a test window
```

If tkinter is missing, install Python from python.org or use Homebrew:
```bash
brew install python-tk@3.11  # Adjust version as needed
```

### Security Warning on First Launch

macOS may show a security warning because the app isn't signed. To open:

1. Right-click the app and select "Open"
2. Click "Open" in the dialog
3. Or go to: System Preferences > Security & Privacy > General > Click "Open Anyway"

### Code Signing (For Distribution)

To properly sign your app for distribution:

```bash
# Sign the app bundle
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name" \
  "dist/Talron Word Search.app"

# Verify signature
codesign --verify --verbose "dist/Talron Word Search.app"
spctl --assess --verbose "dist/Talron Word Search.app"
```

Note: This requires an Apple Developer account and Developer ID certificate.

## File Structure After Build

```
Talron/
├── build/                          # Build artifacts (can be deleted)
├── dist/
│   └── Talron Word Search.app     # The standalone app
├── Talron-Word-Search-Installer.dmg  # DMG installer
├── setup_app.py                   # py2app configuration
├── build_mac_app.sh              # Automated build script
└── README_BUILD.md               # This file
```

## Distribution

### For Personal Use
Simply copy the .app to your Applications folder or share the DMG file.

### For Public Distribution
1. Sign the app with a Developer ID certificate
2. Notarize the app with Apple
3. Staple the notarization ticket
4. Distribute the DMG

See Apple's documentation on app notarization for details.

## Cleaning Build Files

To clean up build artifacts:

```bash
rm -rf build dist
rm -f Talron-Word-Search-Installer.dmg
```

## Additional Resources

- [py2app documentation](https://py2app.readthedocs.io/)
- [Apple Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Creating DMG files](https://developer.apple.com/forums/thread/650458)
