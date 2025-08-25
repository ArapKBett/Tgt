#!/usr/bin/env python3
"""
Complete Telegram Script Runner Bot with Automatic Dependency Installation
"""

import os
import asyncio
import subprocess
import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Dict, Optional, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ScriptManager:
    def __init__(self):
        self.running_scripts: Dict[str, Dict] = {}
        self.scripts_dir = "user_scripts"
        self.logs_dir = "script_logs"
        os.makedirs(self.scripts_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
    def generate_script_id(self, user_id: int, content: str) -> str:
        """Generate unique script ID based on user and content hash"""
        hash_object = hashlib.md5(f"{user_id}_{content}_{datetime.now()}".encode())
        return hash_object.hexdigest()[:8]
    
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
    
    def get_file_extension(self, language: str) -> str:
        """Get appropriate file extension for language"""
        extensions = {
            'python': '.py',
            'c': '.c',
            'cpp': '.cpp',
            'java': '.java',
            'sh': '.sh'
        }
        return extensions.get(language, '.txt')
    
    def save_script(self, script_id: str, content: str, language: str) -> str:
        """Save script to file and return filepath"""
        extension = self.get_file_extension(language)
        filename = f"{script_id}{extension}"
        filepath = os.path.join(self.scripts_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        # Make script executable if it's a shell script
        if language == 'sh':
            os.chmod(filepath, 0o755)
        
        return filepath
    
    def is_safe_command(self, command: str) -> bool:
        """Basic security check"""
        dangerous = ['rm -rf', 'rm /', 'rmdir', 'del ', 'format', 'fdisk', 'wget', 'curl', 
                    'ssh', 'sudo', 'su ', 'mount', 'chmod 777', 'kill -9', ':(){ :|:& };:']
        
        command_lower = command.lower()
        return not any(danger in command_lower for danger in dangerous)
    
    def extract_python_imports(self, content: str) -> List[str]:
        """Extract import statements from Python code and return packages to install"""
        imports = []
        
        # Common packages that can be auto-installed safely
        safe_packages = {
            'requests': 'requests',
            'numpy': 'numpy', 
            'pandas': 'pandas',
            'matplotlib': 'matplotlib',
            'beautifulsoup4': 'beautifulsoup4',
            'bs4': 'beautifulsoup4',
            'selenium': 'selenium',
            'flask': 'flask',
            'fastapi': 'fastapi',
            'PIL': 'Pillow',
            'cv2': 'opencv-python',
            'yaml': 'PyYAML',
            'lxml': 'lxml',
            'psutil': 'psutil',
            'aiohttp': 'aiohttp',
            'colorama': 'colorama',
            'tqdm': 'tqdm',
            'discord': 'discord.py',
            'telebot': 'pyTelegramBotAPI',
            'pygame': 'pygame',
            'tkinter': None,  # Built-in
            'asyncio': None,  # Built-in
            'json': None,     # Built-in
            'os': None,       # Built-in
            'sys': None,      # Built-in
            'time': None,     # Built-in
            'datetime': None, # Built-in
            'random': None,   # Built-in
            'math': None,     # Built-in
            're': None,       # Built-in
            'urllib': None,   # Built-in
            'socket': None,   # Built-in
            'threading': None, # Built-in
            'multiprocessing': None, # Built-in
        }
        
        # Find import statements
        for line in content.split('\n'):
            line = line.strip()
            
            # Match: import package
            match = re.match(r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)', line)
            if match:
                module = match.group(1)
                if module in safe_packages and safe_packages[module]:
                    imports.append(safe_packages[module])
            
            # Match: from package import something
            match = re.match(r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', line)
            if match:
                module = match.group(1)
                if module in safe_packages and safe_packages[module]:
                    imports.append(safe_packages[module])
        
        return list(set(imports))  # Remove duplicates

    async def run_script(self, script_id: str, filepath: str, command: str, user_id: int):
        """Run script with automatic dependency installation for Python"""
        log_file = os.path.join(self.logs_dir, f"{script_id}.log")
        
        try:
            # Check if it's a Python script
            if filepath.endswith('.py'):
                # Read the script content
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Extract required packages
                required_packages = self.extract_python_imports(content)
                
                # Store process info
                self.running_scripts[script_id] = {
                    'user_id': user_id,
                    'process': None,
                    'command': command,
                    'filepath': filepath,
                    'log_file': log_file,
                    'start_time': datetime.now(),
                    'status': 'installing' if required_packages else 'running'
                }
                
                # Create log file and install dependencies if needed
                with open(log_file, 'w') as log:
                    log.write(f"Started at: {datetime.now()}\n")
                    log.write(f"Command: {command}\n")
                    
                    if required_packages:
                        log.write(f"📦 Auto-installing packages: {', '.join(required_packages)}\n")
                        log.write("=" * 60 + "\n")
                        log.flush()
                        
                        # Install each package
                        for package in required_packages:
                            log.write(f"\n🔄 Installing {package}...\n")
                            log.flush()
                            
                            try:
                                # Use pip to install package
                                process = await asyncio.create_subprocess_exec(
                                    'pip', 'install', '--user', '--quiet', package,
                                    stdout=asyncio.subprocess.PIPE,
                                    stderr=asyncio.subprocess.STDOUT
                                )
                                
                                # Stream pip output
                                while True:
                                    line = await process.stdout.readline()
                                    if not line:
                                        break
                                    decoded_line = line.decode('utf-8', errors='ignore')
                                    log.write(decoded_line)
                                    log.flush()
                                
                                await process.wait()
                                
                                if process.returncode == 0:
                                    log.write(f"✅ {package} installed successfully\n")
                                else:
                                    log.write(f"❌ Failed to install {package} (exit code: {process.returncode})\n")
                                    
                            except Exception as e:
                                log.write(f"❌ Error installing {package}: {e}\n")
                        
                        log.write("\n" + "=" * 60 + "\n")
                        log.write("🚀 Starting script execution...\n")
                        log.write("=" * 60 + "\n")
                        log.flush()
                    else:
                        log.write("No additional packages needed to install.\n")
                        log.write("-" * 50 + "\n")
                
                # Update status to running
                self.running_scripts[script_id]['status'] = 'running'
            else:
                # For non-Python scripts, use regular execution
                self.running_scripts[script_id] = {
                    'user_id': user_id,
                    'process': None,
                    'command': command,
                    'filepath': filepath,
                    'log_file': log_file,
                    'start_time': datetime.now(),
                    'status': 'running'
                }
                
                # Create log file
                with open(log_file, 'w') as log:
                    log.write(f"Started at: {datetime.now()}\n")
                    log.write(f"Command: {command}\n")
                    log.write("-" * 50 + "\n")
            
            # Now run the actual script
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=os.path.dirname(filepath)
            )
            
            self.running_scripts[script_id]['process'] = process
            
            # Stream script output to log file
            with open(log_file, 'a') as log:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    
                    decoded_line = line.decode('utf-8', errors='ignore')
                    log.write(decoded_line)
                    log.flush()
            
            # Wait for process to complete
            await process.wait()
            
            # Update status
            if script_id in self.running_scripts:
                self.running_scripts[script_id]['status'] = 'completed'
                
        except Exception as e:
            logger.error(f"Error running script {script_id}: {e}")
            if script_id in self.running_scripts:
                self.running_scripts[script_id]['status'] = 'error'
                
                # Write error to log file
                try:
                    with open(log_file, 'a') as log:
                        log.write(f"\n❌ Error: {e}\n")
                except:
                    pass
    
    def stop_script(self, script_id: str) -> bool:
        """Stop running script"""
        if script_id not in self.running_scripts:
            return False
        
        script_info = self.running_scripts[script_id]
        process = script_info.get('process')
        
        try:
            if process:
                process.terminate()
            script_info['status'] = 'stopped'
            return True
        except:
            return False
    
    def get_user_scripts(self, user_id: int) -> Dict[str, Dict]:
        """Get all scripts for a specific user"""
        user_scripts = {}
        for script_id, info in self.running_scripts.items():
            if info['user_id'] == user_id:
                user_scripts[script_id] = info
        return user_scripts
    
    def get_script_logs(self, script_id: str, lines: int = 50) -> str:
        """Get recent logs from script"""
        if script_id not in self.running_scripts:
            return "Script not found"
        
        log_file = self.running_scripts[script_id]['log_file']
        if not os.path.exists(log_file):
            return "No logs available"
        
        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
        except Exception as e:
            return f"Error reading logs: {e}"

class TelegramScriptBot:
    def __init__(self, token: str):
        self.token = token
        self.script_manager = ScriptManager()
        self.user_sessions = {}  # Track user sessions waiting for commands
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        welcome_msg = """
🤖 **Script Runner Bot with Auto-Install**

Send me your scripts and I'll run them continuously with automatic dependency installation!

**✨ New Features:**
• 📦 **Auto-installs Python packages** (requests, numpy, pandas, etc.)
• 🚀 **Instant execution** - no more "ModuleNotFoundError"
• 🔒 **Safe package management** - only trusted packages

**Commands:**
/start - Show this help
/list - List your running scripts  
/stop - Stop a script
/logs - View script logs

**Supported Languages:**
• Python (.py) - **With auto-install!**
• C (.c)
• C++ (.cpp)
• Java (.java)
• Shell (.sh)

**Example - Python with requests:**
```python
import requests
import time

while True:
    response = requests.get('https://api.github.com')
    print(f"Status: {response.status_code}")
    time.sleep(10)
```

**📦 Supported auto-install packages:**
requests, numpy, pandas, matplotlib, beautifulsoup4, selenium, flask, fastapi, PIL (Pillow), opencv-python, PyYAML, lxml, psutil, aiohttp, colorama, tqdm, discord.py, pygame

Just send me your code - I'll handle the rest! 🚀
        """
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    
    async def handle_script(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming script content"""
        user_id = update.effective_user.id
        content = update.message.text
        
        # Basic security checks
        if len(content) > 100000:  # 100KB limit
            await update.message.reply_text("❌ Script too large (max 100KB)")
            return
        
        # Check for dangerous content patterns
        dangerous_patterns = [
            'rm -rf /', 'format c:', ':(){ :|:& };:', 'sudo rm', '/etc/passwd',
            'import os.*system', 'subprocess.*shell=True.*rm', 'eval.*input'
        ]
        
        content_lower = content.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, content_lower):
                await update.message.reply_text("❌ Script contains potentially dangerous operations!")
                return
        
        # Detect language
        language = self.script_manager.detect_language(content)
        if not language:
            await update.message.reply_text(
                "❌ Couldn't detect script language.\n\n**Supported:** Python, C, C++, Java, Shell"
            )
            return
        
        # Generate script ID
        script_id = self.script_manager.generate_script_id(user_id, content)
        
        # Save script
        filepath = self.script_manager.save_script(script_id, content, language)
        
        # For Python scripts, show what packages will be auto-installed
        auto_install_info = ""
        if language == 'python':
            packages = self.script_manager.extract_python_imports(content)
            if packages:
                auto_install_info = f"\n📦 **Will auto-install:** {', '.join(packages)}"
        
        # Store session info
        self.user_sessions[user_id] = {
            'script_id': script_id,
            'content': content,
            'language': language,
            'filepath': filepath,
            'waiting_for_command': True
        }
        
        # Suggest default commands
        default_commands = {
            'python': f'python3 {os.path.basename(filepath)}',
            'c': f'gcc {os.path.basename(filepath)} -o {script_id} && ./{script_id}',
            'cpp': f'g++ {os.path.basename(filepath)} -o {script_id} && ./{script_id}',
            'java': f'javac {os.path.basename(filepath)} && java {script_id}',
            'sh': f'bash {os.path.basename(filepath)}'
        }
        
        suggested_command = default_commands.get(language, f'cat {os.path.basename(filepath)}')
        
        keyboard = [
            [InlineKeyboardButton(f"✅ Use: {suggested_command}", callback_data=f"use_default_{script_id}")],
            [InlineKeyboardButton("📝 Custom Command", callback_data=f"custom_command_{script_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{script_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ **{language.upper()} script detected!**\n"
            f"Script ID: `{script_id}`\n"
            f"File: `{os.path.basename(filepath)}`{auto_install_info}\n\n"
            f"**Suggested command:**\n`{suggested_command}`\n\n"
            f"Choose an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data.startswith("use_default_"):
            script_id = data.replace("use_default_", "")
            if user_id in self.user_sessions:
                session = self.user_sessions[user_id]
                if session['script_id'] == script_id:
                    language = session['language']
                    filepath = session['filepath']
                    
                    # Get default command
                    default_commands = {
                        'python': f'python3 {os.path.basename(filepath)}',
                        'c': f'gcc {os.path.basename(filepath)} -o {script_id} && ./{script_id}',
                        'cpp': f'g++ {os.path.basename(filepath)} -o {script_id} && ./{script_id}',
                        'java': f'javac {os.path.basename(filepath)} && java {script_id}',
                        'sh': f'bash {os.path.basename(filepath)}'
                    }
                    
                    command = default_commands.get(language, f'cat {os.path.basename(filepath)}')
                    
                    # Start running script
                    await self.start_script_execution(query, script_id, command, user_id)
        
        elif data.startswith("custom_command_"):
            script_id = data.replace("custom_command_", "")
            await query.edit_message_text(
                f"📝 **Enter execution command for script `{script_id}`:**\n\n"
                f"Send me the command as your next message.\n\n"
                f"**Examples:**\n"
                f"• `python3 script.py --args`\n"
                f"• `gcc script.c -o app && ./app arg1 arg2`\n"
                f"• `bash script.sh`",
                parse_mode='Markdown'
            )
            
            if user_id in self.user_sessions:
                self.user_sessions[user_id]['waiting_for_custom_command'] = True
        
        elif data.startswith("cancel_"):
            script_id = data.replace("cancel_", "")
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            
            await query.edit_message_text(f"❌ Script `{script_id}` cancelled.")
        
        elif data.startswith("stop_"):
            script_id = data.replace("stop_", "")
            success = self.script_manager.stop_script(script_id)
            if success:
                await query.edit_message_text(f"⏹️ Script `{script_id}` stopped successfully.")
            else:
                await query.edit_message_text(f"❌ Failed to stop script `{script_id}`.")
    
    async def handle_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle custom command input"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            return
        
        session = self.user_sessions[user_id]
        if not session.get('waiting_for_custom_command'):
            return
        
        command = update.message.text.strip()
        script_id = session['script_id']
        
        # Security check
        if not self.script_manager.is_safe_command(command):
            await update.message.reply_text("❌ Command contains dangerous operations!")
            return
        
        # Start running script with custom command
        await self.start_script_execution(update, script_id, command, user_id)
    
    async def start_script_execution(self, update_or_query, script_id: str, command: str, user_id: int):
        """Start executing the script"""
        session = self.user_sessions.get(user_id)
        if not session:
            return
        
        filepath = session['filepath']
        language = session['language']
        content = session['content']
        
        # Clean up session
        del self.user_sessions[user_id]
        
        # Enhanced message for Python scripts with auto-install info
        if language == 'python':
            packages = self.script_manager.extract_python_imports(content)
            if packages:
                message = f"🚀 **Script Starting with Auto-Install!**\n\n" \
                         f"Script ID: `{script_id}`\n" \
                         f"Language: {language.upper()}\n" \
                         f"Command: `{command}`\n" \
                         f"📦 **Installing:** {', '.join(packages)}\n\n" \
                         f"⏳ Please wait while dependencies are installed...\n\n" \
                         f"**Commands:**\n" \
                         f"• `/logs {script_id}` - View installation & execution output\n" \
                         f"• `/stop {script_id}` - Stop script\n" \
                         f"• `/list` - List all scripts"
            else:
                message = f"🚀 **Script Started!**\n\n" \
                         f"Script ID: `{script_id}`\n" \
                         f"Command: `{command}`\n" \
                         f"Status: ⏳ Running...\n\n" \
                         f"**Commands:**\n" \
                         f"• `/logs {script_id}` - View output\n" \
                         f"• `/stop {script_id}` - Stop script\n" \
                         f"• `/list` - List all scripts"
        else:
            message = f"🚀 **Script Started!**\n\n" \
                     f"Script ID: `{script_id}`\n" \
                     f"Command: `{command}`\n" \
                     f"Status: ⏳ Running...\n\n" \
                     f"**Commands:**\n" \
                     f"• `/logs {script_id}` - View output\n" \
                     f"• `/stop {script_id}` - Stop script\n" \
                     f"• `/list` - List all scripts"
        
        if hasattr(update_or_query, 'edit_message_text'):
            await update_or_query.edit_message_text(message, parse_mode='Markdown')
        else:
            await update_or_query.message.reply_text(message, parse_mode='Markdown')
        
        # Start running script in background
        asyncio.create_task(
            self.script_manager.run_script(script_id, filepath, command, user_id)
        )
    
    async def list_scripts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List user's running scripts"""
        user_id = update.effective_user.id
        scripts = self.script_manager.get_user_scripts(user_id)
        
        if not scripts:
            await update.message.reply_text("📭 No scripts found.\n\nSend me some code to get started!")
            return
        
        message = "📋 **Your Scripts:**\n\n"
        for script_id, info in scripts.items():
            status_emoji = {
                'running': '🟢',
                'completed': '✅',
                'stopped': '⏹️',
                'error': '❌',
                'installing': '📦'
            }.get(info['status'], '❓')
            
            status_text = {
                'installing': 'Installing packages...',
                'running': 'Running',
                'completed': 'Completed',
                'stopped': 'Stopped',
                'error': 'Error'
            }.get(info['status'], info['status'])
            
            message += f"{status_emoji} `{script_id}`\n"
            message += f"   📝 Command: `{info['command'][:50]}{'...' if len(info['command']) > 50 else ''}`\n"
            message += f"   ⏰ Started: {info['start_time'].strftime('%H:%M:%S')}\n"
            message += f"   📊 Status: {status_text}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def stop_script(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop a script"""
        if not context.args:
            await update.message.reply_text("❓ **Usage:** `/stop <script_id>`\n\nUse `/list` to see your scripts.")
            return
        
        script_id = context.args[0]
        user_id = update.effective_user.id
        
        # Check if user owns this script
        scripts = self.script_manager.get_user_scripts(user_id)
        if script_id not in scripts:
            await update.message.reply_text("❌ Script not found or not owned by you.\n\nUse `/list` to see your scripts.")
            return
        
        success = self.script_manager.stop_script(script_id)
        if success:
            await update.message.reply_text(f"⏹️ Script `{script_id}` stopped successfully!")
        else:
            await update.message.reply_text(f"❌ Failed to stop script `{script_id}`.")
    
    async def show_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show script logs"""
        if not context.args:
            await update.message.reply_text("❓ **Usage:** `/logs <script_id> [lines]`\n\nExample: `/logs abc123 30`")
            return
        
        script_id = context.args[0]
        lines = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 50
        user_id = update.effective_user.id
        
        # Check if user owns this script
        scripts = self.script_manager.get_user_scripts(user_id)
        if script_id not in scripts:
            await update.message.reply_text("❌ Script not found or not owned by you.\n\nUse `/list` to see your scripts.")
            return
        
        logs = self.script_manager.get_script_logs(script_id, lines)
        
        if not logs.strip() or logs == "No logs available":
            script_status = scripts[script_id].get('status', 'unknown')
            if script_status == 'installing':
                await update.message.reply_text(f"📦 Script `{script_id}` is installing dependencies...\n\nPlease wait and try again in a few moments.")
            else:
                await update.message.reply_text(f"📭 No logs available for `{script_id}` yet.\n\nThe script might still be starting up.")
            return
        
        # Split long logs into multiple messages
        max_length = 4000
        if len(logs) > max_length:
            await update.message.reply_text(f"📋 **Logs for `{script_id}` (showing last {lines} lines):**")
            for i in range(0, len(logs), max_length):
                chunk = logs[i:i + max_length]
                await update.message.reply_text(f"```\n{chunk}\n```", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"📋 **Logs for `{script_id}` (last {lines} lines):**\n```\n{logs}\n```", parse_mode='Markdown')
    
    async def handle_message_router(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route messages to appropriate handlers"""
        user_id = update.effective_user.id
        
        # Check if user is waiting for custom command
        if user_id in self.user_sessions and self.user_sessions[user_id].get('waiting_for_custom_command'):
            await self.handle_custom_command(update, context)
        else:
            await self.handle_script(update, context)
    
    def run(self):
        """Start the bot"""
        application = Application.builder().token(self.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("list", self.list_scripts))
        application.add_handler(CommandHandler("stop", self.stop_script))
        application.add_handler(CommandHandler("logs", self.show_logs))
        
        # Handle button callbacks
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Handle script content and custom commands
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message_router
        ))
        
        print("🤖 Bot started! Press Ctrl+C to stop.")
        print("📋 Send /start to your bot to begin!")
        application.run_polling()

def main():
    """Main function"""
    # Load configuration
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
    
    bot_token = config.get("bot_token", "")
    
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your bot token in config.json!")
        print("1. Create a bot with @BotFather on Telegram")
        print("2. Edit config.json and add your token")
        exit(1)
    
    bot = TelegramScriptBot(bot_token)
    bot.run()

if __name__ == "__main__":
    main()
