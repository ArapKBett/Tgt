import psutil
import asyncio
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from config_manager import Config

class ResourceMonitor:
    """Monitor system resources and script usage"""
    
    def __init__(self, config: Config):
        self.config = config
        self.process_stats: Dict[str, Dict] = {}
        self.system_stats = {
            'start_time': datetime.now(),
            'total_scripts_run': 0,
            'active_scripts': 0
        }
    
    def start_monitoring_process(self, script_id: str, process):
        """Start monitoring a process"""
        try:
            ps_process = psutil.Process(process.pid)
            self.process_stats[script_id] = {
                'process': ps_process,
                'start_time': datetime.now(),
                'peak_memory': 0,
                'peak_cpu': 0,
                'total_cpu_time': 0,
                'status': 'running'
            }
            self.system_stats['total_scripts_run'] += 1
            self.system_stats['active_scripts'] += 1
        except psutil.NoSuchProcess:
            pass
    
    def stop_monitoring_process(self, script_id: str):
        """Stop monitoring a process"""
        if script_id in self.process_stats:
            self.process_stats[script_id]['status'] = 'stopped'
            self.system_stats['active_scripts'] = max(0, self.system_stats['active_scripts'] - 1)
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        while True:
            await asyncio.sleep(5)  # Monitor every 5 seconds
            
            to_remove = []
            memory_limit = self.config.get("execution_limits", {}).get("memory_mb", 512) * 1024 * 1024  # Convert to bytes
            cpu_limit = self.config.get("execution_limits", {}).get("cpu_percent", 50)
            
            for script_id, stats in self.process_stats.items():
                if stats['status'] != 'running':
                    continue
                
                try:
                    process = stats['process']
                    
                    # Check if process is still alive
                    if not process.is_running():
                        stats['status'] = 'completed'
                        self.system_stats['active_scripts'] -= 1
                        continue
                    
                    # Get memory usage
                    memory_info = process.memory_info()
                    current_memory = memory_info.rss
                    stats['peak_memory'] = max(stats['peak_memory'], current_memory)
                    
                    # Get CPU usage
                    try:
                        current_cpu = process.cpu_percent()
                        stats['peak_cpu'] = max(stats['peak_cpu'], current_cpu)
                        stats['total_cpu_time'] = process.cpu_times().user + process.cpu_times().system
                    except psutil.ZombieProcess:
                        continue
                    
                    # Check limits and kill if exceeded
                    if current_memory > memory_limit:
                        print(f"Script {script_id} exceeded memory limit ({current_memory} > {memory_limit})")
                        process.terminate()
                        stats['status'] = 'killed_memory'
                        self.system_stats['active_scripts'] -= 1
                        
                    elif current_cpu > cpu_limit and stats['total_cpu_time'] > 60:  # Only after 1 minute
                        print(f"Script {script_id} exceeded CPU limit ({current_cpu}% > {cpu_limit}%)")
                        process.terminate()
                        stats['status'] = 'killed_cpu'
                        self.system_stats['active_scripts'] -= 1
                
                except psutil.NoSuchProcess:
                    stats['status'] = 'completed'
                    self.system_stats['active_scripts'] -= 1
                except Exception as e:
                    print(f"Error monitoring script {script_id}: {e}")
            
            # Clean up old completed processes
            current_time = datetime.now()
            for script_id in to_remove:
                if script_id in self.process_stats:
                    del self.process_stats[script_id]
    
    def get_process_stats(self, script_id: str) -> Optional[Dict]:
        """Get statistics for a specific process"""
        if script_id not in self.process_stats:
            return None
        
        stats = self.process_stats[script_id].copy()
        
        # Convert bytes to MB for display
        stats['peak_memory_mb'] = stats['peak_memory'] / (1024 * 1024)
        
        # Calculate runtime
        if stats['status'] == 'running':
            stats['runtime'] = datetime.now() - stats['start_time']
        
        return stats
    
    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        current_system = psutil.virtual_memory()
        current_cpu = psutil.cpu_percent(interval=1)
        
        uptime = datetime.now() - self.system_stats['start_time']
        
        return {
            'bot_uptime': str(uptime).split('.')[0],  # Remove microseconds
            'total_scripts_run': self.system_stats['total_scripts_run'],
            'active_scripts': self.system_stats['active_scripts'],
            'system_memory_used': f"{current_system.percent:.1f}%",
            'system_memory_available': f"{current_system.available / (1024**3):.1f} GB",
            'system_cpu_usage': f"{current_cpu:.1f}%",
            'disk_usage': f"{psutil.disk_usage('/').percent:.1f}%"
        }
    
    def cleanup_old_stats(self, days: int = 1):
        """Clean up statistics older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for script_id, stats in self.process_stats.items():
            if stats['start_time'] < cutoff_time and stats['status'] != 'running':
                to_remove.append(script_id)
        
        for script_id in to_remove:
            del self.process_stats[script_id]
        
        print(f"Cleaned up {len(to_remove)} old process statistics")
    
    def force_kill_script(self, script_id: str) -> bool:
        """Force kill a script process"""
        if script_id not in self.process_stats:
            return False
        
        try:
            process = self.process_stats[script_id]['process']
            if process.is_running():
                # Try graceful termination first
                process.terminate()
                
                # Wait 5 seconds for graceful shutdown
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    # Force kill if still running
                    process.kill()
                
                self.process_stats[script_id]['status'] = 'killed'
                self.system_stats['active_scripts'] -= 1
                return True
                
        except psutil.NoSuchProcess:
            self.process_stats[script_id]['status'] = 'completed'
            
        return False
