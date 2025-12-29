"""
Canto-beats License Manager with Supabase Online Verification
Supports offline mode with 3-day cache
"""

import hashlib
import uuid
import platform
import subprocess
import json
import time
import os
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass, asdict
import requests

# Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "your-anon-key")
OFFLINE_CACHE_DAYS = 3


@dataclass
class LicenseInfo:
    """License information"""
    license_key: str
    license_type: str
    activated_at: int
    machine_fingerprint: str
    last_verified_online: int  # Timestamp of last online verification
    transfers_remaining: int = 1


class MachineFingerprint:
    """Generate unique machine fingerprint (cross-platform)"""
    
    @staticmethod
    def get_cpu_id() -> str:
        """Get CPU identifier"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'processorid'],
                    capture_output=True, text=True, timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    return lines[1].strip()
            elif platform.system() == "Darwin":
                # macOS: Use sysctl to get CPU brand string
                result = subprocess.run(
                    ['sysctl', '-n', 'machdep.cpu.brand_string'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
        except:
            pass
        return str(uuid.getnode())
    
    @staticmethod
    def get_motherboard_id() -> str:
        """Get motherboard/hardware identifier"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['wmic', 'baseboard', 'get', 'serialnumber'],
                    capture_output=True, text=True, timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    return lines[1].strip()
            elif platform.system() == "Darwin":
                # macOS: Use ioreg to get hardware UUID
                result = subprocess.run(
                    ['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'IOPlatformUUID' in line:
                            # Extract UUID from line like: "IOPlatformUUID" = "xxxxxxxx-xxxx-..."
                            parts = line.split('=')
                            if len(parts) > 1:
                                return parts[1].strip().strip('"')
        except:
            pass
        return "unknown-motherboard"
    
    @staticmethod
    def get_disk_id() -> str:
        """Get primary disk identifier"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['wmic', 'diskdrive', 'get', 'serialnumber'],
                    capture_output=True, text=True, timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    for line in lines[1:]:
                        line = line.strip()
                        if line and line != "SerialNumber":
                            return line
            elif platform.system() == "Darwin":
                # macOS: Use diskutil to get disk UUID
                result = subprocess.run(
                    ['diskutil', 'info', '-plist', '/'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    # Simple extraction - look for VolumeUUID
                    import re
                    match = re.search(r'<key>VolumeUUID</key>\s*<string>([^<]+)</string>', result.stdout)
                    if match:
                        return match.group(1)
        except:
            pass
        return "unknown-disk"
    
    @classmethod
    def generate(cls) -> str:
        """Generate machine fingerprint hash"""
        components = [
            cls.get_cpu_id(),
            cls.get_motherboard_id(),
            cls.get_disk_id(),
            platform.node()
        ]
        combined = "-".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]


class SupabaseLicenseClient:
    """Client for Supabase license verification"""
    
    def __init__(self):
        self.base_url = SUPABASE_URL
        self.headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
    
    def activate(self, license_key: str, machine_fingerprint: str, force_transfer: bool = False) -> Tuple[bool, dict]:
        """Activate license online"""
        try:
            response = requests.post(
                f"{self.base_url}/rest/v1/rpc/activate_license",
                headers=self.headers,
                json={
                    "p_license_key": license_key,
                    "p_machine_fingerprint": machine_fingerprint,
                    "p_force_transfer": force_transfer
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return (result.get('success', False), result)
            else:
                return (False, {"message": f"服務器錯誤: {response.status_code}"})
                
        except requests.exceptions.Timeout:
            return (False, {"message": "連接超時", "offline": True})
        except requests.exceptions.ConnectionError:
            return (False, {"message": "無法連接服務器", "offline": True})
        except Exception as e:
            return (False, {"message": str(e)})
    
    def verify(self, license_key: str, machine_fingerprint: str) -> Tuple[bool, dict]:
        """Verify license online"""
        try:
            response = requests.post(
                f"{self.base_url}/rest/v1/rpc/verify_license",
                headers=self.headers,
                json={
                    "p_license_key": license_key,
                    "p_machine_fingerprint": machine_fingerprint
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return (result.get('success', False), result)
            else:
                return (False, {"message": f"服務器錯誤: {response.status_code}"})
                
        except requests.exceptions.Timeout:
            return (False, {"message": "連接超時", "offline": True})
        except requests.exceptions.ConnectionError:
            return (False, {"message": "無法連接服務器", "offline": True})
        except Exception as e:
            return (False, {"message": str(e)})


class LicenseValidator:
    """Validate and activate licenses with online verification"""
    
    def __init__(self, config):
        self.config = config
        self.license_file = Path(config.app_config.data_dir) / 'license.dat'
        self.supabase_client = SupabaseLicenseClient()
        
        # Encryption key for local cache
        from cryptography.fernet import Fernet
        key = hashlib.sha256(b'canto-beats-license-cache-2024').digest()
        self.fernet = Fernet(key[:32].hex().encode() + b'=' * 12)
    
    def activate(self, license_key: str, force_transfer: bool = False) -> Tuple[bool, str]:
        """
        Activate license with online verification
        
        Args:
            license_key: License key to activate
            force_transfer: Force transfer from another machine
        
        Returns:
            Tuple of (success, message)
        """
        license_key = license_key.strip().upper().replace("-", "")
        machine_fingerprint = MachineFingerprint.generate()
        
        # Try online verification
        success, result = self.supabase_client.activate(
            license_key, machine_fingerprint, force_transfer
        )
        
        if success:
            # Save to local cache
            license_info = LicenseInfo(
                license_key=license_key,
                license_type=result.get('license_type', 'permanent'),
                activated_at=int(time.time()),
                machine_fingerprint=machine_fingerprint,
                last_verified_online=int(time.time()),
                transfers_remaining=result.get('transfers_remaining', 0)
            )
            self._save_cache(license_info)
            return (True, result.get('message', '授權成功！'))
        
        # Check if need transfer confirmation
        if result.get('require_transfer'):
            return (False, f"序號已在其他機器啟用。剩餘轉移次數: {result.get('transfers_remaining', 0)}")
        
        # Handle offline mode
        if result.get('offline'):
            cached = self._load_cache()
            if cached and self._is_cache_valid(cached):
                return (True, "離線模式：使用本地緩存")
            return (False, "無法連接服務器，請檢查網絡連接")
        
        return (False, result.get('message', '授權失敗'))
    
    def verify(self) -> Tuple[bool, str]:
        """
        Verify current license status

        Returns:
            Tuple of (is_valid, message)
        """
        cached = self._load_cache()
        if cached is None:
            print("[LICENSE] No cached license found")
            return (False, "未找到授權")

        print(f"[LICENSE] Found cached license: {cached.license_key[:8]}...")

        # Check machine fingerprint
        current_fingerprint = MachineFingerprint.generate()
        print(f"[LICENSE] Current fingerprint: {current_fingerprint[:16]}...")
        print(f"[LICENSE] Cached fingerprint: {cached.machine_fingerprint[:16]}...")

        if cached.machine_fingerprint != current_fingerprint:
            print("[LICENSE] Machine fingerprint mismatch!")
            return (False, "機器指紋不符")

        print("[LICENSE] Fingerprint match, verifying online...")

        # Try online verification
        success, result = self.supabase_client.verify(
            cached.license_key, current_fingerprint
        )

        print(f"[LICENSE] Online verification result: success={success}, result={result}")

        if success:
            # Update cache with new verification time
            cached.last_verified_online = int(time.time())
            self._save_cache(cached)
            print("[LICENSE] ✅ License valid (online)")
            return (True, "授權有效（在線驗證）")

        # Handle offline mode
        if result.get('offline'):
            if self._is_cache_valid(cached):
                days_remaining = OFFLINE_CACHE_DAYS - self._days_since_verification(cached)
                print(f"[LICENSE] ✅ License valid (offline, {days_remaining:.1f} days remaining)")
                return (True, f"離線模式：授權有效（剩餘 {days_remaining:.1f} 天）")
            print("[LICENSE] ❌ Offline cache expired")
            return (False, "離線緩存已過期，請連接網絡")

        print(f"[LICENSE] ❌ Verification failed: {result.get('message')}")
        return (False, result.get('message', '授權無效'))
    
    def _save_cache(self, license_info: LicenseInfo):
        """Save license to encrypted local cache"""
        try:
            data = json.dumps(asdict(license_info)).encode()
            encrypted = self.fernet.encrypt(data)
            self.license_file.parent.mkdir(parents=True, exist_ok=True)
            self.license_file.write_bytes(encrypted)
        except Exception as e:
            print(f"Failed to save license cache: {e}")
    
    def _load_cache(self) -> Optional[LicenseInfo]:
        """Load license from local cache"""
        try:
            if not self.license_file.exists():
                return None
            encrypted = self.license_file.read_bytes()
            data = self.fernet.decrypt(encrypted)
            info_dict = json.loads(data.decode())
            return LicenseInfo(**info_dict)
        except Exception as e:
            print(f"Failed to load license cache: {e}")
            return None
    
    def _is_cache_valid(self, cached: LicenseInfo) -> bool:
        """Check if cached license is still valid"""
        return self._days_since_verification(cached) <= OFFLINE_CACHE_DAYS
    
    def _days_since_verification(self, cached: LicenseInfo) -> float:
        """Get days since last online verification"""
        return (time.time() - cached.last_verified_online) / 86400


class LicenseManager:
    """Main license management interface"""
    
    def __init__(self, config):
        self.config = config
        self.validator = LicenseValidator(config)
    
    def is_licensed(self) -> bool:
        """Check if application is licensed"""
        is_valid, _ = self.validator.verify()
        return is_valid
    
    def get_license_info(self) -> Optional[LicenseInfo]:
        """Get current license information"""
        return self.validator._load_cache()
    
    def activate_license(self, license_key: str, force_transfer: bool = False) -> Tuple[bool, str]:
        """Activate a license key"""
        return self.validator.activate(license_key, force_transfer)
    
    def verify_license(self) -> Tuple[bool, str]:
        """Verify current license"""
        return self.validator.verify()
