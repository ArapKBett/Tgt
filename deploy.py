#!/usr/bin/env python3
"""
Complete deployment script for Telegram Script Runner Bot
Handles free hosting platform deployment and configuration
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

class BotDeployer:
    def __init__(self):
        self.platforms = {
            'railway': self.deploy_railway,
            'render': self.deploy_render,
            'fly': self.deploy_fly,
            'heroku': self.deploy_heroku
        }
        
    def check_requirements(self):
        """Check if all required files exist"""
        required_files = [
            'telegram_bot.py',
            'config_manager.py',
            'security_manager.py',
            'resource_monitor.py',
            'database_manager.py',
            'requirements.txt',
            'Dockerfile'
        ]
        
        missing = []
        for file in required_files:
            if not os.path.exists(file):
                missing.append(file)
        
        if missing:
            print(f"❌ Missing required files: {', '.join(missing)}")
            return False
        
        print("✅ All required files found")
        return True
    
    def setup_config(self, platform='generic'):
        """Setup optimized configuration for hosting platform"""
        
        # Platform-specific optimizations
        configs = {
            'railway': {
                "max_scripts_per_user": 3,
                "execution_limits": {"memory_mb": 256, "cpu_percent": 30},
                "hosting": {"max_concurrent_scripts": 3}
            },
            'render': {
                "max_scripts_per_user": 2,
                "execution_limits": {"memory_mb": 128, "cpu_percent": 25},
                "hosting": {"max_concurrent_scripts": 2}
            },
            'fly': {
                "max_scripts_per_user": 4,
                "execution_limits": {"memory_mb": 512, "cpu_percent": 40},
                "hosting": {"max_concurrent_scripts": 4}
            },
            'heroku': {
                "max_scripts_per_user": 2,
                "execution_limits": {"memory_mb": 128, "cpu_percent": 20},
                "hosting": {"max_concurrent_scripts": 1}
            }
        }
        
        base_config = {
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "allowed_users": [],
            "admin_users": [],
            "max_script_size": 15000,
            "script_timeout": 900,
            "supported_languages": ["python", "c", "cpp", "java", "sh"],
            "security": {
                "enable_sandbox": False,
                "strict_mode": True,
                "blocked_commands": [
                    "rm", "rmdir", "del", "wget", "curl", "ssh",
                    "sudo", "su", "chmod", "chown", "mount", "kill"
                ],
                "blocked_imports": [
                    "subprocess", "os.system", "eval", "exec",
                    "socket", "urllib", "requests"
                ]
            },
            "logging": {
                "level": "WARNING",
                "log_retention_days": 1,
                "max_log_size_mb": 5
            },
            "hosting": {
                "memory_efficient": True,
                "aggressive_cleanup": True,
                "minimize_logs": True,
                "heartbeat_interval": 300
            }
        }
        
        # Apply platform-specific settings
        if platform in configs:
            platform_config = configs[platform]
            for key, value in platform_config.items():
                if isinstance(value, dict) and key in base_config:
                    base_config[key].update(value)
                else:
                    base_config[key] = value
        
        # Save config
        with open('config.json', 'w') as f:
            json.dump(base_config, f, indent=2)
        
        print(f"✅ Created optimized config for {platform}")
        return True
    
    def create_deployment_files(self, platform):
        """Create platform-specific deployment files"""
        
        if platform == 'railway':
            # Railway service configuration
            railway_config = {
                "$schema": "https://railway.app/railway.schema.json",
                "build": {"builder": "DOCKERFILE"},
                "deploy": {
                    "startCommand": "python telegram_bot.py",
                    "healthcheckPath": "/health",
                    "restartPolicyType": "ON_FAILURE",
                    "restartPolicyMaxRetries": 3
                }
            }
            
            with open('railway.json', 'w') as f:
                json.dump(railway_config, f, indent=2)
        
        elif platform == 'render':
            # Render service configuration
            render_config = {
                "services": [{
                    "type": "web",
                    "name": "telegram-script-bot",
                    "env": "python",
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "python telegram_bot.py",
                    "plan": "free",
                    "healthCheckPath": "/health",
                    "envVars": [{
                        "key": "TELEGRAM_BOT_TOKEN",
                        "sync": False
                    }]
                }]
            }
            
            with open('render.yaml', 'w') as f:
                import yaml
                yaml.dump(render_config, f)
        
        elif platform == 'fly':
            # Fly.io configuration
            fly_config = """
app = "telegram-script-bot"
primary_region = "iad"

[build]
dockerfile = "Dockerfile"

[env]
PORT = "8080"

[[services]]
internal_port = 8080
protocol = "tcp"

[[services.ports]]
port = 80
handlers = ["http"]
