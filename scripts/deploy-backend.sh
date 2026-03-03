#!/bin/bash

# Backend Deployment Script for Saarthi.AI

set -e

echo "🚀 Deploying Saarthi.AI Backend..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI."
    exit 1
fi

if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK not found. Installing..."
    npm install -g aws-cdk
fi

# Verify AWS credentials
echo "🔐 Verifying AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run 'aws configure'"
    exit 1
fi

echo "✅ AWS credentials verified"

# Navigate to infra directory
cd infra

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Bootstrap CDK (if needed)
echo "🔧 Bootstrapping CDK..."
cdk bootstrap || echo "CDK already bootstrapped"

# Deploy stack
echo "🚀 Deploying infrastructure..."
cdk deploy --require-approval never

# Get outputs
echo "📊 Getting deployment outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name SaarthiAiStack \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 API Gateway URL: $API_URL"
echo ""
echo "⚠️  Don't forget to:"
echo "   1. Request Bedrock model access (Claude + Titan)"
echo "   2. Update frontend with API Gateway URL"
echo "   3. Test endpoints"
echo ""
