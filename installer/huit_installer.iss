; ============================================================
;  huit_installer.iss – Inno Setup Script
;  Tạo bộ installer .exe cho HUIT – Gợi ý Ngành học
;
;  Yêu cầu: Inno Setup 6  https://jrsoftware.org/isinfo.php
;  Cách dùng:
;    1. Chạy build_app.ps1 trước (tạo thư mục dist\HUIT_GoiYNganh)
;    2. Mở file này bằng Inno Setup Compiler
;    3. Nhấn Ctrl+F9 (Build) → ra file HUIT_GoiYNganh_Setup.exe
; ============================================================

#define AppName      "HUIT - Gợi ý Ngành học"
#define AppVersion   "2.0"
#define AppPublisher "Trường ĐH Công Thương TP.HCM"
#define AppURL       "https://huit.edu.vn"
#define AppExeName   "HUIT_GoiYNganh.exe"
; Đường dẫn thư mục dist (build xong từ PyInstaller)
#define DistDir      "..\dist\HUIT_GoiYNganh"

[Setup]
AppId={{A3B2C1D0-HUIT-2025-GOINGANH-HUIT0001}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\HUIT_GoiYNganh
DefaultGroupName={#AppName}
AllowNoIcons=yes
; Icon ứng dụng (bỏ comment nếu có file .ico)
SetupIconFile=..\apps\desktop\assets\app_icon.ico
OutputBaseFilename=HUIT_GoiYNganh_Setup_v{#AppVersion}
OutputDir=installer_output
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Không yêu cầu quyền admin (cài vào AppData nếu muốn)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng trên Desktop"; \
  GroupDescription: "Biểu tượng:"; Flags: unchecked

[Files]
; Toàn bộ thư mục dist (gồm .exe, models, thư viện Python)
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu
Name: "{group}\{#AppName}";       Filename: "{app}\{#AppExeName}"
Name: "{group}\Gỡ cài đặt";      Filename: "{uninstallexe}"
; Desktop (nếu user tích chọn)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; \
  Tasks: desktopicon

[Run]
; Tuỳ chọn chạy app ngay sau khi cài
Filename: "{app}\{#AppExeName}"; \
  Description: "Chạy {#AppName} ngay bây giờ"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Dọn sạch __pycache__ khi gỡ cài đặt
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\models"
