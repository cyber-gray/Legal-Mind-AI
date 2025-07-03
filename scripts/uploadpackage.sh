#!/bin/bash

# Legal-Mind-AI Teams Package Upload Script
# Based on Microsoft Build healthcare agent deployment pattern

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🤖 Legal-Mind-AI Teams Package Builder${NC}"
echo "================================================"

# Check if output directory is provided
if [ "$#" -ne 1 ]; then
    echo -e "${RED}Usage: $0 <output_directory>${NC}"
    echo "Example: $0 output/"
    exit 1
fi

OUTPUT_DIR="$1"
MANIFEST_DIR="teams-manifest"
PACKAGE_NAME="legal-mind-ai-teams-package.zip"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo -e "${YELLOW}📁 Preparing Teams app package...${NC}"

# Check if manifest exists
if [ ! -f "$MANIFEST_DIR/manifest.json" ]; then
    echo -e "${RED}❌ manifest.json not found in $MANIFEST_DIR/${NC}"
    exit 1
fi

# Validate required files
echo -e "${YELLOW}🔍 Validating manifest files...${NC}"

# For now, we'll create simple placeholder icons if they don't exist
if [ ! -f "$MANIFEST_DIR/icon-color.png" ]; then
    echo -e "${YELLOW}⚠️  Creating placeholder color icon${NC}"
    # Create a simple 1x1 pixel PNG as placeholder
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==" | base64 -d > "$MANIFEST_DIR/icon-color.png"
fi

if [ ! -f "$MANIFEST_DIR/icon-outline.png" ]; then
    echo -e "${YELLOW}⚠️  Creating placeholder outline icon${NC}"
    # Create a simple 1x1 pixel PNG as placeholder
    echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==" | base64 -d > "$MANIFEST_DIR/icon-outline.png"
fi

# Create the Teams app package
echo -e "${YELLOW}📦 Creating Teams app package...${NC}"

cd "$MANIFEST_DIR"
zip -r "../$OUTPUT_DIR/$PACKAGE_NAME" manifest.json icon-color.png icon-outline.png
cd ..

echo -e "${GREEN}✅ Teams app package created: $OUTPUT_DIR/$PACKAGE_NAME${NC}"

# Display installation instructions
echo ""
echo -e "${GREEN}📱 Installation Instructions:${NC}"
echo "1. Open Microsoft Teams"
echo "2. Go to Apps (left sidebar)"
echo "3. Click 'Upload a custom app' or 'Manage your apps'"
echo "4. Click 'Upload an app'"
echo "5. Select the file: $OUTPUT_DIR/$PACKAGE_NAME"
echo "6. Click 'Add' to install Legal-Mind-AI"
echo ""
echo -e "${GREEN}🚀 Your Legal-Mind-AI bot will then be available for chat!${NC}"

# Optional: Auto-open the output directory
if command -v open &> /dev/null; then
    echo -e "${YELLOW}📂 Opening output directory...${NC}"
    open "$OUTPUT_DIR"
fi

echo -e "${GREEN}🎉 Package build complete!${NC}"
