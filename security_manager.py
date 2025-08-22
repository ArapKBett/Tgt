import re
import ast
import subprocess
from typing import List, Tuple, Optional
from config_manager import Config

class SecurityManager:
    """Handle security checks for user scripts"""
    
    def __init__(self, config: Config):
        self.config = config
        self.blocked_commands = config.get("security", {}).get("blocked_commands", [])
        self.blocked_imports = config.get("security", {}).get("blocked_imports", [])
    
    def scan_script_content(self, content: str, language: str) -> Tuple[bool, List[str]]:
        """Scan script content for security violations"""
        violations = []
        
        # Check script size
        max_size = self.config.get("max_script_size", 100000)
        if len(content) > max_size:
            violations.append(f"Script too large ({len(content)} > {max_size} bytes)")
        
        # Language-specific security checks
        if language == "python":
            violations.extend(self._check_python_security(content))
        elif language in ["c", "cpp"]:
            violations.extend(self._check_c_cpp_security(content))
        elif language == "java":
            violations.extend(self._check_java_security(content))
        elif language == "sh":
            violations.extend(self._check_shell_security(content))
        
        # General command checks
        violations.extend(self._check_blocked_commands(content))
        
        is_safe = len(violations) == 0
        return is_safe, violations
    
    def _check_python_security(self, content: str) -> List[str]:
        """Check Python-specific security issues"""
        violations = []
        
        try:
            # Parse AST to check for dangerous imports and calls
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Check imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.blocked_imports:
                            violations.append(f"Blocked import: {alias.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.blocked_imports:
                        violations.append(f"Blocked import: {node.module}")
                
                # Check function calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ["eval", "exec", "__import__"]:
                            violations.append(f"Blocked function call: {node.func.id}")
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in ["system", "popen", "spawn"]:
                            violations.append(f"Blocked method call: {node.func.attr}")
        
        except SyntaxError:
            violations.append("Python syntax error")
        
        return violations
    
    def _check_c_cpp_security(self, content: str) -> List[str]:
        """Check C/C++ specific security issues"""
        violations = []
        
        # Check for dangerous functions
        dangerous_functions = [
            "system", "exec", "popen", "fork",
            "gets", "strcpy", "strcat", "sprintf"
        ]
        
        for func in dangerous_functions:
            if re.search(rf'\b{func}\s*\(', content):
                violations.append(f"Potentially dangerous function: {func}")
        
        # Check for file operations
        file_operations = ["fopen", "remove", "unlink", "rmdir"]
        for op in file_operations:
            if re.search(rf'\b{op}\s*\(', content):
                violations.append(f"File operation detected: {op}")
        
        return violations
    
    def _check_java_security(self, content: str) -> List[str]:
        """Check Java-specific security issues"""
        violations = []
        
        # Check for dangerous classes/methods
        dangerous_patterns = [
            r'Runtime\.getRuntime\(\)\.exec',
            r'ProcessBuilder',
            r'System\.exit',
            r'File\.delete',
            r'Files\.delete'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content):
                violations.append(f"Potentially dangerous Java operation: {pattern}")
        
        return violations
    
    def _check_shell_security(self, content: str) -> List[str]:
        """Check shell script security issues"""
        violations = []
        
        # Check for dangerous commands
        dangerous_commands = [
            "rm", "rmdir", "del", "format", "fdisk",
            "wget", "curl", "nc", "netcat", "ssh",
            "sudo", "su", "chmod", "chown", "mount",
            "umount", "mkfs", "dd"
        ]
        
        for cmd in dangerous_commands:
            if re.search(rf'\b{cmd}\b', content):
                violations.append(f"Blocked shell command: {cmd}")
        
        # Check for network operations
        network_patterns = [
            r'>\s*/dev/tcp/',
            r'>\s*/dev/udp/',
            r'\b\d+\.\d+\.\d+\.\d+\b'  # IP addresses
        ]
        
        for pattern in network_patterns:
            if re.search(pattern, content):
                violations.append("Network operation detected")
                break
        
        return violations
    
    def _check_blocked_commands(self, content: str) -> List[str]:
        """Check for blocked commands across all languages"""
        violations = []
        
        for cmd in self.blocked_commands:
            if re.search(rf'\b{cmd}\b', content, re.IGNORECASE):
                violations.append(f"Blocked command detected: {cmd}")
        
        return violations
    
    def sanitize_command(self, command: str) -> Tuple[bool, str]:
        """Sanitize execution command"""
        # Remove potentially dangerous characters
        dangerous_chars = [';', '&', '|', '`', '$', '>', '<', '*', '?']
        
        for char in dangerous_chars:
            if char in command:
                return False, f"Dangerous character '{char}' in command"
        
        # Check for blocked commands in execution command
        for blocked in self.blocked_commands:
            if blocked in command.lower():
                return False, f"Blocked command '{blocked}' in execution command"
        
        return True, "Command is safe"
    
    def create_sandbox_command(self, original_command: str, script_path: str) -> str:
        """Create sandboxed execution command using firejail or similar"""
        if not self.config.get("security", {}).get("enable_sandbox", False):
            return original_command
        
        # Check if firejail is available
        try:
            subprocess.run(["which", "firejail"], check=True, capture_output=True)
            
            # Create firejail command with restrictions
            memory_limit = self.config.get("execution_limits", {}).get("memory_mb", 512)
            
            sandbox_cmd = f"firejail --quiet --noprofile --private-tmp " \
                         f"--nonetwork --memory={memory_limit}m " \
                         f"--timeout=3600 {original_command}"
            
            return sandbox_cmd
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Firejail not available, use timeout at least
            return f"timeout 3600 {original_command}"
