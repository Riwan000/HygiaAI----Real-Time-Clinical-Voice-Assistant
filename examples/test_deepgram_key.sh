#!/bin/bash
# Test Deepgram API Key validity
# Usage: ./test_deepgram_key.sh YOUR_API_KEY

API_KEY=${1:-"your_api_key_here"}

if [ "$API_KEY" == "your_api_key_here" ]; then
    echo "Usage: ./test_deepgram_key.sh YOUR_API_KEY"
    exit 1
fi

echo "Testing Deepgram API Key..."
echo "API Key: ${API_KEY:0:10}..."

# Test with a simple API call
curl -X GET "https://api.deepgram.com/v1/projects" \
  -H "Authorization: Token $API_KEY" \
  -H "Content-Type: application/json" 2>/dev/null | head -20

echo ""
echo "If you see project data, the API key is valid."
echo "If you see an error, the API key is invalid or expired."

