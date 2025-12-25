"""
Logging utilities for Canto-beats with optional encryption
"""

import logging
import sys
import os
import hashlib
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional


def get_machine_id() -> str:
    """Get a unique machine identifier for key generation."""
    try:
        if sys.platform == 'win32':
            import subprocess
            result = subprocess.run(
                ['wmic', 'csproduct', 'get', 'uuid'],
                capture_output=True, text=True, timeout=5
            )
            uuid = result.stdout.strip().split('\n')[-1].strip()
            if uuid and uuid != 'UUID':
                return uuid
        elif sys.platform == 'darwin':
            # Get IOPlatformUUID on macOS
            import subprocess
            result = subprocess.run(
                ['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                capture_output=True, text=True, timeout=5
            )
            # Find IOPlatformUUID in output
            import re
            match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', result.stdout)
            if match:
                return match.group(1)
    except Exception:
        pass
    
    # Fallback: use username + hostname
    import socket
    try:
        user = os.getlogin()
    except Exception:
        user = os.environ.get('USER', 'unknown')
    return f"{user}@{socket.gethostname()}"


def generate_encryption_key() -> bytes:
    """Generate a Fernet key from machine-specific data."""
    machine_id = get_machine_id()
    salt = "Canto-beats-log-encryption-2024"
    
    # Create a 32-byte key using SHA256
    key_material = f"{machine_id}{salt}".encode()
    key_hash = hashlib.sha256(key_material).digest()
    
    # Fernet requires URL-safe base64 encoded 32-byte key
    return base64.urlsafe_b64encode(key_hash)


class EncryptedFileHandler(logging.Handler):
    """
    A logging handler that encrypts log entries using Fernet (AES).
    Each line is encrypted separately for streaming writes.
    """
    
    def __init__(self, filename: str, key: Optional[bytes] = None):
        super().__init__()
        self.filename = filename
        
        try:
            from cryptography.fernet import Fernet
            
            # Use Master Key by default for cross-machine support
            master_material = b"Canto-Beats-Master-Safety-Key-2025"
            self.key = key or base64.urlsafe_b64encode(hashlib.sha256(master_material).digest())
            
            self.fernet = Fernet(self.key)
            self.encryption_enabled = True
        except ImportError:
            self.encryption_enabled = False
            logging.warning("cryptography not installed, logs will not be encrypted")
        
        # Open file in append binary mode
        self.file = open(filename, 'ab')
    
    def emit(self, record):
        try:
            msg = self.format(record)
            
            if self.encryption_enabled:
                # Encrypt the log message
                encrypted = self.fernet.encrypt(msg.encode('utf-8'))
                self.file.write(encrypted + b'\n')
            else:
                self.file.write(msg.encode('utf-8') + b'\n')
            
            self.file.flush()
        except Exception:
            self.handleError(record)
    
    def close(self):
        if hasattr(self, 'file') and self.file:
            self.file.close()
        super().close()


def decrypt_log_file(encrypted_file: str, output_file: str = None) -> str:
    """
    Decrypt an encrypted log file. Try local machine key first, then master key.
    
    Args:
        encrypted_file: Path to encrypted log file
        output_file: Optional path to write decrypted content
        
    Returns:
        Decrypted log content as string
    """
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise RuntimeError("cryptography package required for decryption")
    
    # 1. Try Local Machine Key
    local_key = generate_encryption_key()
    local_fernet = Fernet(local_key)
    
    # 2. Master Key (for admin/support decryption of user logs)
    # Generated from a hardcoded master salt
    master_material = b"Canto-Beats-Master-Safety-Key-2025"
    master_key = base64.urlsafe_b64encode(hashlib.sha256(master_material).digest())
    master_fernet = Fernet(master_key)
    
    decrypted_lines = []
    with open(encrypted_file, 'rb') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            try:
                # First attempt: Local key
                decrypted = local_fernet.decrypt(line).decode('utf-8')
                decrypted_lines.append(decrypted)
            except Exception:
                try:
                    # Second attempt: Master key
                    decrypted = master_fernet.decrypt(line).decode('utf-8')
                    decrypted_lines.append(decrypted)
                except Exception as e:
                    decrypted_lines.append(f"[DECRYPT ERROR: {e}]")
    
    content = '\n'.join(decrypted_lines)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return content


def get_log_directory() -> Path:
    """
    Get the log directory in user's AppData folder.
    This ensures logs are always saved even in installed environments.
    """
    # Use AppData\Local\Canto-beats\logs on Windows
    if sys.platform == 'win32':
        app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        log_dir = Path(app_data) / 'Canto-beats' / 'logs'
    else:
        # For Mac/Linux, use ~/.canto-beats/logs
        log_dir = Path.home() / '.canto-beats' / 'logs'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logger(name: str = "canto-beats", log_dir: Path = None, encrypt: bool = False) -> logging.Logger:
    """
    Setup application logger
    
    Args:
        name: Logger name
        log_dir: Directory to save log files (optional, defaults to AppData)
        encrypt: Whether to encrypt log files (default: False)
    
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler - ALWAYS enabled now
    # Use provided log_dir or default to AppData
    if log_dir is None:
        log_dir = get_log_directory()
    else:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime('%Y%m%d')
    
    try:
        if encrypt:
            # Use encrypted file handler
            log_file = log_dir / f"canto-beats_{date_str}.log.enc"
            file_handler = EncryptedFileHandler(str(log_file))
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
            logger.info(f"Encrypted log file: {log_file}")
        else:
            # Use standard file handler (plain text)
            log_file = log_dir / f"canto-beats_{date_str}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
            logger.info(f"Log file: {log_file}")
    except Exception as e:
        logger.warning(f"Could not create log file: {e}")
    
    return logger


# CLI utility for decrypting logs
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Decrypt Canto-beats log files")
    parser.add_argument("input", help="Encrypted log file (.log.enc)")
    parser.add_argument("-o", "--output", help="Output file (optional)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        sys.exit(1)
    
    try:
        content = decrypt_log_file(args.input, args.output)
        if args.output:
            print(f"Decrypted to: {args.output}")
        else:
            print(content)
    except Exception as e:
        print(f"Decryption failed: {e}")
        sys.exit(1)
