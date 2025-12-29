"""
Canto-beats Standalone Launcher
極簡啟動器 - 用於創建 EXE 入口點
"""
import os
import sys
import subprocess

def main():
    # ==================== 核心：確定安裝目錄 ====================
    # PyInstaller 打包後，sys.executable 指向 EXE 本身
    # 我們需要找到 EXE 所在的目錄
    if getattr(sys, 'frozen', False):
        # 被 PyInstaller 打包
        install_dir = os.path.dirname(sys.executable)
    else:
        # 直接運行腳本
        install_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ==================== 設置環境 ====================
    os.chdir(install_dir)
    
    # 添加所有必要的 DLL 路徑
    python_dir = os.path.join(install_dir, "python")
    site_packages = os.path.join(python_dir, "Lib", "site-packages")
    torch_lib = os.path.join(site_packages, "torch", "lib")
    bnb_lib = os.path.join(site_packages, "bitsandbytes")
    
    # 構建完整 PATH
    dll_paths = [
        install_dir,
        python_dir,
        torch_lib,
        bnb_lib,
    ]
    
    existing_path = os.environ.get("PATH", "")
    os.environ["PATH"] = os.pathsep.join(dll_paths) + os.pathsep + existing_path
    
    # Windows DLL 搜索路徑
    if hasattr(os, 'add_dll_directory'):
        for dll_path in dll_paths:
            if os.path.isdir(dll_path):
                try:
                    os.add_dll_directory(dll_path)
                except Exception:
                    pass
    
    # ==================== 構建路徑 ====================
    python_exe = os.path.join(install_dir, "python", "pythonw.exe")
    main_py = os.path.join(install_dir, "app", "main.py")
    
    # 驗證路徑存在
    if not os.path.exists(python_exe):
        # 嘗試備用路徑
        python_exe = os.path.join(install_dir, "python", "python.exe")
    
    if not os.path.exists(python_exe):
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, 
            f"找不到 Python：{python_exe}", 
            "啟動錯誤", 0x10)
        return 1
    
    if not os.path.exists(main_py):
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, 
            f"找不到主程式：{main_py}", 
            "啟動錯誤", 0x10)
        return 1
    
    # ==================== 啟動主程式 ====================
    # 使用 CREATE_NO_WINDOW 避免控制台
    creationflags = 0
    if sys.platform == 'win32':
        creationflags = subprocess.CREATE_NO_WINDOW
    
    subprocess.Popen(
        [python_exe, main_py],
        cwd=install_dir,
        creationflags=creationflags
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
