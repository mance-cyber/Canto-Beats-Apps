"""
Canto-beats Launcher
A minimal executable that launches the main application.
Compiled to a small .exe using PyInstaller.
"""

import os
import sys
import subprocess
from pathlib import Path


def get_app_dir():
    """Get the application directory."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent


def main():
    """Launch the main application."""
    app_dir = get_app_dir()
    
    # Python executable path (embedded Python)
    python_dir = app_dir / "python"
    pythonw = python_dir / "pythonw.exe"
    python_exe = python_dir / "python.exe"
    
    # Choose pythonw (no console) or python
    if pythonw.exists():
        python_path = pythonw
    elif python_exe.exists():
        python_path = python_exe
    else:
        # Error: Python not found
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, 
            "找不到 Python 環境！\n請重新安裝 Canto-beats。", 
            "錯誤", 
            0x10
        )
        return 1
    
    # Main script path
    main_script = app_dir / "app" / "main.py"
    
    if not main_script.exists():
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, 
            f"找不到主程式！\n路徑: {main_script}", 
            "錯誤", 
            0x10
        )
        return 1
    
    # Set environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(app_dir / "app")
    
    # Launch the application
    try:
        # Use CREATE_NO_WINDOW flag to hide console
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        
        subprocess.Popen(
            [str(python_path), str(main_script)],
            cwd=str(app_dir / "app"),
            env=env,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return 0
    except Exception as e:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, 
            f"啟動失敗！\n錯誤: {e}", 
            "錯誤", 
            0x10
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
