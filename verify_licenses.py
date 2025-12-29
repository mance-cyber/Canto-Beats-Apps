"""
驗證授權序號是否有效
"""

import sys
import os
import hashlib
import hmac
import base64

# Master key from license_manager.py
MASTER_KEY = b'canto-beats-2024-offline-license-key-v1'

def verify_license(license_key):
    """驗證授權序號是否有效"""
    try:
        # Clean format
        clean_key = license_key.strip().upper()
        if not clean_key.startswith('CANTO-'):
            return False, "格式錯誤：不是以 CANTO- 開頭"
        
        key_body = clean_key.replace('CANTO-', '').replace('-', '')
        
        if len(key_body) != 16:
            return False, f"格式錯誤：長度應為16，實際為{len(key_body)}"
            
        # Decode Base32
        try:
            payload = base64.b32decode(key_body)
        except Exception as e:
            return False, f"解碼錯誤：{e}"
            
        if len(payload) != 10:
            return False, f"負載長度錯誤：應為10，實際為{len(payload)}"
        
        # Extract parts
        random_id = payload[:4]
        metadata = payload[4:5]
        signature = payload[5:]
        
        # Verify Signature
        data = random_id + metadata
        expected_signature = hmac.new(MASTER_KEY, data, hashlib.sha256).digest()[:5]
        
        if not hmac.compare_digest(signature, expected_signature):
            return False, "簽名驗證失敗"
        
        # Parse Metadata
        meta_val = metadata[0]
        is_perm = (meta_val >> 7) & 1
        transfers_allowed = meta_val & 0x7F
        
        license_type = '永久授權' if is_perm else '試用授權'
        
        return True, f"✓ 有效 ({license_type}, {transfers_allowed}次轉移)"
        
    except Exception as e:
        return False, f"驗證錯誤：{e}"

# 測試前10個序號
test_keys = [
    "CANTO-ZXKW-4XEB-EVMQ-SJBE",
    "CANTO-NJPB-JLMB-2BTC-WXWD",
    "CANTO-IU7D-POEB-UFOA-4UHQ",
    "CANTO-L43C-SF4B-A43S-32O3",
    "CANTO-Z75O-STMB-JAOP-YDNU",
    "CANTO-GV3B-GDMB-4F7B-K7HF",
    "CANTO-EFHL-ITEB-BLFY-6A4V",
    "CANTO-OQQV-2OMB-RGCW-3ZLZ",
    "CANTO-YKKH-QA4B-T3KK-GHHT",
    "CANTO-FHQD-PYMB-6OHT-LP7A",
]

print("=" * 70)
print("驗證授權序號")
print("=" * 70)
print()

valid_count = 0
invalid_count = 0

for i, key in enumerate(test_keys, 1):
    is_valid, message = verify_license(key)
    status = "✓ 有效" if is_valid else "✗ 無效"
    print(f"{i:2d}. {key} - {message}")
    if is_valid:
        valid_count += 1
    else:
        invalid_count += 1

print()
print("=" * 70)
print(f"測試結果: {valid_count}/{len(test_keys)} 個序號有效")
print("=" * 70)

# 驗證整個文件
print("\n正在驗證所有序號...")
try:
    with open('license_keys.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    all_valid = 0
    all_invalid = 0
    
    for line in lines:
        if 'CANTO-' in line:
            # Extract key from line
            parts = line.strip().split('CANTO-')
            if len(parts) > 1:
                key = 'CANTO-' + parts[1].strip()
                is_valid, _ = verify_license(key)
                if is_valid:
                    all_valid += 1
                else:
                    all_invalid += 1
    
    print(f"\n文件驗證結果: {all_valid}/{all_valid + all_invalid} 個序號有效")
    if all_invalid == 0:
        print("🎉 所有序號都是有效的！")
    
except FileNotFoundError:
    print("找不到 license_keys.txt 文件")
