#!/bin/bash

# Locals Only - Enhanced Startup Script

echo "🗺️ Locals Only - Enhanced with Google Maps"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env and add your API keys:"
    echo "   - GOOGLE_MAPS_API_KEY (required)"
    echo "   - ANTHROPIC_API_KEY (optional)"
    echo "   - SECRET_KEY (required)"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check for required API keys
source .env

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo "❌ GOOGLE_MAPS_API_KEY not set in .env file"
    echo "   Get your API key from: https://console.cloud.google.com/"
    echo "   Enable these APIs:"
    echo "   - Geocoding API"
    echo "   - Maps JavaScript API"
    echo "   - Places API"
    echo "   - And others listed in .env.example"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "❌ SECRET_KEY not set in .env file"
    echo "   Generate a random secret key for Flask sessions"
    exit 1
fi

echo "✅ Environment configuration looks good!"

# Check if Python dependencies are installed
if ! python -c "import flask, requests, langchain" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    
    # Try pyproject.toml first, then requirements.txt
    if [ -f pyproject.toml ]; then
        echo "   Using pyproject.toml..."
        pip install -e .
    elif [ -f requirements.txt ]; then
        echo "   Using requirements.txt..."
        pip install -r requirements.txt
    else
        echo "❌ No dependency file found (pyproject.toml or requirements.txt)"
        exit 1
    fi
fi

echo "🚀 Starting Locals Only Enhanced..."
echo ""
echo "🌐 Application will be available at:"
echo "   http://localhost:5005"
echo ""
echo "🎯 Features available:"
echo "   ✓ Google Maps integration"
echo "   ✓ Google Places API recommendations"
echo "   ✓ Onboarding flow"
echo "   ✓ Interactive dashboard"
echo "   ✓ AI-enhanced descriptions (if Anthropic key provided)"
echo ""
echo "📱 Try it on different devices for responsive experience!"
echo ""
echo "🔄 Starting Flask development server..."
echo "   (Press Ctrl+C to stop)"
echo ""

# Start the application
python app.py
