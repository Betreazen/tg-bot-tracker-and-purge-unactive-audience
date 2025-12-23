#!/bin/bash

# Telegram Bot - Quick Start Script

echo "🤖 Telegram Bot for Channel Audience Collection"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your values:"
    echo "   - BOT_TOKEN"
    echo "   - CHANNEL_ID"
    echo "   - CHANNEL_USERNAME"
    echo "   - ADMIN_IDS"
    echo ""
    echo "After editing .env, run this script again."
    exit 1
fi

echo "✅ .env file found"
echo ""

# Check if using Docker or local setup
read -p "Run with Docker? (y/n): " use_docker

if [ "$use_docker" = "y" ]; then
    echo ""
    echo "🐳 Starting with Docker Compose..."
    docker-compose up -d
    echo ""
    echo "✅ Bot started!"
    echo ""
    echo "📊 View logs: docker-compose logs -f bot"
    echo "🛑 Stop bot: docker-compose down"
else
    echo ""
    echo "🐍 Starting local setup..."
    
    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python -m venv venv
    fi
    
    # Activate venv
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    
    # Create logs directory
    mkdir -p logs
    
    # Run bot
    echo ""
    echo "🚀 Starting bot..."
    python bot.py
fi
