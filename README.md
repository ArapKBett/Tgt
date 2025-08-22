# Telegram Script Runner Bot

## ✨ Features

- **Multi-language Support**: Python, C, C++, Java, Shell scripts
- **Continuous Execution**: Scripts run indefinitely until stopped
- **Real-time Monitoring**: CPU and memory usage tracking
- **Security Features**: Sandboxing, command filtering, resource limits
- **User Management**: Per-user script limits and permissions
- **Logging**: Comprehensive execution logs and statistics
- **Database Integration**: Persistent storage with SQLite
- **Resource Management**: Automatic cleanup and limits

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- GCC/G++ compiler
- Java Development Kit (JDK)
- SQLite3

### Installation

1. **Clone or download the bot files**

2. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Get a Telegram bot token:**
   - Message @BotFather on Telegram
   - Create a new bot with `/newbot`
   - Copy the bot token

4. **Configure the bot:**
   ```bash
   nano config.json
   ```
   Add your bot token:
   ```json
   {
     "bot_token": "YOUR_BOT_TOKEN_HERE"
   }
   ```

5. **Start the bot:**
   ```bash
   ./start_bot.sh
   ```

## 📁 Project Structure

```
telegram-script-bot/
├── telegram_bot.py          # Main bot application
├── config_manager.py        # Configuration management
├── security_manager.py      # Security and sandboxing
├── resource_monitor.py      # Resource usage monitoring
├── database_manager.py      # Database operations
├── setup.sh                # Setup script
├── maintenance.py           # Maintenance utilities
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container deployment
├── config.json             # Bot configuration
├── user_scripts/           # User uploaded scripts
├── script_logs/            # Execution logs
└── backups/               # Database backups
```

## 🤖 Bot Commands

### User Commands

- `/start` - Show welcome message and help
- `/list` - List your running scripts
- `/stop <script_id>` - Stop a specific script
- `/logs <script_id> [lines]` - View script execution logs
- `/stats` - View your usage statistics

### Admin Commands (if configured)

- `/admin stats` - Global bot statistics
- `/admin users` - List all users
- `/admin kill <script_id>` - Force kill any script
- `/admin cleanup` - Clean old data

## 📝 Usage Examples

### 1. Python Script
```python
import time
import random

while True:
    print(f"Random number: {random.randint(1, 100)}")
    time.sleep(5)
```

**Execution command:** `python script.py`

### 2. C++ Script
```cpp
#include <iostream>
#include <chrono>
#include <thread>

int main() {
    int counter = 0;
    while(true) {
        std::cout << "Counter: " << ++counter << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(2));
    }
    return 0;
}
```

**Execution command:** `g++ script.cpp -o script && ./script`

### 3. Shell Script
```bash
#!/bin/bash
counter=0
while true; do
    echo "Iteration: $((++counter))"
    sleep 3
done
```

**Execution command:** `bash script.sh`

### 4. Java Script
```java
public class ContinuousRunner {
    public static void main(String[] args) {
        int count = 0;
        while(true) {
            System.out.println("Java count: " + (++count));
            try {
                Thread.sleep(1000);
            } catch(InterruptedException e) {
                break;
            }
        }
    }
}
```

**Execution command:** `javac ContinuousRunner.java && java ContinuousRunner`

## ⚙️ Configuration

### config.json Options

```json
{
  "bot_token": "YOUR_TOKEN",
  "allowed_users": [],
  "max_scripts_per_user": 10,
  "max_script_size": 100000,
  "script_timeout": 3600,
  "log_retention_days": 7,
  "execution_limits": {
    "memory_mb": 512,
    "cpu_percent": 50
  },
  "security": {
    "enable_sandbox": true,
    "blocked_commands": ["rm", "wget", "curl"],
    "blocked_imports": ["subprocess", "os.system"]
  }
}
```

### Security Settings

- **Sandboxing**: Uses firejail when available
- **Command filtering**: Blocks dangerous commands
- **Resource limits**: CPU and memory constraints
- **Import restrictions**: Prevents dangerous Python imports
- **User permissions**: Whitelist allowed users

## 🐳 Docker Deployment

Build and run with Docker:

```bash
docker build -t telegram-script-bot .
docker run -d \
  --name script-bot \
  -v $(pwd)/user_scripts:/app/user_scripts \
  -v $(pwd)/script_logs:/app/script_logs \
  -e TELEGRAM_BOT_TOKEN="YOUR_TOKEN" \
  telegram-script-bot
```

## 🔧 Maintenance

### Automatic Cleanup
```bash
# Clean files older than 7 days
python maintenance.py cleanup 7

# Create database backup
python maintenance.py backup

# View statistics
python maintenance.py stats
```

### Manual Operations
```bash
# View running processes
ps aux | grep python

# Check disk usage
du -h user_scripts/ script_logs/

# Monitor bot logs
tail -f bot.log
```

## 🛡️ Security Considerations

### Recommended Security Measures

1. **Run as non-root user**
2. **Use firewall rules**
3. **Enable sandboxing**
4. **Limit allowed users**
5. **Monitor resource usage**
6. **Regular updates**

### Default Security Features

- Command filtering (rm, wget, curl, etc.)
- Memory limits (512MB default)
- CPU limits (50% default)
- Execution timeouts (1 hour default)
- Import restrictions for Python
- Sandboxed execution with firejail

## 📊 Monitoring

### Resource Monitoring
- Real-time CPU and memory tracking
- Automatic process termination on limit exceed
- Resource usage statistics per script

### Logging
- Comprehensive execution logs
- Error tracking and reporting
- User activity monitoring

### Statistics
- Per-user usage statistics
- Global bot metrics
- Language usage trends

## 🐛 Troubleshooting

### Common Issues

**Bot doesn't respond**
- Check bot token in config.json
- Verify network connectivity
- Check bot permissions

**Scripts won't run**
- Verify compilers are installed
- Check file permissions
- Review security settings

**High resource usage**
- Adjust limits in config.json
- Enable sandboxing
- Monitor running scripts

**Database errors**
- Check disk space
- Verify SQLite installation
- Run database backup

### Debugging

```bash
# Enable debug logging
export TELEGRAM_BOT_DEBUG=1
python telegram_bot.py

# Check system resources
htop
df -h

# View bot logs
tail -f script_logs/bot.log
```

## 🔄 Updates

To update the bot:

1. Backup your database and config
2. Download new version
3. Run setup script again
4. Restore your config.json
5. Restart the bot

## 📄 License

This project is provided as-is for educational and personal use. Use responsibly and ensure compliance with your local laws and Telegram's Terms of Service.

## ⚠️ Disclaimer

Running user-provided code can be dangerous. This bot includes security measures, but no system is 100% secure. Use at your own risk and always run in a controlled environment.

## 🤝 Contributing

Feel free to submit issues, feature requests, and improvements. Please ensure all security measures are maintained in any contributions.

---

**Happy coding! 🚀**
