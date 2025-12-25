
import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from utils.logger import setup_logger, decrypt_log_file

def test_master_key():
    test_log_dir = Path("test_logs")
    test_log_dir.mkdir(exist_ok=True)
    
    # 1. Create a logger (uses Master Key now)
    logger = setup_logger("test-master", log_dir=test_log_dir, encrypt=True)
    logger.info("This is a test message for Master Key encryption")
    
    # Find the log file
    log_file = list(test_log_dir.glob("*.log.enc"))[0]
    print(f"Log file created: {log_file}")
    
    # 2. Try to decrypt
    print("Attempting to decrypt...")
    content = decrypt_log_file(str(log_file))
    print(f"Decrypted content:\n{content}")
    
    if "This is a test message" in content:
        print("✅ Master Key decryption successful!")
    else:
        print("❌ Decryption failed or content mismatch")
    
    # Cleanup
    import shutil
    # shutil.rmtree(test_log_dir) # Keep for inspection? Nah.

if __name__ == "__main__":
    test_master_key()
