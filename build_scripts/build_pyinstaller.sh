#!/bin/bash
# Script to build macOS .app bundle and DMG installer using PyInstaller

set -e  # Exit on error

# Change to project root directory
cd "$(dirname "$0")/.."

echo "========================================"
echo "Building Talron Word Search for macOS"
echo "Using PyInstaller"
echo "========================================"

# Check for custom icon
ICON_ARG=""
if [ -f "app_icon.icns" ]; then
    echo "✓ Found custom icon: app_icon.icns"
    ICON_ARG="--icon=app_icon.icns"
else
    echo "ℹ No custom icon found. To add one:"
    echo "  1. Place a 1024x1024 PNG in the project root"
    echo "  2. Run: ./build_scripts/create_icon.sh your_icon.png"
    echo ""
fi

# Clean previous builds
echo ""
echo "Step 1: Cleaning previous builds..."
rm -rf build dist
echo "✓ Cleaned build and dist directories"

# Install PyInstaller if not already installed
echo ""
echo "Step 2: Installing PyInstaller..."
pip install pyinstaller
echo "✓ PyInstaller installed"

# Build the .app bundle
echo ""
echo "Step 3: Building .app bundle..."
# Use the pre-configured spec file with correct paths
pyinstaller --noconfirm "build_scripts/Talron Word Search.spec"

echo "✓ .app bundle created in dist/ directory"

# Create DMG installer
echo ""
echo "Step 4: Creating DMG installer..."

APP_NAME="Talron Word Search"
DMG_NAME="Talron-Word-Search-Installer"
DMG_TEMP="dmg_temp"
APP_PATH="dist/${APP_NAME}.app"

# Create temporary directory for DMG
mkdir -p "${DMG_TEMP}"

# Copy app to temp directory
cp -R "${APP_PATH}" "${DMG_TEMP}/"

# Create symbolic link to Applications folder
ln -s /Applications "${DMG_TEMP}/Applications"

# Create DMG
hdiutil create -volname "${APP_NAME}" -srcfolder "${DMG_TEMP}" -ov -format UDZO "${DMG_NAME}.dmg"

# Clean up temp directory
rm -rf "${DMG_TEMP}"

echo "✓ DMG installer created: ${DMG_NAME}.dmg"

# Display final information
echo ""
echo "========================================"
echo "Build Complete!"
echo "========================================"
echo ""
echo "Application bundle: dist/${APP_NAME}.app"
echo "DMG Installer: ${DMG_NAME}.dmg"
echo ""
echo "To test the app:"
echo "  open \"dist/${APP_NAME}.app\""
echo ""
echo "To install the app:"
echo "  1. Open ${DMG_NAME}.dmg"
echo "  2. Drag '${APP_NAME}' to Applications folder"
echo ""
echo "Note: If you see a security warning, go to:"
echo "  System Preferences > Security & Privacy > General"
echo "  and click 'Open Anyway'"
echo ""
