#!/bin/bash

# Frontend Deployment Script for Saarthi.AI

set -e

echo "🎨 Deploying Saarthi.AI Frontend..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js."
    exit 1
fi

# Check for API Gateway URL
if [ -z "$NEXT_PUBLIC_API_GATEWAY_URL" ]; then
    echo "⚠️  NEXT_PUBLIC_API_GATEWAY_URL not set"
    echo "Please set it:"
    echo "  export NEXT_PUBLIC_API_GATEWAY_URL=https://your-api-gateway-url/prod"
    read -p "Enter API Gateway URL: " API_URL
    export NEXT_PUBLIC_API_GATEWAY_URL=$API_URL
fi

# Navigate to frontend directory
cd frontend

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build
echo "🔨 Building frontend..."
npm run build

echo ""
echo "✅ Build complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Push to GitHub for Amplify auto-deploy"
echo "   2. Or deploy manually to Amplify/Vercel"
echo "   3. Set NEXT_PUBLIC_API_GATEWAY_URL in hosting platform"
echo ""
