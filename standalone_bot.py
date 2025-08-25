#!/usr/bin/env python3
"""
Standalone Telegram Script Runner Bot
No external module dependencies - only uses built-in Python modules
"""

import os
import asyncio
import subprocess
import tempfile
import hashlib
import json
import time
import threading
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Optional
from urllib.request import urlopen, Request
from urllib.parse import urlencode
import ssl

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleTelegramBot:
    """Simple Telegram bot using only built-in Python modules"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.running_scripts = {}
        self.user_sessions = {}
        self.offset = 0
        
        # Setup directories
        os.makedirs("user_scripts", exist_ok=True)
        os.makedirs("script_logs", exist_ok=True)
        
        # Setup database
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect('telegram_bot.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                script_id TEXT PRIMARY KEY,
                user_id INTEGER,
                language TEXT,
                content TEXT,
                command TEXT,
                status TEXT DEFAULT 'created',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def make_request(self, method: str, data: dict = None):
        """Make HTTP request to Telegram API"""
        url = f"{self.base_url}/{method}"
        
        try:
            if data:
                data = urlencode(data).encode('utf-8')
                req = Request(url, data=data)
            else:
                req = Request(url)
            
            # Create SSL context that doesn't verify certificates (for compatibility)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            response = urlopen(req, context=ctx, timeout=30)
            return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def send_message(self, chat_id: int, text: str, reply_markup=None):
        """Send message to Telegram chat"""
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        return self.make_request('sendMessage', data)
    
    def get_updates(self):
        """Get updates from Telegram"""
        data = {
            'offset': self.offset,
            'timeout': 10
        }
        return self.make_request('getUpdates', data)
    
    def detect_language(self, content: str) -> Optional[str]:
        """Detect script language based on content"""
        content = content.strip()
        
        # Check for shebang
        if content.startswith('#!/bin/bash') or content.startswith('#!/bin/sh'):
            return 'sh'
        elif content.startswith('#!/usr/bin/python') or content.startswith('#!/usr/bin/env python'):
            return 'python'
        
        # Check for common patterns
        if any(keyword in content for keyword in ['import ', 'def ', 'print(', 'if __name__']):
            return 'python'
        elif any(keyword in content for keyword in ['#include', 'int main', 'printf', 'cout']):
            return 'cpp' if 'cout' in content or 'std::' in content else 'c'
        elif any(keyword in content for keyword in ['public class', 'public static void main', 'System.out']):
            return 'java'
        elif any(keyword in content for keyword in ['echo', 'cd ', 'ls ', 'mkdir']):
            return 'sh'
        
        return None
    
    def generate_script_id(self, user_id: int, content: str) -> str:
        """Generate unique script ID"""
        hash_object = hashlib.md5(f"{user_id}_{content}_{time.time()}".encode())
        return hash_object.hexdigest()[:8]
    
    def save_script(self, script_id: str, content: str, language: str) -> str:
        """Save script to file"""
        extensions = {
            'python': '.py',
            'c': '.c',
            'cpp': '.cpp',
            'java': '.java',
            'sh': '.sh'
        }
        
        extension = extensions.get(language, '.txt')
        filename = f"{script_id}{extension}"
        filepath = os.path.join("user_scripts", filename)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        if language == 'sh':
            os.chmod(filepath, 0o755)
        
        return filepath
    
    def is_safe_command(self, command: str) -> bool:
        """Basic security check for commands"""
        dangerous = ['rm ', 'rmdir', 'del ', 'format', 'fdisk', 'wget', 'curl', 
                    'ssh', 'sudo', 'su ', '&&rm', ';rm', '|rm', '&rm']
        
        command_lower = command.lower()
        return not any(danger in command_lower for danger in dangerous)
    
    def run_script(self, script_id: str, command: str, filepath: str):
        """Run script in background thread"""
        def execute():
            try:
                log_file = os.path.join("script_logs", f"{script_id}.log")
                
                with open(log_file, 'w') as log:
                    log.write(f"Started at: {datetime.now()}\n")
                    log.write(f"Command: {command}\n")
                    log.write("-" * 50 + "\n")
                    log.flush()
                    
                    # Execute command
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        cwd=os.path.dirname(filepath),
                        universal_newlines=True,
                        bufsize=1
                    )
                    
                    self.running_scripts[script_id]['process'] = process
                    
                    # Stream output
                    for line in process.stdout:
                        log.write(line)
                        log.flush()
                    
                    process.wait()
                    
                    if script_id in self.running_scripts:
                        self.running_scripts[script_id]['status'] = 'completed'
                        
            except Exception as e:
                logger.error(f"Script execution error: {e}")
                if script_id in self.running_scripts:
                    self.running_scripts[script_id]['status'] = 'error'
        
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
    
    def handle_message(self, message: dict):
        """Handle incoming message"""
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        text = message.get('text', '')
        
        if text.startswith('/start'):
            welcome = """🤖 **Script Runner Bot**
            
Send me your scripts and I'll run them continuously!

**Supported languages:**
• Python
• C/C++
• Java  
• Shell scripts

**Commands:**
/list - List running scripts
/stop <script_id> - Stop a script
/logs <script_id> - View script output

Just send me your code to get started!"""
            
            self.send_message(chat_id, welcome)
            
        elif text.startswith('/list'):
            user_scripts = [(k, v) for k, v in self.running_scripts.items() if v['user_id'] == user_id]
            
            if not user_scripts:
                self.send_message(chat_id, "📭 No running scripts found.")
                return
            
            message_text = "📋 **Your Scripts:**\n\n"
            for script_id, info in user_scripts:
                status_emoji = '🟢' if info['status'] == 'running' else '✅'
                message_text += f"{status_emoji} `{script_id}` - {info['language']}\n"
                message_text += f"   Command: `{info['command']}`\n\n"
            
            self.send_message(chat_id, message_text)
            
        elif text.startswith('/stop'):
            parts = text.split()
            if len(parts) != 2:
                self.send_message(chat_id, "Usage: /stop <script_id>")
                return
            
            script_id = parts[1]
            if script_id in self.running_scripts and self.running_scripts[script_id]['user_id'] == user_id:
                try:
                    process = self.running_scripts[script_id].get('process')
                    if process:
                        process.terminate()
                    self.running_scripts[script_id]['status'] = 'stopped'
                    self.send_message(chat_id, f"⏹️ Script `{script_id}` stopped.")
                except:
                    self.send_message(chat_id, f"❌ Failed to stop script `{script_id}`.")
            else:
                self.send_message(chat_id, "❌ Script not found.")
                
        elif text.startswith('/logs'):
            parts = text.split()
            if len(parts) != 2:
                self.send_message(chat_id, "Usage: /logs <script_id>")
                return
            
            script_id = parts[1]
            log_file = os.path.join("script_logs", f"{script_id}.log")
            
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        logs = f.read()[-3000:]  # Last 3000 characters
                    
                    if logs:
                        self.send_message(chat_id, f"📋 **Logs for `{script_id}`:**\n```\n{logs}\n```")
                    else:
                        self.send_message(chat_id, "📭 No logs available yet.")
                except:
                    self.send_message(chat_id, "❌ Failed to read logs.")
            else:
                self.send_message(chat_id, "❌ Log file not found.")
                
        else:
            # Handle script content
            if user_id in self.user_sessions and self.user_sessions[user_id].get('waiting_for_command'):
                # User is providing execution command
                command = text.strip()
                session = self.user_sessions[user_id]
                script_id = session['script_id']
                filepath = session['filepath']
                language = session['language']
                
                if not self.is_safe_command(command):
                    self.send_message(chat_id, "❌ Command contains dangerous operations!")
                    return
                
                # Start execution
                self.running_scripts[script_id] = {
                    'user_id': user_id,
                    'command': command,
                    'language': language,
                    'filepath': filepath,
                    'status': 'running',
                    'start_time': datetime.now()
                }
                
                self.run_script(script_id, command, filepath)
                
                # Save to database
                conn = sqlite3.connect('telegram_bot.db')
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scripts (script_id, user_id, language, content, command, status)
                    VALUES (?, ?, ?, ?, ?, 'running')
                """, (script_id, user_id, language, session['content'], command))
                conn.commit()
                conn.close()
                
                del self.user_sessions[user_id]
                
                self.send_message(chat_id, f"""🚀 **Script started!**

Script ID: `{script_id}`
Language: {language}
Command: `{command}`

Use /logs {script_id} to view output
Use /stop {script_id} to stop execution""")
                
            else:
                # New script content
                language = self.detect_language(text)
                
                if not language:
                    self.send_message(chat_id, "❌ Couldn't detect script language. Supported: Python, C, C++, Java, Shell")
                    return
                
                script_id = self.generate_script_id(user_id, text)
                filepath = self.save_script(script_id, text, language)
                
                # Default commands
                default_commands = {
                    'python': f'python {os.path.basename(filepath)}',
                    'c': f'gcc {os.path.basename(filepath)} -o {script_id} && ./{script_id}',
                    'cpp': f'g++ {os.path.basename(filepath)} -o {script_id} && ./{script_id}',
                    'java': f'javac {os.path.basename(filepath)} && java {script_id}',
                    'sh': f'bash {os.path.basename(filepath)}'
                }
                
                suggested = default_commands.get(language, f'cat {os.path.basename(filepath)}')
                
                self.user_sessions[user_id] = {
                    'script_id': script_id,
                    'content': text,
                    'language': language,
                    'filepath': filepath,
                    'waiting_for_command': True
                }
                
                self.send_message(chat_id, f"""✅ **{language.upper()} script detected!**

Script ID: `{script_id}`
File: `{os.path.basename(filepath)}`

**Suggested command:** `{suggested}`

Please send the execution command, or use the suggested one above.""")
    
    def run(self):
        """Main bot loop"""
        print("🤖 Starting Telegram Script Runner Bot...")
        print("Press Ctrl+C to stop.")
        
        while True:
            try:
                updates = self.get_updates()
                
                if updates and updates.get('ok'):
                    for update in updates['result']:
                        self.offset = update['update_id'] + 1
                        
                        if 'message' in update:
                            self.handle_message(update['message'])
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n👋 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Bot error: {e}")
                time.sleep(5)

def main():
    """Main function"""
    # Load config
    config_file = 'config.json'
    
    if not os.path.exists(config_file):
        print("❌ config.json not found!")
        print("Creating basic config file...")
        
        config = {
            "bot_token": "YOUR_BOT_TOKEN_HERE"
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Created config.json")
        print("Please edit config.json and add your bot token from @BotFather")
        return
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    bot_token = config.get('bot_token', '')
    
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your bot token in config.json!")
        print("1. Message @BotFather on Telegram")
        print("2. Create a new bot with /newbot")
        print("3. Copy the token to config.json")
        return
    
    # Start bot
    bot = SimpleTelegramBot(bot_token)
    bot.run()

if __name__ == "__main__":
    main()
