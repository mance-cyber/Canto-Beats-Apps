
import sys
from PySide6.QtWidgets import QApplication
from src.ui.style_panel import StyleControlPanel

def test_style_panel_signal():
    app = QApplication(sys.argv)
    panel = StyleControlPanel()
    
    # Test if _emit_change accepts arguments
    try:
        panel._emit_change(None) # Simulate signal with argument
        print("SUCCESS: _emit_change accepts arguments")
    except TypeError:
        print("FAILURE: _emit_change raised TypeError with arguments")
        sys.exit(1)
    except Exception as e:
        print(f"FAILURE: Unexpected error: {e}")
        sys.exit(1)
        
    print("Style Panel Test Passed")

if __name__ == "__main__":
    test_style_panel_signal()
