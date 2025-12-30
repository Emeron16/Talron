#!/bin/bash
# Script to create macOS .icns icon from a PNG image
# Usage: ./create_icon.sh your_icon.png

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: ./create_icon.sh <path-to-icon.png>"
    echo ""
    echo "Requirements:"
    echo "  - PNG image (recommended: 1024x1024 pixels)"
    echo "  - Square image works best"
    echo ""
    echo "Output: app_icon.icns (ready to use for app)"
    exit 1
fi

INPUT_IMAGE="$1"

if [ ! -f "$INPUT_IMAGE" ]; then
    echo "Error: File '$INPUT_IMAGE' not found!"
    exit 1
fi

echo "Creating macOS icon from: $INPUT_IMAGE"
echo ""

# Create iconset directory
ICONSET_DIR="app_icon.iconset"
rm -rf "$ICONSET_DIR"
mkdir "$ICONSET_DIR"

# Generate all required icon sizes
echo "Generating icon sizes..."
sips -z 16 16     "$INPUT_IMAGE" --out "${ICONSET_DIR}/icon_16x16.png" > /dev/null
sips -z 32 32     "$INPUT_IMAGE" --out "${ICONSET_DIR}/icon_16x16@2x.png" > /dev/null
sips -z 32 32     "$INPUT_IMAGE" --out "${ICONSET_DIR}/icon_32x32.png" > /dev/null
sips -z 64 64     "$INPUT_IMAGE" --out "${ICONSET_DIR}/icon_32x32@2x.png" > /dev/null
sips -z 128 128   "$INPUT_IMAGE" --out "${ICONSET_DIR}/icon_128x128.png" > /dev/null
sips -z 256 256   "$INPUT_IMAGE" --out "${ICONSET_DIR}/icon_128x128@2x.png" > /dev/null
sips -z 256 256   "$INPUT_IMAGE" --out "${ICONSET_DIR}/icon_256x256.png" > /dev/null
sips -z 512 512   "$INPUT_IMAGE" --out "${ICONSET_DIR}/icon_256x256@2x.png" > /dev/null
sips -z 512 512   "$INPUT_IMAGE" --out "${ICONSET_DIR}/icon_512x512.png" > /dev/null
sips -z 1024 1024 "$INPUT_IMAGE" --out "${ICONSET_DIR}/icon_512x512@2x.png" > /dev/null

echo "✓ Generated all icon sizes"
echo ""

# Convert to .icns
echo "Creating .icns file..."
iconutil -c icns "$ICONSET_DIR" -o app_icon.icns

# Clean up
rm -rf "$ICONSET_DIR"

echo "✓ Created app_icon.icns"
echo ""
echo "Success! Your icon is ready."
echo ""
echo "Next steps:"
echo "  1. The icon will be automatically used in the next build"
echo "  2. Run: ./build_scripts/build_pyinstaller.sh"
echo "  3. Your app will have the custom icon!"
