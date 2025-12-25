
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from utils.logger import generate_encryption_key, get_machine_id

def test_encryption_key():
    print(f"OS: {sys.platform}")
    machine_id = get_machine_id()
    print(f"Detected Machine ID: {machine_id}")
    
    key = generate_encryption_key()
    print(f"Generated Key (base64): {key.decode()}")
    
    if len(key) > 0:
        print("✅ Key generation successful")
    else:
        print("❌ Key generation failed")

if __name__ == "__main__":
    test_encryption_key()
