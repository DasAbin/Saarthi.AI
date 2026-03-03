#!/bin/bash

# Test API Endpoints Script

set -e

if [ -z "$1" ]; then
    echo "Usage: ./test-endpoints.sh <API_GATEWAY_URL>"
    echo "Example: ./test-endpoints.sh https://xxxxx.execute-api.us-east-1.amazonaws.com/prod"
    exit 1
fi

API_URL=$1

echo "🧪 Testing Saarthi.AI API Endpoints..."
echo "API URL: $API_URL"
echo ""

# Health check
echo "1. Testing /health..."
curl -s "$API_URL/health" | jq '.' || echo "Failed"
echo ""

# Test query
echo "2. Testing /query..."
curl -s -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is PMAY?", "language": "en"}' | jq '.' || echo "Failed"
echo ""

# Test recommend
echo "3. Testing /recommend..."
curl -s -X POST "$API_URL/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "state": "Maharashtra",
    "income": 200000,
    "occupation": "Farmer"
  }' | jq '.' || echo "Failed"
echo ""

# Test grievance
echo "4. Testing /grievance..."
curl -s -X POST "$API_URL/grievance" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_type": "Water Supply",
    "description": "No water supply for 3 days",
    "location": "Ward 5, Sector 12, Mumbai"
  }' | jq '.' || echo "Failed"
echo ""

echo "✅ Testing complete!"
