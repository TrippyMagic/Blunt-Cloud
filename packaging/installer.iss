[Setup]
AppName=Blunt-Cloud
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\BluntCloud
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
OutputDir=..\dist
OutputBaseFilename=BluntCloud-Setup
Compression=lzma2
SolidCompression=yes
LicenseFile=..\LICENSE.txt
[Files]
Source: "..\dist\BluntCloud\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
[Icons]
Name: "{userprograms}\Blunt-Cloud"; Filename: "{app}\BluntCloud.exe"

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
