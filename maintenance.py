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
