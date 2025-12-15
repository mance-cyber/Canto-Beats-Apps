# Redistributable Files for Canto-beats Installer

This folder contains runtime dependencies required for MPV to work on fresh Windows installations.

## Required Files

### 1. vc_redist.x64.exe (Required)
**Visual C++ 2015-2022 Redistributable for x64**

Download from Microsoft:
https://aka.ms/vs/17/release/vc_redist.x64.exe

This is required because `libmpv-2.dll` depends on Visual C++ runtime libraries (VCRUNTIME140.dll, etc.)

### 2. d3dcompiler_47.dll (Auto-copied)
**DirectX Shader Compiler**

This should be automatically copied from `C:\Windows\System32\d3dcompiler_47.dll`.
If missing, copy it manually from any Windows 10/11 system.

Required because MPV uses ANGLE backend for video rendering.

## Notes

- The installer will only install VC++ Runtime if it's not already present on the target system
- Both files together add approximately 28 MB to the installer size
- These dependencies ensure MPV works on completely fresh Windows installations
