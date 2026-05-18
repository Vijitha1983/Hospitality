; Inno Setup script for Hotel Desk
; Compile with: ISCC.exe hotel_desk.iss  (from apps\hotel_desk\)

#define AppName      "Hotel Desk"
#define AppVersion   "1.0.0"
#define AppPublisher "Hospitality"
#define AppExeName   "HotelDesk.exe"
#define SourceExe    "..\release\HotelDesk.exe"
#define OutputDir    "..\release"

[Setup]
AppId={{A1B2C3D4-1111-2222-3333-AABBCCDDEEFF}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Hospitality\Hotel Desk
DefaultGroupName=Hospitality
OutputDir={#OutputDir}
OutputBaseFilename=HotelDesk_Setup
SetupIconFile=
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "{#SourceExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Hotel Desk";       Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall Hotel Desk"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Hotel Desk"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch Hotel Desk"; Flags: nowait postinstall skipifsilent
