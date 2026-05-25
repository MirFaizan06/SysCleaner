; Inno Setup script — SysCleaner by Tech Bytes Design
; Compile with: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" syscleaner.iss

#define AppName        "SysCleaner"
#define AppVersion     "1.0.0"
#define AppPublisher   "Tech Bytes Design"
#define AppURL         "https://techbytesdesign.in"
#define AppExeName     "SysCleaner.exe"

[Setup]
AppId={{8A5F2C1D-3B6E-4F9A-B2C7-D8E1F5A4B3C2}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; Install for current user by default (no admin required for basic usage)
DefaultDirName={localappdata}\{#AppPublisher}\{#AppName}
DefaultGroupName={#AppPublisher}\{#AppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Output
OutputDir=dist\installer
OutputBaseFilename=SysCleaner_Setup_v{#AppVersion}
SetupIconFile=syscleaner.ico
UninstallDisplayIcon={app}\{#AppExeName}

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Appearance
WizardStyle=modern
WizardResizable=no
DisableWelcomePage=no
DisableDirPage=no

; Misc
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Create a &desktop shortcut";    GroupDescription: "Additional icons:"
Name: "startmenuicon";  Description: "Create a &Start Menu entry";    GroupDescription: "Additional icons:"; Flags: checkedonce

[Files]
; Main executable (built by PyInstaller)
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; AI agent documentation
Source: "CLAUDE.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start menu
Name: "{group}\{#AppName}";                         Filename: "{app}\{#AppExeName}"; Tasks: startmenuicon
Name: "{group}\{#AppName} (Administrator)";         Filename: "{app}\{#AppExeName}"; Parameters: ""; WorkingDir: "{app}"; Comment: "Run as Administrator for full functionality"; Tasks: startmenuicon

; Uninstall entry in Start Menu
Name: "{group}\Uninstall {#AppName}";               Filename: "{uninstallexe}"; Tasks: startmenuicon

; Desktop
Name: "{autodesktop}\{#AppName}";                   Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up any runtime files left behind
Type: filesandordirs; Name: "{app}"

[Code]
// Show a friendly note about Administrator mode during install
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    WizardForm.WelcomeLabel2.Caption + #13#10 +
    'Tip: For full functionality (system-level cleaning, ' +
    'Winsock reset, RAM optimization), right-click SysCleaner.exe ' +
    'and choose "Run as administrator".';
end;
