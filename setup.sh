#!/bin/bash

echo "🤖 Telegram Script Runner Bot Setup"
echo "=================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  This script should not be run as root for security reasons!"
   echo "Please run as a regular user."
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
echo "📋 Checking system requirements..."

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✅ Python 3 found: $PYTHON_VERSION"
else
    echo "❌ Python 3 is required but not installed!"
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

# Check pip
if command_exists pip3; then
    echo "✅ pip3 found"
else
    echo "❌ pip3 is required but not installed!"
    echo "Please install pip3 and try again."
    exit 1
fi

# Install compilers and interpreters
echo ""
echo "🔧 Installing compilers and interpreters..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command_exists apt; then
        # Debian/Ubuntu
        echo "📦 Installing packages for Debian/Ubuntu..."
        sudo apt update
        sudo apt install -y gcc g++ openjdk-11-jdk python3-dev build-essential
        
        # Optional: Install firejail for sandboxing
        echo "🔒 Installing firejail for sandboxing (optional)..."
        sudo apt install -y firejail || echo "⚠️  Firejail installation failed (optional)"
        
    elif command_exists yum; then
        # RedHat/CentOS
        echo "📦 Installing packages for RedHat/CentOS..."
        sudo yum install -y gcc gcc-c++ java-11-openjdk-devel python3-devel
        
    elif command_exists pacman; then
        # Arch Linux
        echo "📦 Installing packages for Arch Linux..."
        sudo pacman -S gcc jdk-openjdk python
        
    else
        echo "⚠️  Unknown Linux distribution. Please install gcc, g++, and Java manually."
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "📦 Installing packages for macOS..."
    
    if command_exists brew; then
        brew install gcc openjdk@11
        echo 'export PATH="/usr/local/opt/openjdk@11/bin:$PATH"' >> ~/.zshrc
    else
        echo "⚠️  Homebrew not found. Please install Xcode Command Line Tools and Java manually."
    fi
    
else
    echo "⚠️  Unsupported operating system: $OSTYPE"
    echo "Please install gcc, g++, Java, and Python manually."
fi

# Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."

# Create virtual environment (recommended)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p user_scripts
mkdir -p script_logs
mkdir -p backups

# Set permissions
chmod 755 user_scripts
chmod 755 script_logs
chmod 755 backups

# Create config file if it doesn't exist
echo ""
echo "⚙️  Setting up configuration..."

if [ ! -f "config.json" ]; then
    cat > config.json << EOF
{
  "bot_token": "",
  "allowed_users": [],
  "max_scripts_per_user": 10,
  "max_script_size": 100000,
  "script_timeout": 3600,
  "log_retention_days": 7,
  "supported_languages": ["python", "c", "cpp", "java", "sh"],
  "compile_timeouts": {
    "c": 30,
    "cpp": 60,
    "java": 60
  },
  "execution_limits": {
    "memory_mb": 512,
    "cpu_percent": 50
  },
  "security": {
    "enable_sandbox": true,
    "blocked_commands": [
      "rm", "rmdir", "del", "format", "fdisk",
      "wget", "curl", "nc", "netcat", "ssh",
      "sudo", "su", "chmod", "chown"
    ],
    "blocked_imports": [
      "subprocess", "os.system", "eval", "exec",
      "input", "raw_input", "__import__"
    ]
  }
}
EOF
    echo "✅ Created config.json - Please edit it to add your bot token!"
else
    echo "✅ config.json already exists"
fi

# Create systemd service file (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo ""
    echo "🔧 Creating systemd service..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    USERNAME=$(whoami)
    
    sudo tee /etc/systemd/system/telegram-script-bot.service > /dev/null << EOF
[Unit]
Description=Telegram Script Runner Bot
After=network.target

[Service]
Type=simple
User=$USERNAME
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$SCRIPT_DIR/venv/bin
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    echo "✅ Created systemd service file"
    echo "To enable auto-start: sudo systemctl enable telegram-script-bot"
    echo "To start service: sudo systemctl start telegram-script-bot"
fi

# Create startup script
echo ""
echo "📝 Creating startup scripts..."

cat > start_bot.sh << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
source venv/bin/activate
python telegram_bot.py
EOF

chmod +x start_bot.sh

cat > start_bot.bat << 'EOF'
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python telegram_bot.py
pause
EOF

echo "✅ Created start_bot.sh (Linux/Mac) and start_bot.bat (Windows)"

# Create maintenance script
cat > maintenance.py << 'EOF'
#!/usr/bin/env python3
"""
Maintenance script for the Telegram Script Runner Bot
"""
import os
import sys
import shutil
from datetime import datetime, timedelta
from database_manager import DatabaseManager

def cleanup_old_files(days=7):
    """Clean up old script files and logs"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    cleaned_files = 0
    
    # Clean script files
    if os.path.exists("user_scripts"):
        for filename in os.listdir("user_scripts"):
            filepath = os.path.join("user_scripts", filename)
            if os.path.getctime(filepath) < cutoff_date.timestamp():
                os.remove(filepath)
                cleaned_files += 1
    
    # Clean log files
    if os.path.exists("script_logs"):
        for filename in os.listdir("script_logs"):
            filepath = os.path.join("script_logs", filename)
            if os.path.getctime(filepath) < cutoff_date.timestamp():
                os.remove(filepath)
                cleaned_files += 1
    
    return cleaned_files

def backup_database():
    """Create a backup of the database"""
    if not os.path.exists("telegram_bot.db"):
        return False
    
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"telegram_bot_backup_{timestamp}.db")
    
    shutil.copy2("telegram_bot.db", backup_file)
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python maintenance.py <command>")
        print("Commands:")
        print("  cleanup [days] - Clean up old files (default: 7 days)")
        print("  backup         - Create database backup")
        print("  stats          - Show database statistics")
        return
    
    command = sys.argv[1].lower()
    
    if command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        print(f"Cleaning up files older than {days} days...")
        
        # Clean files
        cleaned_files = cleanup_old_files(days)
        print(f"Cleaned {cleaned_files} files")
        
        # Clean database
        db = DatabaseManager()
        cleaned_records = db.cleanup_old_data(days)
        print(f"Cleaned {cleaned_records} database records")
        
    elif command == "backup":
        print("Creating database backup...")
        if backup_database():
            print("✅ Backup created successfully")
        else:
            print("❌ No database found to backup")
    
    elif command == "stats":
        db = DatabaseManager()
        stats = db.get_global_statistics()
        
        print("\n📊 Bot Statistics:")
        print(f"Total users: {stats['total_users']}")
        print(f"Active users (24h): {stats['active_users']}")
        print(f"Total scripts: {stats['total_scripts']}")
        print(f"Running scripts: {stats['running_scripts']}")
        print(f"Popular languages: {stats['popular_languages']}")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
EOF

chmod +x maintenance.py

echo "✅ Created maintenance.py for database cleanup and backups"

# Final instructions
echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Get a bot token from @BotFather on Telegram"
echo "2. Edit config.json and add your bot token"
echo "3. Optionally, add allowed user IDs to config.json for security"
echo "4. Run the bot:"
echo "   ./start_bot.sh (Linux/Mac)"
echo "   start_bot.bat (Windows)"
echo "   OR: source venv/bin/activate && python telegram_bot.py"
echo ""
echo "🔧 Optional commands:"
echo "• Enable auto-start (Linux): sudo systemctl enable telegram-script-bot"
echo "• Start as service (Linux): sudo systemctl start telegram-script-bot"
echo "• View logs: journalctl -u telegram-script-bot -f"
echo "• Run maintenance: python maintenance.py cleanup"
echo "• Create backup: python maintenance.py backup"
echo ""
echo "⚠️  Security recommendations:"
echo "• Run the bot as a non-root user"
echo "• Use firewall to restrict network access"
echo "• Regularly update the system and Python packages"
echo "• Monitor resource usage and logs"
echo ""
echo "📖 For more information, check the README.md file"
