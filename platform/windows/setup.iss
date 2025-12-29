; Canto-beats Inno Setup Script
; Generated for Standalone distribution

#define MyAppName "Canto-beats"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Canto-beats Team"
#define MyAppExeName "Canto-beats.bat"
#define MyAppIcon "public\app_icon.ico"

[Setup]
AppId={{E8A2F4C0-8B1D-4C3E-9A5F-6D7E8F9A0B1C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=Canto-beats-Setup
SetupIconFile={#MyAppIcon}
UninstallDisplayIcon={app}\app\public\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Python embedded environment
Source: "dist\Canto-beats-Standalone\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs createallsubdirs

; Application files
Source: "dist\Canto-beats-Standalone\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs

; DLLs and executables
Source: "dist\Canto-beats-Standalone\libmpv-2.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Canto-beats-Standalone\ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Canto-beats-Standalone\ffprobe.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Canto-beats-Standalone\launcher.pyw"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Canto-beats-Standalone\Canto-beats.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app\public\app_icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app\public\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
