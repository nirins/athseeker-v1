#!/bin/bash
# Package Downloader Lambda for deployment

set -e

LAMBDA_DIR="lambdas/downloader"
PACKAGE_DIR="$LAMBDA_DIR/package"
OUTPUT_ZIP="$LAMBDA_DIR/downloader.zip"

echo "Packaging Downloader Lambda..."

# Clean previous package
rm -rf "$PACKAGE_DIR"
rm -f "$OUTPUT_ZIP"

# Create package directory
mkdir -p "$PACKAGE_DIR"

# Install dependencies
echo "Installing dependencies..."
pip install -r "$LAMBDA_DIR/requirements.txt" -t "$PACKAGE_DIR" --quiet

# Copy Lambda code
echo "Copying Lambda code..."
cp "$LAMBDA_DIR/handler.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/downloader.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/__init__.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/technical_analysis.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/ath_detector.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/cross_detector.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/breakout_analyzer.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/storage.py" "$PACKAGE_DIR/"

# Copy beauty models system
echo "Copying beauty models..."
cp -r "src/beauty_models" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/breakout_analyzer.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/storage.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/api_client.py" "$PACKAGE_DIR/"

# Create ZIP file
echo "Creating deployment package..."
cd "$PACKAGE_DIR"
zip -r "../downloader.zip" . -q
cd - > /dev/null

echo "Package created: $OUTPUT_ZIP"
echo "Size: $(du -h $OUTPUT_ZIP | cut -f1)"
