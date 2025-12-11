@echo off
REM Canto-beats Build Script
REM Compiles the application using Nuitka for code protection

echo ============================================================
echo Canto-beats Build Script
echo ============================================================
echo.

REM Activate conda environment if available
call conda activate canto-env 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Conda environment not found, using system Python
)

REM Check Python version
python --version
echo.

REM Run Nuitka build script
python build_nuitka.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build completed successfully!
    echo Output file: dist\Canto-beats.exe
) else (
    echo.
    echo Build failed! Check the error messages above.
)

pause
