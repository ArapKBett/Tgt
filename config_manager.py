import os
import json
from typing import Dict, Any

class Config:
    """Configuration manager for the Telegram bot"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or environment variables"""
        config = {
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "allowed_users": [],
            "max_scripts_per_user": 10,
            "max_script_size": 100000,  # 100KB
            "script_timeout": 3600,  # 1 hour
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
                "enable_sandbox": True,
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
        
        # Try to load from config file
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
    
    def is_user_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot"""
        allowed_users = self.config.get("allowed_users", [])
        return not allowed_users or user_id in allowed_users
    
    def add_allowed_user(self, user_id: int):
        """Add user to allowed users list"""
        allowed_users = self.config.get("allowed_users", [])
        if user_id not in allowed_users:
            allowed_users.append(user_id)
            self.set("allowed_users", allowed_users)
    
    def remove_allowed_user(self, user_id: int):
        """Remove user from allowed users list"""
        allowed_users = self.config.get("allowed_users", [])
        if user_id in allowed_users:
            allowed_users.remove(user_id)
            self.set("allowed_users", allowed_users)
