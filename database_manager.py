import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    """Manage persistent storage for the bot"""
    
    def __init__(self, db_path: str = "telegram_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_allowed BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Scripts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scripts (
                    script_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    language TEXT,
                    content TEXT,
                    command TEXT,
                    filepath TEXT,
                    status TEXT DEFAULT 'created',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Execution logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_id TEXT,
                    log_content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (script_id) REFERENCES scripts (script_id)
                )
            """)
            
            # System statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    metric_value TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Resource usage table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resource_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_id TEXT,
                    cpu_percent REAL,
                    memory_mb REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (script_id) REFERENCES scripts (script_id)
                )
            """)
            
            conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add or update user information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_seen)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, username, first_name, last_name))
            conn.commit()
    
    def is_user_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_allowed FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else True  # Allow new users by default
    
    def set_user_permission(self, user_id: int, is_allowed: bool):
        """Set user permission"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET is_allowed = ? WHERE user_id = ?
            """, (is_allowed, user_id))
            conn.commit()
    
    def add_script(self, script_id: str, user_id: int, language: str, content: str, 
                   command: str, filepath: str) -> bool:
        """Add a new script to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scripts (script_id, user_id, language, content, command, filepath)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (script_id, user_id, language, content, command, filepath))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_script_status(self, script_id: str, status: str, error_message: str = None):
        """Update script status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            timestamp_field = None
            if status in ['running', 'started']:
                timestamp_field = 'started_at'
            elif status in ['completed', 'stopped', 'killed', 'error']:
                timestamp_field = 'completed_at'
            
            if timestamp_field:
                cursor.execute(f"""
                    UPDATE scripts 
                    SET status = ?, error_message = ?, {timestamp_field} = CURRENT_TIMESTAMP
                    WHERE script_id = ?
                """, (status, error_message, script_id))
            else:
                cursor.execute("""
                    UPDATE scripts SET status = ?, error_message = ? WHERE script_id = ?
                """, (status, error_message, script_id))
            
            conn.commit()
    
    def get_user_scripts(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all scripts for a user"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scripts 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_script(self, script_id: str) -> Optional[Dict]:
        """Get script information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scripts WHERE script_id = ?", (script_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_active_scripts(self) -> List[Dict]:
        """Get all currently running scripts"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM scripts 
                WHERE status = 'running' 
                ORDER BY started_at DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def add_execution_log(self, script_id: str, log_content: str):
        """Add execution log entry"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO execution_logs (script_id, log_content)
                VALUES (?, ?)
            """, (script_id, log_content))
            conn.commit()
    
    def get_script_logs(self, script_id: str, limit: int = 100) -> List[Dict]:
        """Get script execution logs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM execution_logs 
                WHERE script_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (script_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def record_resource_usage(self, script_id: str, cpu_percent: float, memory_mb: float):
        """Record resource usage for a script"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO resource_usage (script_id, cpu_percent, memory_mb)
                VALUES (?, ?, ?)
            """, (script_id, cpu_percent, memory_mb))
            conn.commit()
    
    def get_resource_usage_stats(self, script_id: str) -> Dict:
        """Get resource usage statistics for a script"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    AVG(cpu_percent) as avg_cpu,
                    MAX(cpu_percent) as max_cpu,
                    AVG(memory_mb) as avg_memory,
                    MAX(memory_mb) as max_memory,
                    COUNT(*) as sample_count
                FROM resource_usage 
                WHERE script_id = ?
            """, (script_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'avg_cpu': round(result[0] or 0, 2),
                    'max_cpu': round(result[1] or 0, 2),
                    'avg_memory': round(result[2] or 0, 2),
                    'max_memory': round(result[3] or 0, 2),
                    'sample_count': result[4]
                }
            return {}
    
    def cleanup_old_data(self, days: int = 7):
        """Clean up old data from the database"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clean old completed scripts
            cursor.execute("""
                DELETE FROM scripts 
                WHERE status IN ('completed', 'stopped', 'killed', 'error') 
                AND completed_at < ?
            """, (cutoff_date,))
            
            # Clean old execution logs
            cursor.execute("""
                DELETE FROM execution_logs 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            # Clean old resource usage data
            cursor.execute("""
                DELETE FROM resource_usage 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            # Clean old system stats
            cursor.execute("""
                DELETE FROM system_stats 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            conn.commit()
            
            # Get cleanup stats
            cursor.execute("SELECT changes()")
            changes = cursor.fetchone()[0]
            return changes
    
    def get_user_statistics(self, user_id: int) -> Dict:
        """Get statistics for a specific user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total scripts
            cursor.execute("SELECT COUNT(*) FROM scripts WHERE user_id = ?", (user_id,))
            total_scripts = cursor.fetchone()[0]
            
            # Running scripts
            cursor.execute("""
                SELECT COUNT(*) FROM scripts 
                WHERE user_id = ? AND status = 'running'
            """, (user_id,))
            running_scripts = cursor.fetchone()[0]
            
            # Language usage
            cursor.execute("""
                SELECT language, COUNT(*) 
                FROM scripts 
                WHERE user_id = ? 
                GROUP BY language
            """, (user_id,))
            language_usage = dict(cursor.fetchall())
            
            # Status distribution
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM scripts 
                WHERE user_id = ? 
                GROUP BY status
            """, (user_id,))
            status_distribution = dict(cursor.fetchall())
            
            return {
                'total_scripts': total_scripts,
                'running_scripts': running_scripts,
                'language_usage': language_usage,
                'status_distribution': status_distribution
            }
    
    def get_global_statistics(self) -> Dict:
        """Get global bot statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # Active users (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE last_seen > datetime('now', '-1 day')
            """)
            active_users = cursor.fetchone()[0]
            
            # Total scripts
            cursor.execute("SELECT COUNT(*) FROM scripts")
            total_scripts = cursor.fetchone()[0]
            
            # Currently running scripts
            cursor.execute("SELECT COUNT(*) FROM scripts WHERE status = 'running'")
            running_scripts = cursor.fetchone()[0]
            
            # Most popular languages
            cursor.execute("""
                SELECT language, COUNT(*) as count
                FROM scripts 
                GROUP BY language 
                ORDER BY count DESC 
                LIMIT 5
            """)
            popular_languages = dict(cursor.fetchall())
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_scripts': total_scripts,
                'running_scripts': running_scripts,
                'popular_languages': popular_languages
          }
