; Canto-beats Installer (PyInstaller version)
; Uses PyInstaller output for complete dependency bundling
; No Python or additional software installation required!

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
OutputBaseFilename=Canto-beats-Setup-v{#MyAppVersion}
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
; VC++ 2015-2022 Redistributable - may be needed for some DLLs
Source: "redist\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
; D3DCompiler for MPV ANGLE backend
Source: "redist\d3dcompiler_47.dll"; DestDir: "{app}"; Flags: ignoreversion

; ========================================
; PYINSTALLER OUTPUT (complete app bundle)
; ========================================
; Main executable
Source: "..\dist\Canto-beats\Canto-beats.exe"; DestDir: "{app}"; Flags: ignoreversion
; Internal dependencies (all Python packages, DLLs, etc.)
Source: "..\dist\Canto-beats\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start menu shortcut with icon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop shortcut with icon
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Install VC++ Runtime silently (only if needed)
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/quiet /norestart"; StatusMsg: "Installing Visual C++ Runtime..."; Flags: waituntilterminated skipifdoesntexist
; Launch application after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
