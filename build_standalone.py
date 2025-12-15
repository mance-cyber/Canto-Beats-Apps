"""
Build Standalone Installer for Canto-beats (CUDA Version)
Includes embedded Python environment with CUDA support - no Python installation required!

Usage:
    python build_standalone.py
"""

import os
import sys
import shutil
import subprocess
import zipfile
import urllib.request
from pathlib import Path


# Python embedded download URL
PYTHON_EMBED_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"


def download_file(url, dest):
    """Download a file with progress."""
    print(f"   Downloading: {url.split('/')[-1]}")
    urllib.request.urlretrieve(url, dest)
    print(f"   OK Downloaded")


def main():
    """Main build function."""
    print("=" * 60)
    print("Canto-beats Standalone Installer Builder (CUDA Version)")
    print("Includes NVIDIA GPU support for AI transcription")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    dist_dir = project_dir / "dist" / "Canto-beats-Standalone"
    python_dir = dist_dir / "python"
    app_dir = dist_dir / "app"
    
    # Clean previous build
    if dist_dir.exists():
        print("\nCleaning previous build...")
        shutil.rmtree(dist_dir)
    
    dist_dir.mkdir(parents=True, exist_ok=True)
    python_dir.mkdir(exist_ok=True)
    app_dir.mkdir(exist_ok=True)
    
    # Step 1: Download Python Embedded
    print("\n[1/6] Downloading Python Embedded...")
    python_zip = project_dir / "python-embed.zip"
    if not python_zip.exists():
        download_file(PYTHON_EMBED_URL, python_zip)
    else:
        print("   Using cached Python Embedded")
    
    # Extract Python
    print("\n[2/6] Extracting Python Embedded...")
    with zipfile.ZipFile(python_zip, 'r') as zf:
        zf.extractall(python_dir)
    print("   OK Python extracted")
    
    # Enable pip by modifying python311._pth
    pth_file = python_dir / "python311._pth"
    if pth_file.exists():
        content = pth_file.read_text()
        # Uncomment 'import site' line
        content = content.replace("#import site", "import site")
        # Add Lib/site-packages and app paths
        content += "\nLib\\site-packages\n"
        content += "..\\app\n"
        content += "..\\app\\src\n"
        pth_file.write_text(content)
        print("   OK Python path configured")
    
    # Step 3: Install pip
    print("\n[3/6] Installing pip...")
    get_pip = python_dir / "get-pip.py"
    download_file(GET_PIP_URL, get_pip)
    
    python_exe = python_dir / "python.exe"
    subprocess.run([str(python_exe), str(get_pip), "--no-warn-script-location"], 
                   cwd=str(python_dir), check=True)
    print("   OK pip installed")
    
    # Step 4: Install dependencies with CUDA support
    print("\n[4/6] Installing dependencies with CUDA support (this may take 20-30 minutes)...")
    
    pip_exe = python_dir / "Scripts" / "pip.exe"
    
    # Install PyTorch with CUDA 12.6 first (matching dev environment)
    print("   Installing PyTorch with CUDA 12.6 support...")
    try:
        subprocess.run(
            [str(pip_exe), "install", "--no-warn-script-location",
             "torch", "torchaudio", 
             "--index-url", "https://download.pytorch.org/whl/cu126"],
            cwd=str(python_dir),
            check=True
        )
        print("   OK PyTorch CUDA installed")
    except subprocess.CalledProcessError as e:
        print(f"   ERROR: PyTorch CUDA installation failed: {e}")
        return 1
    
    # Install other core dependencies
    core_deps = [
        "PySide6",
        "python-mpv",
        "transformers",
        "faster-whisper",
        "accelerate",
        "sentencepiece",
        "requests",
        "cryptography",
        "pysrt",
        "numpy",
        "Pillow",
        "huggingface_hub",
        "pydub",
        "soundfile",
        "python-dotenv",
        "SQLAlchemy",
        "librosa",
        "ffmpeg-python",
        "silero-vad",
        "opencc-python-reimplemented",
        "ctranslate2",
        "bitsandbytes",
    ]
    
    for dep in core_deps:
        print(f"   Installing: {dep}...")
        try:
            subprocess.run(
                [str(pip_exe), "install", "--no-warn-script-location", dep],
                cwd=str(python_dir),
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"   Warning: {dep} installation failed, continuing...")
    
    # Install llama-cpp-python with CUDA support (optional, for GGUF inference)
    print("   Installing llama-cpp-python with CUDA support...")
    try:
        subprocess.run(
            [str(pip_exe), "install", "--no-warn-script-location",
             "llama-cpp-python",
             "--extra-index-url", "https://abetlen.github.io/llama-cpp-python/whl/cu122"],
            cwd=str(python_dir),
            capture_output=True,
            check=True
        )
        print("   OK llama-cpp-python CUDA installed")
    except subprocess.CalledProcessError as e:
        print("   Warning: llama-cpp-python CUDA installation failed, continuing...")
    
    print("   OK Dependencies installed")
    
    # Step 5: Copy application files
    print("\n[5/6] Copying application files...")
    
    # Copy main.py
    shutil.copy(project_dir / "main.py", app_dir / "main.py")
    
    # Copy src
    if (project_dir / "src").exists():
        shutil.copytree(project_dir / "src", app_dir / "src")
    
    # Copy public
    if (project_dir / "public").exists():
        shutil.copytree(project_dir / "public", app_dir / "public")
    
    print("   OK Application files copied")
    
    # Step 6: Copy critical DLLs and executables
    print("\n[6/6] Copying DLLs and executables...")
    
    # Copy libmpv-2.dll
    libmpv_src = project_dir / "libmpv-2.dll"
    if libmpv_src.exists():
        shutil.copy(libmpv_src, dist_dir / "libmpv-2.dll")
        print("   OK libmpv-2.dll copied")
    else:
        print("   WARNING: libmpv-2.dll not found!")
    
    # Copy ffmpeg.exe and ffprobe.exe
    ffmpeg_src = project_dir / "ffmpeg.exe"
    ffprobe_src = project_dir / "ffprobe.exe"
    
    if ffmpeg_src.exists():
        shutil.copy(ffmpeg_src, dist_dir / "ffmpeg.exe")
        print("   OK ffmpeg.exe copied")
    else:
        print("   WARNING: ffmpeg.exe not found!")
        
    if ffprobe_src.exists():
        shutil.copy(ffprobe_src, dist_dir / "ffprobe.exe")
        print("   OK ffprobe.exe copied")
    else:
        print("   WARNING: ffprobe.exe not found!")
    
    # Copy any other DLLs from project root
    for dll in project_dir.glob("*.dll"):
        if dll.name != "libmpv-2.dll":  # Already copied
            shutil.copy(dll, dist_dir / dll.name)
            print(f"   OK {dll.name} copied")
    
    # Copy FFmpeg shared DLLs from conda (required for torchcodec/torchaudio VAD)
    print("   Copying FFmpeg shared DLLs for VAD support...")
    conda_lib = Path(os.environ.get("CONDA_PREFIX", Path.home() / "miniconda3")) / "Library" / "bin"
    ffmpeg_dlls = [
        "avcodec-60.dll", "avformat-60.dll", "avutil-58.dll",
        "swresample-4.dll", "swscale-7.dll", "avfilter-9.dll",
        "avdevice-60.dll", "postproc-57.dll",
        "libx264-164.dll", "libx265.dll"  # Video codec dependencies
    ]
    for dll_name in ffmpeg_dlls:
        dll_src = conda_lib / dll_name
        if dll_src.exists():
            shutil.copy(dll_src, python_dir / dll_name)
            print(f"   OK {dll_name} copied")
        else:
            print(f"   WARNING: {dll_name} not found in {conda_lib}")
    
    print("   OK DLLs and executables copied")
    
    # Create launcher EXE wrapper script
    launcher_py = dist_dir / "launcher.pyw"
    launcher_py.write_text('''
import os
import sys
import subprocess

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set up environment
os.chdir(script_dir)

# Add DLL directory to PATH
os.environ["PATH"] = script_dir + os.pathsep + os.environ.get("PATH", "")

# Add DLL directory for Windows
if hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(script_dir)

# Run the main application
python_exe = os.path.join(script_dir, "python", "pythonw.exe")
main_py = os.path.join(script_dir, "app", "main.py")

subprocess.run([python_exe, main_py], cwd=script_dir)
''', encoding="utf-8")
    
    # Create launcher batch file
    launcher = dist_dir / "Canto-beats.bat"
    launcher.write_text("""@echo off
cd /d "%~dp0"
set PATH=%~dp0;%PATH%
cd app
start "" "..\\python\\pythonw.exe" "main.py"
""", encoding="utf-8")
    
    # Create README
    readme = dist_dir / "README.txt"
    readme.write_text("""
Canto-beats Standalone Edition (CUDA Version)
==============================================

Requirements:
- NVIDIA GPU with CUDA support
- Windows 10/11 64-bit

No Python installation required!

Simply double-click "Canto-beats.exe" or "Canto-beats.bat" to start.

Note: First startup may take a few seconds to initialize.
      First transcription will download AI models (~3-5 GB).

Troubleshooting:
- If the app doesn't start, try running Canto-beats.bat
- Make sure your NVIDIA drivers are up to date
- Ensure you have at least 8GB VRAM for best performance

Support: https://cantobeats.com
""", encoding="utf-8")
    
    # Summary
    print("\n" + "=" * 60)
    print("BUILD COMPLETE!")
    print("=" * 60)
    
    # Calculate size
    total_size = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file())
    print(f"\nOutput: {dist_dir}")
    print(f"Total size: {total_size / 1024 / 1024 / 1024:.2f} GB")
    
    print("\nNext steps:")
    print("1. Test the standalone by running Canto-beats.bat")
    print("2. Create installer using Inno Setup if needed")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
