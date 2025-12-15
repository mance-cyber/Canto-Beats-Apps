; Canto-beats Standalone Installer (includes Python + MPV)
; No Python or additional software installation required!
; Includes VC++ Runtime for fresh Windows installations

#define MyAppName "Canto-beats"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Canto-beats"
#define MyAppURL "https://github.com/mance-cyber/Canto-Beats-Apps"
#define MyAppExeName "Canto-beats.exe"

[Setup]
AppId={{B2C3D4E5-F6A7-8901-BCDE-F12345678901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Canto-beats-Full-Setup
; Setup installer icon
SetupIconFile=..\public\app_icon.ico
; Uninstall icon
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DiskSpanning=no
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; ========================================
; RUNTIME DEPENDENCIES (for fresh Windows)
; ========================================
; VC++ 2015-2022 Redistributable - required for libmpv-2.dll
Source: "redist\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
; D3DCompiler for MPV ANGLE backend
Source: "redist\d3dcompiler_47.dll"; DestDir: "{app}"; Flags: ignoreversion

; ========================================
; PYTHON ENVIRONMENT
; ========================================
; Python environment and all dependencies
Source: "..\dist\Canto-beats-Standalone\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs

; ========================================
; APPLICATION FILES
; ========================================
; Application files
Source: "..\dist\Canto-beats-Standalone\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs
; Launcher EXE (with icon embedded)
Source: "..\dist\Canto-beats-Standalone\Canto-beats.exe"; DestDir: "{app}"; Flags: ignoreversion
; MPV Library (critical!)
Source: "..\dist\Canto-beats-Standalone\libmpv-2.dll"; DestDir: "{app}"; Flags: ignoreversion
; FFmpeg for thumbnail generation
Source: "..\dist\Canto-beats-Standalone\ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Canto-beats-Standalone\ffprobe.exe"; DestDir: "{app}"; Flags: ignoreversion
; README
Source: "..\dist\Canto-beats-Standalone\README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
; Start menu shortcut with icon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop shortcut with icon
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Install VC++ Runtime silently (only if needed)
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/quiet /norestart"; StatusMsg: "正在安裝 Visual C++ Runtime..."; Flags: waituntilterminated skipifdoesntexist
; Launch application after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
