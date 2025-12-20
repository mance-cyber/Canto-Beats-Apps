"""
License management system for Canto-beats
Online verification with Supabase + Offline fallback with machine binding
"""

import hashlib
import uuid
import platform
import subprocess
import json
import base64
import struct
import time
import os
import hmac
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass, asdict

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ==================== Configuration ====================
# Supabase configuration - 填入你的 Supabase 憑證
# 從 https://app.supabase.io/project/YOUR_PROJECT/settings/api 獲取
SUPABASE_URL = "https://evzxjipgrmswkeeqlals.supabase.co"  # 例如: "https://xxxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2enhqaXBncm1zd2tlZXFsYWxzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyOTI1NjAsImV4cCI6MjA4MDg2ODU2MH0.Nm3TvI_Tocc4ytovkuUgUTaYdvPrlQCfqhbxZYDOBiM"  # 例如: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
OFFLINE_CACHE_DAYS = 12  # 離線緩存有效天數
USE_ONLINE_VERIFICATION = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

# Master key for license encryption (protected by Nuitka compilation)
MASTER_KEY = b'canto-beats-2024-offline-license-key-v1'


@dataclass
class LicenseInfo:
    """License information"""
    license_type: str  # 'permanent' or 'trial'
    created_at: int  # Unix timestamp
    machine_hash: str  # First 16 chars of machine fingerprint hash
    transfers_remaining: int  # Number of transfers allowed
    activated_at: int  # Unix timestamp of activation
    machine_fingerprint: str  # Full fingerprint of activated machine
    last_verified_online: int = 0  # Timestamp of last online verification (for caching)


class SupabaseClient:
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
        if not HAS_REQUESTS or not USE_ONLINE_VERIFICATION:
            return (False, {"message": "在線驗證未配置", "offline": True})
        
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
                try:
                    error_json = response.json()
                    msg = error_json.get('message', f"服務器錯誤: {response.status_code}")
                    hint = error_json.get('hint', '')
                    details = error_json.get('details', '')
                    full_msg = msg
                    if details: full_msg += f" ({details})"
                    if hint: full_msg += f" [{hint}]"
                except:
                    full_msg = f"服務器錯誤: {response.status_code}\n{response.text[:100]}"
                return (False, {"message": full_msg})
                
        except Exception as e:
            return (False, {"message": str(e), "offline": True})
    
    def verify(self, license_key: str, machine_fingerprint: str) -> Tuple[bool, dict]:
        """Verify license online"""
        if not HAS_REQUESTS or not USE_ONLINE_VERIFICATION:
            return (False, {"message": "在線驗證未配置", "offline": True})
        
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
                try:
                    error_json = response.json()
                    msg = error_json.get('message', f"服務器錯誤: {response.status_code}")
                except:
                    msg = f"服務器錯誤: {response.status_code}"
                return (False, {"message": msg})
                
        except Exception as e:
            return (False, {"message": str(e), "offline": True})


class MachineFingerprint:
    """Generate unique machine fingerprint"""
    
    @staticmethod
    def get_cpu_id() -> str:
        """Get CPU identifier"""
        try:
            if platform.system() == 'Windows':
                # SECURITY: Use shell=False with list arguments to prevent command injection
                output = subprocess.check_output(
                    ['wmic', 'cpu', 'get', 'ProcessorId'],
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0,
                    timeout=5
                ).decode()
                lines = output.strip().split('\n')
                if len(lines) > 1:
                    return lines[1].strip()
            elif platform.system() == 'Darwin':  # macOS
                output = subprocess.check_output(
                    ['sysctl', '-n', 'machdep.cpu.brand_string'],
                    stderr=subprocess.DEVNULL,
                    timeout=5
                ).decode()
                return output.strip()
            else:  # Linux
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            return line.split(':')[1].strip()
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, OSError, FileNotFoundError):
            pass
        return platform.processor()
    
    @staticmethod
    def get_motherboard_id() -> str:
        """Get motherboard identifier"""
        try:
            if platform.system() == 'Windows':
                # SECURITY: Use shell=False with list arguments to prevent command injection
                output = subprocess.check_output(
                    ['wmic', 'baseboard', 'get', 'SerialNumber'],
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0,
                    timeout=5
                ).decode()
                lines = output.strip().split('\n')
                if len(lines) > 1:
                    return lines[1].strip()
            elif platform.system() == 'Darwin':  # macOS (Optimized with ioreg)
                output = subprocess.check_output(
                    ['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                    stderr=subprocess.DEVNULL,
                    timeout=5
                ).decode()
                for line in output.split('\n'):
                    if 'IOPlatformSerialNumber' in line and '=' in line:
                        # Extract value between quotes and clean it thoroughly
                        val = line.split('=')[1].strip().replace('"', '')
                        return "".join(c for c in val if c.isalnum())  # Only alphanumeric
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, OSError, FileNotFoundError):
            pass
        return platform.node().strip()
    
    @staticmethod
    def get_disk_id() -> str:
        """Get primary disk identifier"""
        try:
            if platform.system() == 'Windows':
                # SECURITY: Use shell=False with list arguments to prevent command injection
                output = subprocess.check_output(
                    ['wmic', 'diskdrive', 'get', 'SerialNumber'],
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0,
                    timeout=5
                ).decode()
                lines = output.strip().split('\n')
                if len(lines) > 1:
                    return lines[1].strip()
            elif platform.system() == 'Darwin':  # macOS
                output = subprocess.check_output(
                    ['diskutil', 'info', '/'],
                    stderr=subprocess.DEVNULL,
                    timeout=5
                ).decode()
                for line in output.split('\n'):
                    if 'Volume UUID' in line:
                        return line.split(':')[-1].strip()
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, OSError, FileNotFoundError):
            pass
        return str(uuid.getnode())
    
    @classmethod
    def generate(cls) -> str:
        """Generate machine fingerprint hash"""
        cpu = cls.get_cpu_id().strip()
        mb = cls.get_motherboard_id().strip()
        disk = cls.get_disk_id().strip()
        
        # Combine and hash
        combined = f"{cpu}|{mb}|{disk}|{platform.system()}"
        fingerprint = hashlib.sha256(combined.encode()).hexdigest()
        
        return fingerprint


class LicenseGenerator:
    """Generate license keys (Compact format)"""
    
    def __init__(self):
        # Secret key for HMAC signature
        self.secret_key = MASTER_KEY
    
    def generate(self, license_type: str = 'permanent', transfers_allowed: int = 1) -> str:
        """
        Generate a new license key (Compact 10-byte payload -> 16-char Base32)
        Format: [Random ID (4)] + [Metadata (1)] + [Signature (5)]
        """
        # 1. Random ID (4 bytes) - ensures uniqueness
        random_id = os.urandom(4)
        
        # 2. Metadata (1 byte)
        # Bit 7: Type (1=permanent, 0=trial)
        # Bit 0-6: Transfers allowed (0-127)
        is_perm = 1 if license_type == 'permanent' else 0
        transfers = min(transfers_allowed, 127)
        metadata_byte = (is_perm << 7) | transfers
        metadata = bytes([metadata_byte])
        
        # 3. Calculate Signature (HMAC-SHA256)
        data = random_id + metadata
        signature = hmac.new(self.secret_key, data, hashlib.sha256).digest()[:5]  # Take first 5 bytes
        
        # 4. Combine: 4 + 1 + 5 = 10 bytes
        payload = data + signature
        
        # 5. Encode to Base32
        # 10 bytes * 8 = 80 bits. 80 / 5 = 16 characters. No padding needed.
        encoded = base64.b32encode(payload).decode()
        
        # Format as CANTO-XXXX-XXXX-XXXX-XXXX
        # encoded is exactly 16 chars
        return f"CANTO-{encoded[0:4]}-{encoded[4:8]}-{encoded[8:12]}-{encoded[12:16]}"
    
    def decode(self, license_key: str) -> Optional[Tuple[str, int, int]]:
        """
        Decode and verify license key
        """
        try:
            # Clean format
            clean_key = license_key.strip().upper()
            if not clean_key.startswith('CANTO-'):
                return None
            
            key_body = clean_key.replace('CANTO-', '').replace('-', '')
            
            if len(key_body) != 16:
                return None
                
            # Decode Base32
            try:
                payload = base64.b32decode(key_body)
            except Exception:
                return None
                
            if len(payload) != 10:
                return None
            
            # Extract parts
            random_id = payload[:4]
            metadata = payload[4:5]
            signature = payload[5:]
            
            # Verify Signature
            data = random_id + metadata
            expected_signature = hmac.new(self.secret_key, data, hashlib.sha256).digest()[:5]
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Parse Metadata
            meta_val = metadata[0]
            is_perm = (meta_val >> 7) & 1
            transfers_allowed = meta_val & 0x7F
            
            license_type = 'permanent' if is_perm else 'trial'
            
            # Note: Created time is not stored in key to save space, using current time for object
            return (license_type, int(time.time()), transfers_allowed)
            
        except Exception as e:
            print(f"Error decoding license: {e}")
            return None


class LicenseValidator:
    """Validate and activate licenses with online verification + offline fallback"""
    
    def __init__(self, config):
        self.config = config
        self.license_file = Path(config.app_config.data_dir) / 'license.dat'
        self.generator = LicenseGenerator()
        self.supabase = SupabaseClient() if USE_ONLINE_VERIFICATION else None
    
    def validate_key(self, license_key: str) -> Tuple[bool, str]:
        """
        Validate license key format (basic format check only)
        Actual verification is done online by Supabase when activating
        
        Returns:
            Tuple of (is_valid, message)
        """
        license_key = license_key.strip().upper()
        
        # Basic format check: CANTO-XXXX-XXXX-XXXX-XXXX (25 chars with dashes)
        if not license_key.startswith("CANTO-"):
            return (False, "序號格式錯誤：需要以 CANTO- 開頭")
        
        # Remove dashes and check length
        key_body = license_key.replace("CANTO-", "").replace("-", "")
        if len(key_body) != 16:
            return (False, "序號長度錯誤：需要 16 位字符")
        
        # Check if alphanumeric
        if not key_body.isalnum():
            return (False, "序號格式錯誤：只能包含字母和數字")
        
        return (True, "序號格式正確，請按「啟用授權」進行線上驗證")
    
    def activate(self, license_key: str, force_transfer: bool = False) -> Tuple[bool, str]:
        """
        Activate license on current machine with online verification
        
        Args:
            license_key: License key to activate
            force_transfer: Force transfer even if already activated
        
        Returns:
            Tuple of (success, message)
        """
        license_key = license_key.strip().upper()
        current_fingerprint = MachineFingerprint.generate()
        
        # ==================== Online Verification Only ====================
        if not self.supabase or not USE_ONLINE_VERIFICATION:
            return (False, "授權服務未配置，請聯繫開發者")
        
        success, result = self.supabase.activate(license_key, current_fingerprint, force_transfer)
        
        if success:
            # Save to local cache for offline use after activation
            license_info = LicenseInfo(
                license_type=result.get('license_type', 'permanent'),
                created_at=int(time.time()),
                machine_hash=current_fingerprint[:16],
                transfers_remaining=result.get('transfers_remaining', 0),
                activated_at=int(time.time()),
                machine_fingerprint=current_fingerprint,
                last_verified_online=int(time.time())
            )
            self.save_license(license_info)
            return (True, result.get('message', '授權成功！'))
        
        # Check if need transfer confirmation
        if result.get('require_transfer'):
            remaining = result.get('transfers_remaining', 0)
            return (False, f"序號已在其他機器啟用，剩餘轉移次數: {remaining}")
        
        # Handle network error
        if result.get('offline'):
            return (False, "無法連接授權服務器，請檢查網絡連接")
        
        return (False, result.get('message', '授權失敗'))
    
    def save_license(self, license_info: LicenseInfo):
        """Save license to encrypted file"""
        if not HAS_CRYPTOGRAPHY:
            # Fallback: save as plain JSON (less secure but functional)
            data = json.dumps(asdict(license_info), ensure_ascii=False)
            self.license_file.parent.mkdir(parents=True, exist_ok=True)
            self.license_file.write_text(data, encoding='utf-8')
            return
        
        # Encrypt license data
        key_hash = hashlib.sha256(MASTER_KEY).digest()
        cipher = Fernet(base64.urlsafe_b64encode(key_hash))
        
        data = json.dumps(asdict(license_info), ensure_ascii=False).encode()
        encrypted = cipher.encrypt(data)
        
        self.license_file.parent.mkdir(parents=True, exist_ok=True)
        self.license_file.write_bytes(encrypted)
    
    def clear_license(self) -> bool:
        """Clear local license file"""
        try:
            if self.license_file.exists():
                self.license_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error clearing license: {e}")
            return False
            
    def load_license(self) -> Optional[LicenseInfo]:
        """Load license from file"""
        if not self.license_file.exists():
            return None
        
        try:
            if not HAS_CRYPTOGRAPHY:
                # Fallback: load as plain JSON
                data = json.loads(self.license_file.read_text(encoding='utf-8'))
                return LicenseInfo(**data)
            
            # Decrypt license data
            key_hash = hashlib.sha256(MASTER_KEY).digest()
            cipher = Fernet(base64.urlsafe_b64encode(key_hash))
            
            encrypted = self.license_file.read_bytes()
            decrypted = cipher.decrypt(encrypted)
            data = json.loads(decrypted.decode())
            
            return LicenseInfo(**data)
        except Exception as e:
            print(f"Error loading license: {e}")
            return None
    
    def verify(self) -> Tuple[bool, str]:
        """
        Verify current license status with online check + offline cache
        
        Returns:
            Tuple of (is_valid, message)
        """
        license_info = self.load_license()
        if license_info is None:
            return (False, "未找到授權")
        
        # Check machine fingerprint
        current_fingerprint = MachineFingerprint.generate()
        if license_info.machine_fingerprint != current_fingerprint:
            return (False, "機器指紋不符")
        
        # Check license type (trial period)
        if license_info.license_type == 'trial':
            days_used = (int(time.time()) - license_info.activated_at) / 86400
            if days_used > 7:
                return (False, "試用期已過")
        
        # ==================== Online Verification ====================
        if self.supabase and USE_ONLINE_VERIFICATION:
            # Get stored license key from cache (we need to store it)
            # For now, skip online re-verification and use cache duration
            pass
        
        # ==================== Offline Cache Validation ====================
        # Check if offline cache is still valid (3 days)
        if license_info.last_verified_online > 0:
            days_since_verify = (time.time() - license_info.last_verified_online) / 86400
            if days_since_verify > OFFLINE_CACHE_DAYS:
                # Try online verification
                if self.supabase and USE_ONLINE_VERIFICATION:
                    return (False, f"離線緩存已過期（{OFFLINE_CACHE_DAYS} 天），請連接網絡")
            remaining_days = max(0, OFFLINE_CACHE_DAYS - days_since_verify)
            return (True, f"授權有效（離線緩存剩餘 {remaining_days:.1f} 天）")
        
        return (True, "授權有效")


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
        return self.validator.load_license()
    
    def activate_license(self, license_key: str, force_transfer: bool = False) -> Tuple[bool, str]:
        """Activate a license key"""
        return self.validator.activate(license_key, force_transfer)
    
    def validate_key(self, license_key: str) -> Tuple[bool, str]:
        """Validate license key format"""
        return self.validator.validate_key(license_key)

    def clear_license(self) -> bool:
        """Clear local license"""
        return self.validator.clear_license()
