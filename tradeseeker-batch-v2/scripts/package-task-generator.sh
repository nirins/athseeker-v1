#!/bin/bash
# Package Task Generator Lambda for deployment

set -e

LAMBDA_DIR="lambdas/task-generator"
PACKAGE_DIR="$LAMBDA_DIR/package"
OUTPUT_ZIP="$LAMBDA_DIR/task-generator.zip"

echo "Packaging Task Generator Lambda..."

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
cp "$LAMBDA_DIR/task_generator.py" "$PACKAGE_DIR/"
cp "$LAMBDA_DIR/__init__.py" "$PACKAGE_DIR/"

# Create ZIP file
echo "Creating deployment package..."
cd "$PACKAGE_DIR"
zip -r "../task-generator.zip" . -q
cd - > /dev/null

echo "Package created: $OUTPUT_ZIP"
echo "Size: $(du -h $OUTPUT_ZIP | cut -f1)"
