; Canto-beats Inno Setup Script
; Creates a professional Windows installer

#define MyAppName "Canto-beats"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Canto-beats"
#define MyAppURL "https://github.com/mance-cyber/Canto-Beats-Apps"
#define MyAppExeName "Canto-beats.bat"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Canto-beats-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Application files from portable distribution
Source: "..\dist\Canto-beats-Portable\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\Canto-beats-Portable\Canto-beats.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Canto-beats-Portable\install.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Canto-beats-Portable\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Canto-beats-Portable\README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Install Dependencies"; Filename: "{app}\install.bat"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
