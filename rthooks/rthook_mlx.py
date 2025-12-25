"""
PyInstaller runtime hook for MLX.
Sets up environment for MLX to find its metallib files in packaged app.
This runs BEFORE any other imports, ensuring MLX can find its libraries.
"""
import sys
import os
from pathlib import Path

def setup_mlx_environment():
    """Setup MLX environment variables for packaged app."""
    
    # Only run in frozen (packaged) environment
    if not getattr(sys, 'frozen', False):
        return
    
    # Build list of possible mlx lib paths
    possible_paths = []
    
    # macOS .app bundle structure: Contents/Frameworks/mlx/lib
    exe_dir = Path(sys.executable).parent  # Contents/MacOS
    contents_dir = exe_dir.parent  # Contents/
    possible_paths.append(contents_dir / 'Frameworks' / 'mlx' / 'lib')
    possible_paths.append(contents_dir / 'Frameworks' / 'mlx')
    possible_paths.append(contents_dir / 'Frameworks')
    possible_paths.append(contents_dir / 'Resources' / 'mlx' / 'lib')
    possible_paths.append(contents_dir / 'Resources' / 'mlx')
    
    # PyInstaller onefile _MEIPASS structure
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
        possible_paths.append(base_path / 'mlx' / 'lib')
        possible_paths.append(base_path / 'mlx')
        possible_paths.append(base_path / 'Resources' / 'mlx' / 'lib')
        possible_paths.append(base_path)
    
    for mlx_lib_path in possible_paths:
        metallib_path = mlx_lib_path / 'mlx.metallib'
        if metallib_path.exists():
            # Set environment variables for MLX
            current_dyld = os.environ.get('DYLD_LIBRARY_PATH', '')
            os.environ['DYLD_LIBRARY_PATH'] = str(mlx_lib_path) + (':' + current_dyld if current_dyld else '')
            
            # Set custom env var that our code uses
            os.environ['MLX_METAL_PATH'] = str(metallib_path)
            os.environ['MLX_DEFAULT_METALLIB_PATH'] = str(metallib_path)
            
            print(f"[MLX Runtime Hook] ✅ Found metallib at: {metallib_path}")
            print(f"[MLX Runtime Hook] Set DYLD_LIBRARY_PATH: {mlx_lib_path}")
            return
    
    # Log if not found
    searched = [str(p / 'mlx.metallib') for p in possible_paths]
    print(f"[MLX Runtime Hook] ⚠️ metallib not found. Searched: {searched}")

# Run setup immediately when hook is loaded
setup_mlx_environment()
