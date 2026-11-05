[Setup]
AppName=Blunt-Cloud
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\BluntCloud
PrivilegesRequired=lowest
Uninstallable=yes
UninstallDisplayName=Blunt-Cloud
UninstallDisplayIcon={app}\BluntCloud.exe
ArchitecturesAllowed=x64compatible
OutputDir=..\dist
OutputBaseFilename=BluntCloud-Setup
Compression=lzma2
SolidCompression=yes
LicenseFile=..\LICENSE.txt
[Files]
Source: "..\dist\BluntCloud\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
[Tasks]
Name: "startmenu"; Description: "Create a Start menu shortcut"; GroupDescription: "Shortcuts:"
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Icons]
Name: "{userprograms}\Blunt-Cloud"; Filename: "{app}\BluntCloud.exe"; WorkingDir: "{app}"; Tasks: startmenu
Name: "{userdesktop}\Blunt-Cloud"; Filename: "{app}\BluntCloud.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\BluntCloud.exe"; Description: "Launch Blunt-Cloud"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[InstallDelete]
Type: files; Name: "{app}\_internal\icuuc.dll"
Type: files; Name: "{app}\_internal\icudt78.dll"

Type: files; Name: "{userprograms}\Blunt-Cloud.lnk"; Tasks: not startmenu
Type: files; Name: "{userdesktop}\Blunt-Cloud.lnk"; Tasks: not desktopicon
