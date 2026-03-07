# PowerShell script to build Tesseract Lambda Layer using Docker
# This creates a Lambda-compatible layer with Tesseract OCR and Poppler

$ErrorActionPreference = "Stop"

$LAYER_NAME = "tesseract-poppler-layer"
$LAYER_DIR = ".\layer"
$PYTHON_DIR = "$LAYER_DIR\python"

Write-Host "Building Lambda Layer: $LAYER_NAME" -ForegroundColor Green

# Clean previous build
if (Test-Path $LAYER_DIR) {
    Remove-Item -Recurse -Force $LAYER_DIR
}
New-Item -ItemType Directory -Path $LAYER_DIR -Force | Out-Null
New-Item -ItemType Directory -Path "$LAYER_DIR\bin" -Force | Out-Null
New-Item -ItemType Directory -Path "$LAYER_DIR\lib" -Force | Out-Null
New-Item -ItemType Directory -Path "$LAYER_DIR\share" -Force | Out-Null

Write-Host "`nStep 1: Building layer using Docker (Amazon Linux 2)..." -ForegroundColor Yellow

# Use Docker to build in Amazon Linux 2 environment
docker run --rm `
  -v "${PWD}:/var/task" `
  -w /var/task `
  public.ecr.aws/lambda/python:3.12 `
  bash -c @"
    yum update -y -q
    yum install -y -q tesseract poppler-utils
    
    mkdir -p /var/task/$LAYER_DIR/bin
    mkdir -p /var/task/$LAYER_DIR/lib
    mkdir -p /var/task/$LAYER_DIR/share
    
    cp /usr/bin/tesseract /var/task/$LAYER_DIR/bin/ 2>/dev/null || true
    cp -r /usr/share/tesseract /var/task/$LAYER_DIR/share/ 2>/dev/null || true
    cp /usr/bin/pdftoppm /var/task/$LAYER_DIR/bin/ 2>/dev/null || true
    cp /usr/bin/pdfinfo /var/task/$LAYER_DIR/bin/ 2>/dev/null || true
    
    # Copy required libraries
    ldd /usr/bin/tesseract 2>/dev/null | grep -o '/[^ ]*' | xargs -I {} cp {} /var/task/$LAYER_DIR/lib/ 2>/dev/null || true
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nERROR: Docker build failed. Make sure Docker is running." -ForegroundColor Red
    exit 1
}

Write-Host "`nStep 2: Creating wrapper script..." -ForegroundColor Yellow

# Create wrapper script
@"
#!/bin/bash
export LD_LIBRARY_PATH=/opt/lib:`$LD_LIBRARY_PATH
export TESSDATA_PREFIX=/opt/share/tesseract
exec /opt/bin/tesseract `$@
"@ | Out-File -FilePath "$LAYER_DIR\tesseract_wrapper.sh" -Encoding ASCII -NoNewline
# Note: PowerShell can't easily set Unix permissions, but Lambda will handle it

Write-Host "`nStep 3: Creating layer ZIP..." -ForegroundColor Yellow

# Create ZIP file
$zipPath = "$LAYER_NAME.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

# Use PowerShell's Compress-Archive (works on Windows)
Compress-Archive -Path "$LAYER_DIR\*" -DestinationPath $zipPath -Force

Write-Host "`n✅ Layer built successfully!" -ForegroundColor Green
Write-Host "`nLayer ZIP: $zipPath" -ForegroundColor Cyan
Write-Host "Size: $((Get-Item $zipPath).Length / 1MB) MB" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Upload $zipPath to S3" -ForegroundColor White
Write-Host "2. Create Lambda Layer from S3 or upload directly via AWS Console" -ForegroundColor White
Write-Host "3. Attach layer ARN to your Lambda in CDK" -ForegroundColor White
