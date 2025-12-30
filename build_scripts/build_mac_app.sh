#!/bin/bash
# Script to build macOS .app bundle and DMG installer for Talron Word Search

set -e  # Exit on error

echo "========================================"
echo "Building Talron Word Search for macOS"
echo "========================================"

# Clean previous builds
echo ""
echo "Step 1: Cleaning previous builds..."
rm -rf build dist
echo "✓ Cleaned build and dist directories"

# Install py2app if not already installed
echo ""
echo "Step 2: Installing py2app..."
pip install py2app
echo "✓ py2app installed"

# Build the .app bundle
echo ""
echo "Step 3: Building .app bundle..."
python setup_app.py py2app
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
echo "  open dist/${APP_NAME}.app"
echo ""
echo "To install the app:"
echo "  1. Open ${DMG_NAME}.dmg"
echo "  2. Drag '${APP_NAME}' to Applications folder"
echo ""
echo "Note: If you see a security warning, go to:"
echo "  System Preferences > Security & Privacy > General"
echo "  and click 'Open Anyway'"
echo ""
