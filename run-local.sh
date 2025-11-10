#!/bin/bash

# Local development runner for snailmail API
# This script helps you run the API locally with either Ollama or a Cloud Run inference service

set -e

echo "snailmail API - Local Development"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cat > .env << EOF
SERVICE_TYPE=ollama
INFERENCE_SERVICE_URL=http://localhost:11434
PORT=5000
DEBUG=True
EOF
    echo "✅ Created .env file. Please update it if needed."
    echo ""
fi

# Source .env
export $(grep -v '^#' .env | xargs)

echo "Configuration:"
echo "  Service Type: $SERVICE_TYPE"
echo "  Inference URL: $INFERENCE_SERVICE_URL"
echo "  Port: $PORT"
echo ""

# Check if using Ollama
if [ "$SERVICE_TYPE" = "ollama" ]; then
    echo "🔍 Checking if Ollama is running..."
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "❌ Ollama is not running!"
        echo "   Start it with: ollama serve"
        echo "   Then run: ollama pull gemma3:1b"
        echo "   Then run: ollama pull gemma3:12b"
        exit 1
    fi

    # Check if model is available
    if ! curl -s http://localhost:11434/api/tags | grep -q "gemma3:12b"; then
        echo "⚠️  Gemma model not found. Pulling gemma3:12b..."
        ollama pull gemma3:12b
    fi

    if ! curl -s http://localhost:11434/api/tags | grep -q "gemma3:1b"; then
        echo "⚠️  Gemma model not found. Pulling gemma3:1b..."
        ollama pull gemma3:1b
    fi

    echo "✅ Ollama is ready"
    echo ""
fi

# Check if running in Docker or directly
if [ "$1" = "docker" ]; then
    echo "🐳 Building and running in Docker..."
    docker build -t snailmail-api .
    docker run -p $PORT:8080 \
        -e SERVICE_TYPE=$SERVICE_TYPE \
        -e INFERENCE_SERVICE_URL=$INFERENCE_SERVICE_URL \
        -e PORT=8080 \
        -e DEBUG=$DEBUG \
        -e WITTY_TEXT_MODEL=$WITTY_TEXT_MODEL \
        -e CUBE_ANALYSIS_MODEL=$CUBE_ANALYSIS_MODEL \
        --name snailmail-api \
        --rm \
        snailmail-api
else
    echo "🐍 Running with Python..."

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install requirements
    pip install -q -r requirements.txt

    echo "🚀 Starting API on http://localhost:$PORT"
    echo ""
    python main.py
fi
