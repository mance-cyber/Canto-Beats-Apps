@echo off
REM Canto-beats GPU Launcher
REM This script ensures the app runs in the canto-env environment with GPU support

echo ========================================
echo Canto-beats GPU Launcher
echo ========================================
echo.

REM Activate canto-env
echo Activating canto-env environment...
call conda activate canto-env

if %errorlevel% neq 0 (
    echo ERROR: Failed to activate canto-env
    echo Please ensure conda is installed and canto-env exists
    pause
    exit /b 1
)

REM Verify GPU availability
echo.
echo Checking GPU status...
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA Available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU Only')"

if %errorlevel% neq 0 (
    echo WARNING: PyTorch check failed
    echo Continuing anyway...
)

REM Launch application
echo.
echo Starting Canto-beats...
echo ========================================
echo.
python main.py

REM Keep window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Application exited with error code: %errorlevel%
    echo ========================================
    pause
)
