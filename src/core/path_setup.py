"""
Centralized path setup for all external dependencies.
This module should be imported FIRST in main.py before any other modules.

Handles:
- FFmpeg (ffmpeg.exe, ffprobe.exe) for thumbnail/audio processing
- libmpv-2.dll for video playback
- Any other external dependencies
- CRITICAL PATCHES for PyInstaller compatibility
"""

import os
import sys
from pathlib import Path

# ============================================
# CRITICAL PATCH: TORCHCODEC METADATA FIX
# transformers.audio_utils tries to get torchcodec version which fails in PyInstaller
# This MUST be patched before ANY transformers import
# ============================================
import importlib.metadata
_original_metadata_version = importlib.metadata.version

def _patched_metadata_version(package):
    """Patch to provide fake version for torchcodec to prevent import failures."""
    if package == 'torchcodec':
        return '0.0.0'  # Fake version to prevent PackageNotFoundError
    return _original_metadata_version(package)

importlib.metadata.version = _patched_metadata_version

# NOTE: We do NOT patch subprocess.Popen globally as it breaks asyncio on Windows.
# Console window hiding is handled in specific files (video_utils.py, audio_utils.py, etc.)
# using subprocess.run(..., creationflags=CREATE_NO_WINDOW)


def _get_app_directories():
    """
    Get all possible application directories to search for dependencies.
    
    Returns:
        List of Path objects representing possible install/app directories
    """
    dirs = []
    
    # For frozen/packaged applications
    if getattr(sys, 'frozen', False):
        # 1. Directory of the executable
        exe_dir = Path(sys.executable).parent
        dirs.append(exe_dir)
        
        # 1b. macOS app bundle - check for bundled binaries in public/bin
        if sys.platform == 'darwin':
            app_contents = exe_dir.parent  # Contents/
            dirs.append(app_contents / 'Resources' / 'public' / 'bin')
            dirs.append(app_contents / 'Frameworks' / 'public' / 'bin')
    
    # 2. Installed location: C:\Program Files (x86)\Canto-beats
    #    When running from: app\src\core\path_setup.py
    #    Go up 4 levels: core -> src -> app -> install_dir
    current_file = Path(__file__)
    install_dir = current_file.parent.parent.parent.parent
    dirs.append(install_dir)
    
    # 3. Development location: canto-beats root
    #    When running from: src\core\path_setup.py
    #    Go up 3 levels: core -> src -> canto-beats
    project_root = current_file.parent.parent.parent
    dirs.append(project_root)
    
    # 3b. Bundled binaries in public/bin
    dirs.append(project_root / 'public' / 'bin')
    
    # 4. Current working directory
    dirs.append(Path.cwd())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_dirs = []
    for d in dirs:
        resolved = d.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_dirs.append(d)
    
    return unique_dirs


def setup_all_paths():
    """
    Setup PATH environment variable for all external dependencies (cross-platform).
    Should be called once at application startup.
    
    Returns:
        dict with status of each dependency
    """
    from utils.logger import setup_logger
    logger = setup_logger()
    
    results = {
        'ffmpeg': False,
        'libmpv': False,
        'directories_added': []
    }
    
    # Determine executable/library names based on platform
    if sys.platform == 'darwin':
        ffmpeg_name = 'ffmpeg'
        libmpv_name = 'libmpv.dylib'
    else:  # Windows
        ffmpeg_name = 'ffmpeg.exe'
        libmpv_name = 'libmpv-2.dll'
    
    app_dirs = _get_app_directories()
    
    # Add Homebrew paths for macOS
    if sys.platform == 'darwin':
        homebrew_paths = [
            Path('/opt/homebrew/bin'),   # Apple Silicon
            Path('/opt/homebrew/lib'),   # Apple Silicon libs
            Path('/usr/local/bin'),       # Intel Mac
            Path('/usr/local/lib'),       # Intel Mac libs
        ]
        app_dirs = homebrew_paths + app_dirs
    
    logger.info(f"Searching for dependencies in: {[str(d) for d in app_dirs]}")
    
    # Check what dependencies exist in each directory
    for dir_path in app_dirs:
        if not dir_path.exists():
            continue
            
        dir_str = str(dir_path)
        has_ffmpeg = (dir_path / ffmpeg_name).exists()
        has_libmpv = (dir_path / libmpv_name).exists()
        
        # On macOS, also check for alternate libmpv names
        if sys.platform == 'darwin' and not has_libmpv:
            for alt_name in ['libmpv.2.dylib', 'libmpv.1.dylib']:
                if (dir_path / alt_name).exists():
                    has_libmpv = True
                    break
        
        if has_ffmpeg:
            results['ffmpeg'] = True
            logger.info(f"Found {ffmpeg_name} in: {dir_str}")
            
        if has_libmpv:
            results['libmpv'] = True
            logger.info(f"Found {libmpv_name} in: {dir_str}")
        
        # Add to PATH if any dependency found
        if has_ffmpeg or has_libmpv:
            # On Windows, PATH comparison is case-insensitive
            if sys.platform == 'win32':
                if dir_str.lower() not in os.environ["PATH"].lower():
                    os.environ["PATH"] = dir_str + os.pathsep + os.environ["PATH"]
                    results['directories_added'].append(dir_str)
                    logger.info(f"Added to PATH: {dir_str}")
            else:
                if dir_str not in os.environ["PATH"]:
                    os.environ["PATH"] = dir_str + os.pathsep + os.environ["PATH"]
                    results['directories_added'].append(dir_str)
                    logger.info(f"Added to PATH: {dir_str}")
            
            # Also use os.add_dll_directory for Python 3.8+ (Windows only)
            if sys.platform == 'win32' and hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(dir_str)
                    logger.info(f"Added DLL directory: {dir_str}")
                except Exception as e:
                    logger.warning(f"Failed to add DLL directory {dir_str}: {e}")
    
    # Log summary
    if results['ffmpeg']:
        logger.info("[OK] FFmpeg available")
    else:
        if sys.platform == 'darwin':
            logger.warning("[!] FFmpeg not found - run: brew install ffmpeg")
        else:
            logger.warning("[!] FFmpeg not found - thumbnails will not work")
        
    # Note: libmpv is no longer required on macOS (using AVPlayer instead)
    if results['libmpv']:
        logger.info("[OK] libmpv available")
    # Removed libmpv warning - AVPlayer is the primary player on macOS
    
    return results



def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to a resource file, works both in development and packaged app.
    
    Args:
        relative_path: Path relative to src directory, e.g. "resources/icons/play.svg"
        
    Returns:
        Absolute path to the resource
    """
    # Try multiple possible base directories
    possible_bases = []
    
    # For frozen/packaged applications (PyInstaller)
    if getattr(sys, 'frozen', False):
        # ===== macOS .app bundle structure =====
        # Executable: Canto-beats.app/Contents/MacOS/Canto-beats
        # Resources:  Canto-beats.app/Contents/Resources/src/
        exe_dir = Path(sys.executable).parent  # Contents/MacOS
        contents_dir = exe_dir.parent  # Contents/
        
        # Primary: macOS app bundle structure
        possible_bases.append(contents_dir / "Resources" / "src")
        possible_bases.append(contents_dir / "Resources")
        possible_bases.append(contents_dir / "Frameworks" / "src")
        
        # Secondary: PyInstaller onefile (_MEIPASS)
        if hasattr(sys, '_MEIPASS'):
            meipass = Path(sys._MEIPASS)
            possible_bases.append(meipass / "src")
            possible_bases.append(meipass)
        
        # Fallback: Windows/Linux structure
        possible_bases.append(exe_dir / "_internal" / "src")
        possible_bases.append(exe_dir / "src")
        possible_bases.append(exe_dir)
    
    # Development: src is in project root
    current_file = Path(__file__)
    src_dir = current_file.parent.parent  # path_setup.py -> core -> src
    possible_bases.append(src_dir)
    
    # Also try project root / src
    project_root = src_dir.parent
    possible_bases.append(project_root / "src")
    
    # CWD
    possible_bases.append(Path.cwd() / "src")
    possible_bases.append(Path.cwd())
    
    # Standalone build: app/src structure
    possible_bases.append(Path.cwd() / "app" / "src")
    possible_bases.append(Path.cwd() / "app")
    
    # Try each base
    for base in possible_bases:
        full_path = base / relative_path
        if full_path.exists():
            return str(full_path)
    
    # Fallback: return original relative path (may fail)
    return relative_path


def get_ffmpeg_path() -> str:
    """
    Get the full path to ffmpeg executable.
    Works in both development and packaged app environments.
    
    Priority:
    1. Bundled ffmpeg in .app bundle (for packaged apps)
    2. Homebrew paths (for development)
    3. System paths
    
    Returns:
        Full path to ffmpeg, or 'ffmpeg' if not found (relies on PATH)
    """
    import shutil
    
    # For packaged apps, check bundled ffmpeg FIRST
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent  # Contents/MacOS
        bundled_ffmpeg = exe_dir / 'ffmpeg'
        if bundled_ffmpeg.exists():
            return str(bundled_ffmpeg)
    
    # For macOS, check known Homebrew paths
    if sys.platform == 'darwin':
        known_paths = [
            '/opt/homebrew/bin/ffmpeg',  # Apple Silicon Homebrew
            '/usr/local/bin/ffmpeg',      # Intel Mac Homebrew
            '/usr/bin/ffmpeg',            # System ffmpeg (rare)
        ]
        
        for path in known_paths:
            if Path(path).exists():
                return path
    
    # Try shutil.which (works in development/non-sandboxed environments)
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path
    
    # Windows: check known paths
    if sys.platform == 'win32':
        known_paths = [
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\ffmpeg\bin\ffmpeg.exe',
        ]
        for path in known_paths:
            if Path(path).exists():
                return path
    
    # Last resort: return 'ffmpeg' and hope it's in PATH
    return 'ffmpeg'


def get_ffprobe_path() -> str:
    """
    Get the full path to ffprobe executable.
    Works in both development and packaged app environments.
    
    Priority:
    1. Bundled ffprobe in .app bundle (for packaged apps)
    2. Homebrew paths (for development)
    3. System paths
    
    Returns:
        Full path to ffprobe, or 'ffprobe' if not found (relies on PATH)
    """
    import shutil
    
    # For packaged apps, check bundled ffprobe FIRST
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent  # Contents/MacOS
        bundled_ffprobe = exe_dir / 'ffprobe'
        if bundled_ffprobe.exists():
            return str(bundled_ffprobe)
    
    # For macOS, check known Homebrew paths
    if sys.platform == 'darwin':
        known_paths = [
            '/opt/homebrew/bin/ffprobe',  # Apple Silicon Homebrew
            '/usr/local/bin/ffprobe',      # Intel Mac Homebrew
            '/usr/bin/ffprobe',            # System ffprobe (rare)
        ]
        
        for path in known_paths:
            if Path(path).exists():
                return path
    
    # Try shutil.which (works in development/non-sandboxed environments)
    ffprobe_path = shutil.which('ffprobe')
    if ffprobe_path:
        return ffprobe_path
    
    # Windows: check known paths
    if sys.platform == 'win32':
        known_paths = [
            r'C:\Program Files\ffmpeg\bin\ffprobe.exe',
            r'C:\ffmpeg\bin\ffprobe.exe',
        ]
        for path in known_paths:
            if Path(path).exists():
                return path
    
    # Last resort: return 'ffprobe' and hope it's in PATH
    return 'ffprobe'


def get_icon_path(icon_name: str) -> str:
    """
    Get path to an icon file.
    
    Args:
        icon_name: Name of the icon without extension, e.g. "play", "pause"
        
    Returns:
        Absolute path to the icon SVG file
    """
    return get_resource_path(f"resources/icons/{icon_name}.svg")


# Auto-run on import
if __name__ != "__main__":
    # Only auto-run when imported, not when run directly
    pass

