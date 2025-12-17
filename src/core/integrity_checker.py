"""
Code Integrity Checker for Canto-beats
Runtime verification to detect tampering and debugging attempts.
"""

import hashlib
import sys
import os
import ctypes
from pathlib import Path
from typing import Dict, Optional, Tuple
from utils.logger import setup_logger

logger = setup_logger()


class IntegrityChecker:
    """Runtime integrity verification."""
    
    # Critical modules to verify (relative to src/)
    CRITICAL_MODULES = [
        "core/license_manager.py",
        "core/config.py",
    ]
    
    def __init__(self, src_dir: Path):
        self.src_dir = src_dir
        self._baseline_hashes: Dict[str, str] = {}
        self._load_baseline()
    
    def _load_baseline(self):
        """Load or generate baseline hashes."""
        baseline_file = self.src_dir.parent / ".integrity"
        
        if baseline_file.exists():
            try:
                with open(baseline_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            path, hash_val = line.strip().split('=', 1)
                            self._baseline_hashes[path] = hash_val
            except Exception:
                pass
        
        # Generate if empty
        if not self._baseline_hashes:
            self._generate_baseline()
    
    def _generate_baseline(self):
        """Generate baseline hashes for critical files."""
        for rel_path in self.CRITICAL_MODULES:
            full_path = self.src_dir / rel_path
            if full_path.exists():
                file_hash = self._hash_file(full_path)
                self._baseline_hashes[rel_path] = file_hash
        
        # Save baseline
        self._save_baseline()
    
    def _save_baseline(self):
        """Save baseline hashes."""
        baseline_file = self.src_dir.parent / ".integrity"
        try:
            with open(baseline_file, 'w') as f:
                for path, hash_val in self._baseline_hashes.items():
                    f.write(f"{path}={hash_val}\n")
        except Exception:
            pass
    
    def _hash_file(self, path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""
    
    def verify_integrity(self) -> Tuple[bool, str]:
        """
        Verify all critical files.
        Returns: (is_valid, message)
        """
        for rel_path, expected_hash in self._baseline_hashes.items():
            full_path = self.src_dir / rel_path
            
            if not full_path.exists():
                return False, f"Missing: {rel_path}"
            
            current_hash = self._hash_file(full_path)
            if current_hash != expected_hash:
                logger.warning(f"Integrity check failed: {rel_path}")
                return False, f"Modified: {rel_path}"
        
        return True, "OK"
    
    def detect_debugger(self) -> bool:
        """Detect if a debugger is attached (cross-platform)."""
        # Windows-specific debugger detection
        if sys.platform == 'win32':
            try:
                kernel32 = ctypes.windll.kernel32
                return kernel32.IsDebuggerPresent() != 0
            except Exception:
                pass
        
        # macOS/Linux: Check ptrace status
        elif sys.platform in ('darwin', 'linux'):
            try:
                # On macOS/Linux, being traced shows in /proc/self/status
                # or we can check if P_TRACED flag is set
                import subprocess
                result = subprocess.run(
                    ['ps', '-p', str(os.getpid()), '-o', 'stat='],
                    capture_output=True, text=True, timeout=2
                )
                # 'T' in stat indicates traced/stopped
                if 'T' in result.stdout:
                    return True
            except Exception:
                pass
        
        # Check for common debugging environment variables (cross-platform)
        debug_vars = ['PYDEVD_USE_FRAME_EVAL', 'PYCHARM_DEBUG', 'DEBUGGER_ATTACHED']
        for var in debug_vars:
            if os.environ.get(var):
                return True
        
        return False
    
    def run_checks(self) -> Tuple[bool, str]:
        """Run all security checks."""
        # Check debugger
        if self.detect_debugger():
            logger.warning("Debugger detected")
            return False, "Debug mode not allowed"
        
        # Check integrity
        return self.verify_integrity()


def check_integrity(src_dir: Path) -> bool:
    """
    Quick integrity check function.
    Returns True if all checks pass.
    """
    try:
        checker = IntegrityChecker(src_dir)
        is_valid, msg = checker.run_checks()
        
        if not is_valid:
            logger.error(f"Security check failed: {msg}")
        
        return is_valid
    except Exception as e:
        logger.error(f"Integrity check error: {e}")
        return True  # Allow on error to avoid breaking app
