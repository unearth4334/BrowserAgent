#!/bin/bash
# Test script demonstrating the new browser server design

echo "============================================"
echo "Browser Server Interactive Design Test"
echo "============================================"
echo ""
echo "This script demonstrates:"
echo "1. Starting server in background with wait_for_auth=True"
echo "2. Server returns console with interactive prompt"
echo "3. User can type 'ready' OR send via client"
echo "4. Server continues to main loop after 'ready'"
echo ""

# Kill any existing servers
pkill -9 -f "browser-agent server" 2>/dev/null
pkill -9 -f "browser_server" 2>/dev/null
sleep 1

echo "Step 1: Starting browser server in background..."
echo "Command: browser-agent server <url> --browser-exe /usr/bin/brave-browser --port 9999 &"
echo ""

cd /home/sdamk/dev/BrowserAgent
.venv/bin/browser-agent server "https://www.patreon.com/collection/251893?view=expanded" --browser-exe /usr/bin/brave-browser --port 9999 &

SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"
echo ""

# Wait for server to initialize
sleep 5

echo ""
echo "Step 2: Server is now waiting for authentication..."
echo "        You can either:"
echo "        a) Type 'ready' in the server terminal"
echo "        b) Run: python -m browser_agent.server.browser_client ready"
echo "        c) Use the test script: .venv/bin/python test_ready_command.py"
echo ""
echo "Step 3: Demonstrating option (c) - sending 'ready' via client..."
echo ""

.venv/bin/python test_ready_command.py

echo ""
echo "============================================"
echo "Server is now in main interactive loop!"
echo ""
echo "You can interact with it by:"
echo "1. Typing commands in the server terminal: status, quit, help"
echo "2. Sending commands via client:"
echo "   .venv/bin/python -m browser_agent.server.browser_client ping"
echo "   .venv/bin/python -m browser_agent.server.browser_client info"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================"

# Keep the script running
wait $SERVER_PID
