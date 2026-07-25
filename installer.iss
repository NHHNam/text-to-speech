[Setup]
AppName=Offline TTS
AppVersion=1.0
DefaultDirName={autopf}\OfflineTTS
DefaultGroupName=Offline TTS
OutputDir=.\installer
OutputBaseFilename=OfflineTTS_Setup
Compression=lzma2/ultra64
SolidCompression=yes

[Files]
; Copy all files from the PyInstaller output folder to the installation directory
Source: "dist\OfflineTTS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Create a shortcut in the Start Menu and on the Desktop
Name: "{group}\Offline TTS"; Filename: "{app}\OfflineTTS.exe"
Name: "{commondesktop}\Offline TTS"; Filename: "{app}\OfflineTTS.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"
