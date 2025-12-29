@echo off
title Canto-beats
cd /d "%~dp0"

REM Check for embedded Python first
if exist "python\pythonw.exe" (
    start "" "python\pythonw.exe" "app\main.py"
    exit
)

if exist "python\python.exe" (
    start "" "python\python.exe" "app\main.py"
    exit
)

REM Fallback to system Python
where pythonw >nul 2>&1
if %ERRORLEVEL% == 0 (
    start "" pythonw "app\main.py"
    exit
)

where python >nul 2>&1
if %ERRORLEVEL% == 0 (
    start "" python "app\main.py"
    exit
)

REM Python not found
echo ERROR: Python not found!
echo Please install Python 3.11 from https://www.python.org/
pause
