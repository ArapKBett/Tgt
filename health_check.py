# health_check.py - Health endpoint for hosting platforms
from aiohttp import web
import json
import asyncio
import threading
import os
import psutil
from datetime import datetime

class HealthMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.health_checks = 0
        
    async def health_endpoint(self, request):
        """Health check endpoint for hosting platforms"""
        self.health_checks += 1
        
        # Basic health metrics
        uptime = datetime.now() - self.start_time
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent if os.path.exists('/') else 0
        
        status = {
            "status": "healthy",
            "uptime": str(uptime).split('.')[0],
            "health_checks": self.health_checks,
            "memory_usage": f"{memory_usage:.1f}%",
            "disk_usage": f"{disk_usage:.1f}%",
            "timestamp": datetime.now().isoformat()
        }
        
        return web.json_response(status)
    
    async def metrics_endpoint(self, request):
        """Detailed metrics endpoint"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Bot metrics (if database exists)
            bot_metrics = {}
            if os.path.exists('telegram_bot.db'):
                try:
                    import sqlite3
                    conn = sqlite3.connect('telegram_bot.db')
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT COUNT(*) FROM scripts WHERE status='running'")
                    running_scripts = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM users")
                    total_users = cursor.fetchone()[0]
                    
                    bot_metrics = {
                        "running_scripts": running_scripts,
                        "total_users": total_users
                    }
                    conn.close()
                except:
                    pass
            
            metrics = {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent
                    },
                    "disk": {
                        "total": disk.total,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100
                    }
                },
                "bot": bot_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            return web.json_response(metrics)
            
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

def start_health_server(port=8080):
    """Start health check server"""
    monitor = HealthMonitor()
    
    app = web.Application()
    app.router.add_get('/health', monitor.health_endpoint)
    app.router.add_get('/metrics', monitor.metrics_endpoint)
    app.router.add_get('/', monitor.health_endpoint)  # Root endpoint
    
    def run_server():
        web.run_app(app, host='0.0.0.0', port=port, access_log=None)
    
    # Run in separate thread to not block main bot
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print(f"🏥 Health server started on port {port}")
    return server_thread

# keep_alive.py - Keep hosting platform awake
import asyncio
import aiohttp
import os
import random
from datetime import datetime

class KeepAlive:
    def __init__(self, url=None):
        self.url = url or os.getenv('APP_URL')
        self.ping_count = 0
        
    async def ping_self(self):
        """Ping own health endpoint to stay awake"""
        if not self.url:
            return
            
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.url}/health") as response:
                    if response.status == 200:
                        self.ping_count += 1
                        print(f"🏓 Keep-alive ping #{self.ping_count} - Status: {response.status}")
                    else:
                        print(f"⚠️  Keep-alive ping failed - Status: {response.status}")
        except Exception as e:
            print(f"❌ Keep-alive error: {e}")
    
    async def start_keep_alive(self, interval=300):
        """Start keep-alive loop (5 minutes default)"""
        print(f"🔄 Starting keep-alive service (interval: {interval}s)")
        
        while True:
            await asyncio.sleep(interval + random.randint(-30, 30))  # Add randomness
            await self.ping_self()

# webhook_handler.py - Alternative to polling for some platforms
from aiohttp import web
import json
import ssl
import asyncio

class WebhookHandler:
    def __init__(self, bot_application, webhook_path="/webhook"):
        self.bot_application = bot_application
        self.webhook_path = webhook_path
        
    async def webhook_handler(self, request):
        """Handle incoming webhook requests"""
        try:
            data = await request.json()
            
            # Process the update
            from telegram import Update
            update = Update.de_json(data, self.bot_application.bot)
            
            # Queue the update for processing
            await self.bot_application.update_queue.put(update)
            
            return web.Response(text="OK")
            
        except Exception as e:
            print(f"Webhook error: {e}")
            return web.Response(text="Error", status=500)
    
    def create_webhook_app(self):
        """Create webhook application"""
        app = web.Application()
        app.router.add_post(self.webhook_path, self.webhook_handler)
        
        # Add health check
        from health_check import HealthMonitor
        monitor = HealthMonitor()
        app.router.add_get('/health', monitor.health_endpoint)
        
        return app

# optimized_requirements.txt for free hosting
REQUIREMENTS_MINIMAL = """
python-telegram-bot==20.7
aiohttp==3.8.6
aiofiles==23.1.0
psutil==5.9.5
"""

# environment_setup.py - Environment configuration
import os
import json

def setup_environment():
    """Setup environment variables and config for hosting"""
    
    # Default configuration for free hosting
    default_config = {
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "allowed_users": [],
        "max_scripts_per_user": 3,
        "max_script_size": 20000,
        "script_timeout": 900,  # 15 minutes max
        "execution_limits": {
            "memory_mb": 128,
            "cpu_percent": 25,
            "max_processes": 2
        },
        "security": {
            "enable_sandbox": False,  # Most free hosts don't support
            "strict_mode": True,
            "blocked_commands": [
                "rm", "rmdir", "del", "wget", "curl", "ssh",
                "sudo", "su", "chmod", "chown", "mount"
            ]
        },
        "hosting": {
            "memory_efficient": True,
            "aggressive_cleanup": True,
            "max_concurrent_scripts": 2,
            "heartbeat_interval": 300
        }
    }
    
    # Write config if it doesn't exist
    if not os.path.exists('config.json'):
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        print("✅ Created optimized config.json for hosting")
    
    # Environment variables
    required_vars = ['TELEGRAM_BOT_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

# deployment_monitor.py - Monitor deployment health
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

class DeploymentMonitor:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url
        self.last_alert = None
        
    async def check_bot_health(self):
        """Check if bot is responding"""
        try:
            # Simple health check - can be expanded
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "status": "healthy",
                "memory_usage": "unknown",
                "active_scripts": 0
            }
            
            return health_status
            
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def send_alert(self, message):
        """Send alert to webhook (Discord, Slack, etc.)"""
        if not self.webhook_url:
            return
            
        # Rate limit alerts (max 1 per hour)
        if self.last_alert and datetime.now() - self.last_alert < timedelta(hours=1):
            return
        
        try:
            alert_data = {
                "content": f"🚨 Bot Alert: {message}",
                "timestamp": datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                await session.post(self.webhook_url, json=alert_data)
            
            self.last_alert = datetime.now()
            
        except Exception as e:
            print(f"Failed to send alert: {e}")
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        print("🔍 Starting deployment monitor...")
        
        while True:
            try:
                health = await self.check_bot_health()
                
                if health['status'] != 'healthy':
                    await self.send_alert(f"Bot unhealthy: {health.get('error', 'Unknown error')}")
                
                await asyncio.sleep(600)  # Check every 10 minutes
                
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes

if __name__ == "__main__":
    # Test health server
    start_health_server(8080)
