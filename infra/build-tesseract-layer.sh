#!/bin/bash
# Build a Lambda Layer containing Tesseract OCR and Poppler utilities
# This layer can be attached to Lambda functions that need OCR capabilities

set -e

LAYER_NAME="tesseract-poppler-layer"
LAYER_DIR="./layer"
PYTHON_DIR="${LAYER_DIR}/python"

echo "Building Lambda Layer: ${LAYER_NAME}"

# Clean previous build
rm -rf ${LAYER_DIR}
mkdir -p ${PYTHON_DIR}

# Use Docker to build the layer in an Amazon Linux 2 environment
# This ensures compatibility with Lambda's runtime environment
docker run --rm \
  -v "$(pwd)":/var/task \
  -w /var/task \
  public.ecr.aws/lambda/python:3.12 \
  bash -c "
    # Install Tesseract and Poppler
    yum update -y
    yum install -y tesseract poppler-utils
    
    # Copy binaries to layer
    mkdir -p /var/task/${LAYER_DIR}/bin
    mkdir -p /var/task/${LAYER_DIR}/lib
    
    # Copy Tesseract
    cp /usr/bin/tesseract /var/task/${LAYER_DIR}/bin/
    cp -r /usr/share/tesseract /var/task/${LAYER_DIR}/share/ 2>/dev/null || true
    
    # Copy Poppler utilities (pdftoppm, pdfinfo, etc.)
    cp /usr/bin/pdftoppm /var/task/${LAYER_DIR}/bin/ 2>/dev/null || true
    cp /usr/bin/pdfinfo /var/task/${LAYER_DIR}/bin/ 2>/dev/null || true
    
    # Copy required libraries
    ldd /usr/bin/tesseract | grep -o '/[^ ]*' | xargs -I {} cp {} /var/task/${LAYER_DIR}/lib/ 2>/dev/null || true
  "

# Create a wrapper script that sets LD_LIBRARY_PATH
cat > ${LAYER_DIR}/tesseract_wrapper.sh << 'EOF'
#!/bin/bash
export LD_LIBRARY_PATH=/opt/lib:$LD_LIBRARY_PATH
export TESSDATA_PREFIX=/opt/share/tesseract
exec /opt/bin/tesseract "$@"
EOF
chmod +x ${LAYER_DIR}/tesseract_wrapper.sh

# Create layer structure
mkdir -p ${LAYER_DIR}/bin ${LAYER_DIR}/lib ${LAYER_DIR}/share

echo "Layer built successfully!"
echo "Next steps:"
echo "1. Zip the layer: cd ${LAYER_DIR} && zip -r ../${LAYER_NAME}.zip ."
echo "2. Upload to S3 or publish directly to Lambda"
echo "3. Attach to your Lambda function in CDK"
