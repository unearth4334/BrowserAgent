#!/bin/bash
# Quick start script for Civitai extraction

echo "🚀 Civitai Model Extractor - Quick Start"
echo "========================================"
echo ""

# Check if browser path is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <browser_path> [model_url]"
    echo ""
    echo "Example:"
    echo "  $0 /usr/bin/brave-browser 'https://civitai.com/models/277058?modelVersionId=1920523'"
    echo ""
    exit 1
fi

BROWSER_PATH="$1"
MODEL_URL="$2"

# Start the browser server
echo "📡 Starting browser server..."
echo "   Browser: $BROWSER_PATH"
echo "   URL: https://civitai.com/"
echo ""
echo "⚠️  Please login to Civitai when the browser opens"
echo "⚠️  Then press Enter in the terminal to continue"
echo ""

python examples/civitai/browser_server.py "$BROWSER_PATH" &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# If model URL provided, offer to extract it
if [ -n "$MODEL_URL" ]; then
    echo ""
    echo "🎯 Model URL provided: $MODEL_URL"
    echo ""
    echo "After logging in and starting the server, run:"
    echo "  python examples/civitai/extract_civitai_model.py '$MODEL_URL'"
    echo ""
fi

echo "Press Ctrl+C to stop the server when done"
wait $SERVER_PID
