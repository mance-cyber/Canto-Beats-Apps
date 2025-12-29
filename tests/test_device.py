"""
測試自動設備檢測
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import Config
from models.model_manager import ModelManager

class TestManager(ModelManager):
    def load_model(self):
        pass
    
    def unload_model(self):
        pass

# Test
config = Config()
mgr = TestManager(config)

print("=" * 50)
print("自動設備檢測測試")
print("=" * 50)
print(f"配置中的設備: {config.get('device')}")
print(f"實際選擇的設備: {mgr.device}")
print()
print("設備詳細信息:")
for key, value in mgr.get_device_info().items():
    print(f"  {key}: {value}")
print("=" * 50)
