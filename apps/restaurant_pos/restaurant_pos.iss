; Inno Setup script for Restaurant POS
; Compile with: ISCC.exe restaurant_pos.iss  (from apps\restaurant_pos\)

#define AppName      "Restaurant POS"
#define AppVersion   "1.0.0"
#define AppPublisher "Hospitality"
#define AppExeName   "RestaurantPOS.exe"
#define SourceExe    "..\release\RestaurantPOS.exe"
#define OutputDir    "..\release"

[Setup]
AppId={{A1B2C3D4-4444-5555-6666-AABBCCDDEEFF}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Hospitality\Restaurant POS
DefaultGroupName=Hospitality
OutputDir={#OutputDir}
OutputBaseFilename=RestaurantPOS_Setup
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
Name: "{group}\Restaurant POS";       Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall Restaurant POS"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Restaurant POS"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch Restaurant POS"; Flags: nowait postinstall skipifsilent
