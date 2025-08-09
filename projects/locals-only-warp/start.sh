#!/bin/bash

echo "🏘️ Locals Only - Starting development server..."
echo ""

# Get the local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')

# Activate virtual environment
source .venv/bin/activate

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not found in environment"
    echo "   Make sure your .env file contains your Anthropic API key"
    echo ""
fi

# Start the Flask app
echo "🚀 Starting Flask server on port 5005"
echo "🌐 Local access: http://localhost:5005"
echo "📱 Network access: http://$LOCAL_IP:5005"
echo ""
echo "📲 To test on mobile devices:"
echo "   1. Connect your phone to the same WiFi network"
echo "   2. Open browser and go to: http://$LOCAL_IP:5005"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

python main.py
