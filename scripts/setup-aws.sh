#!/bin/bash

# AWS Setup Script for Saarthi.AI

set -e

echo "🔧 Setting up AWS for Saarthi.AI..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found"
    echo "Install: https://aws.amazon.com/cli/"
    exit 1
fi

# Check credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region || echo "us-east-1")

echo "✅ AWS Account: $ACCOUNT_ID"
echo "✅ Region: $REGION"
echo ""

# Check Bedrock access
echo "🤖 Checking Bedrock model access..."
MODELS=$(aws bedrock list-foundation-models --region $REGION --query 'modelSummaries[*].modelId' --output text 2>/dev/null || echo "")

if [[ $MODELS == *"claude"* ]]; then
    echo "✅ Claude models accessible"
else
    echo "⚠️  Claude models not accessible"
    echo "   Request access: AWS Console → Bedrock → Model access"
fi

if [[ $MODELS == *"titan"* ]]; then
    echo "✅ Titan models accessible"
else
    echo "⚠️  Titan models not accessible"
    echo "   Request access: AWS Console → Bedrock → Model access"
fi

echo ""
echo "📋 Setup checklist:"
echo "  [ ] AWS CLI configured"
echo "  [ ] Bedrock model access requested"
echo "  [ ] CDK installed (npm install -g aws-cdk)"
echo "  [ ] Python 3.12+ installed"
echo "  [ ] Node.js 18+ installed"
echo ""
echo "Ready to deploy! 🚀"
