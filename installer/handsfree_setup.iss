; Inno Setup Script for Handsfree by Apex Caliber Labs
; Generates Handsfree_Setup.exe

#define MyAppName "Handsfree"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Apex Caliber Labs"
#define MyAppURL "https://github.com/apexcaliberlabs/Handsfree"
#define MyAppExeName "Handsfree.exe"

[Setup]
AppId={{5E47BF3E-8162-4D90-A88E-325A3841A87D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Apex Caliber Labs\Handsfree
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Handsfree_Setup
SetupIconFile=..\handsfree\ui\assets\handsfree.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start Handsfree automatically when Windows starts"; GroupDescription: "Windows Integration:"

[Files]
Source: "..\dist\Handsfree\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Handsfree"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Handsfree"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\Handsfree"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--background"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,Handsfree}"; Flags: nowait postinstall skipifsilent
