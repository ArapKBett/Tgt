#!/bin/bash

echo "🔧 Quick Fix for Telegram Bot Installation"
echo "========================================="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected. Creating one..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Created virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    echo "✅ Activated virtual environment"
fi

# Upgrade pip first
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install required packages
echo "📦 Installing required packages..."
pip install python-telegram-bot==20.7
pip install psutil
pip install aiofiles
pip install aiohttp

# Verify installation
echo ""
echo "🔍 Verifying installation..."
python3 -c "import telegram; print('✅ python-telegram-bot installed successfully')" || echo "❌ Failed to import telegram"
python3 -c "import psutil; print('✅ psutil installed successfully')" || echo "❌ Failed to import psutil"

# Check if bot token is set
if [ ! -f "config.json" ]; then
    echo ""
    echo "📝 Creating basic config.json..."
    cat > config.json << 'EOF'
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "allowed_users": [],
  "max_scripts_per_user": 5,
  "max_script_size": 50000,
  "script_timeout": 1800,
  "execution_limits": {
    "memory_mb": 256,
    "cpu_percent": 30
  },
  "security": {
    "enable_sandbox": false,
    "blocked_commands": ["rm", "wget", "curl", "ssh", "sudo"],
    "blocked_imports": ["subprocess", "os.system", "eval"]
  },
  "logging": {
    "level": "INFO",
    "log_retention_days": 3
  }
}
EOF
    echo "✅ Created config.json"
fi

# Create necessary directories
mkdir -p user_scripts script_logs backups

echo ""
echo "🎉 Installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit config.json and add your bot token:"
echo "   nano config.json"
echo ""
echo "2. Get bot token from @BotFather on Telegram"
echo ""
echo "3. Start the bot:"
echo "   source venv/bin/activate"
echo "   python telegram_bot.py"
echo ""
echo "Or use the startup script:"
echo "   ./start_bot.sh"
