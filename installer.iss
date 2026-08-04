[Setup]
AppName=Van Ban Thanh Giong Noi
AppVersion=1.0
DefaultDirName={autopf}\VanBanThanhGiongNoi
DefaultGroupName=Van ban thanh giong noi
OutputDir={#SourcePath}\installer
OutputBaseFilename=VanBanThanhGiongNoi_Setup
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile={#SourcePath}\assets\VanBanThanhGiongNoi.ico

[Files]
; Copy all files from the PyInstaller output folder to the installation directory
Source: "{#SourcePath}\dist\VanBanThanhGiongNoi\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Icons]
; Create a shortcut in the Start Menu and on the Desktop
Name: "{group}\Văn bản thành giọng nói"; Filename: "{app}\VanBanThanhGiongNoi.exe"
Name: "{commondesktop}\Văn bản thành giọng nói"; Filename: "{app}\VanBanThanhGiongNoi.exe"; Tasks: desktopicon
