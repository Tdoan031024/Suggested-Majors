# HUIT Career Advisor Desktop

Ứng dụng desktop Tkinter gợi ý ngành học HUIT từ các mô hình ML đã huấn luyện.

## Cấu trúc

```text
apps/
└── desktop/              # Ứng dụng desktop Tkinter

huit_career_advisor/
├── domain/               # Catalog ngành, nhóm ngành, tổ hợp
├── inference/            # Logic suy luận từ model đã huấn luyện
└── paths.py              # Đường dẫn runtime

data/                     # Dataset nghiên cứu
models/                   # Model artifact dùng khi chạy ứng dụng
research/                 # Code huấn luyện và đánh giá model
installer/                # PyInstaller và Inno Setup
scripts/                  # Compatibility wrapper cho import cũ
```

## Cài đặt

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Chạy app desktop

```powershell
.\.venv\Scripts\python.exe .\app_gui.py
```

## Đóng gói file .exe

```powershell
.\installer\build_app.ps1
```

## Nghiên cứu và tạo model

Dataset: `data/DXDuong.xlsx`

```powershell
.\.venv\Scripts\python.exe .\research\training\train_hocba_models.py
.\.venv\Scripts\python.exe .\research\training\train_thpt_models.py
.\.venv\Scripts\python.exe .\research\training\train_tuyenthang_models.py
.\.venv\Scripts\python.exe .\research\training\train_dgnl_models.py
```

Model được ghi vào `models/`.

## Kiểm tra

```powershell
.\.venv\Scripts\python.exe -m compileall -q apps huit_career_advisor research app_gui.py
.\.venv\Scripts\python.exe -c "from apps.desktop.app import App; app=App(); app.update(); print(app.winfo_geometry()); app.destroy()"
```
