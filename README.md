# HUIT Career Advisor AI — Tài liệu hướng dẫn dự án

> Hệ thống gợi ý ngành học thông minh dành cho học sinh THPT, sử dụng mô hình Machine Learning kết hợp giao diện desktop Tkinter.

---

## Mục lục

1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Cấu trúc thư mục](#2-cấu-trúc-thư-mục)
3. [Cài đặt môi trường](#3-cài-đặt-môi-trường)
4. [Chạy ứng dụng](#4-chạy-ứng-dụng)
5. [Huấn luyện lại model](#5-huấn-luyện-lại-model)
6. [Đóng gói thành file .exe](#6-đóng-gói-thành-file-exe)
7. [Các phương thức xét tuyển được hỗ trợ](#7-các-phương-thức-xét-tuyển-được-hỗ-trợ)
8. [Kiểm tra nhanh](#8-kiểm-tra-nhanh)
9. [Xử lý lỗi thường gặp](#9-xử-lý-lỗi-thường-gặp)

---

## 1. Yêu cầu hệ thống

| Thành phần | Yêu cầu tối thiểu |
|-----------|-------------------|
| **Hệ điều hành** | Windows 10/11 (64-bit) |
| **Python** | 3.10 trở lên |
| **RAM** | 4 GB (khuyến nghị 8 GB) |
| **Ổ cứng** | ~500 MB (bao gồm model files) |
| **Tkinter** | Đã tích hợp sẵn trong Python stdlib |

> [!NOTE]
> Tkinter **không cần cài thêm** — có sẵn trong Python. Nếu bị thiếu (thường trên Linux): `sudo apt install python3-tk`

---

## 2. Cấu trúc thư mục

```
Code_goi_y_huong_nghiep/
│
├── app_gui.py                    <- Entry point chạy app
├── requirements.txt              <- Thư viện runtime
├── requirements-dev.txt          <- Thư viện developer (PyInstaller, Pillow)
│
├── apps/desktop/
│   ├── app.py                    <- Toàn bộ giao diện và logic UI
│   ├── theme.py                  <- Bảng màu, font, spacing (Light/Dark mode)
│   └── assets/                   <- Icon, logo ứng dụng
│
├── huit_career_advisor/
│   ├── domain/
│   │   ├── advisory.py           <- Logic tư vấn: profile học sinh, xếp hạng phương thức
│   │   └── catalog.py            <- Danh mục ngành, tổ hợp môn, nhóm ngành
│   ├── inference/
│   │   ├── dgnl.py               <- Gợi ý ngành theo điểm ĐGNL
│   │   ├── academic_record.py    <- Gợi ý ngành theo điểm học bạ
│   │   ├── thpt.py               <- Gợi ý ngành theo điểm thi THPT QG
│   │   └── direct_admission.py   <- Gợi ý ngành theo tuyển thẳng
│   └── paths.py                  <- Quản lý đường dẫn (source + PyInstaller)
│
├── models/                       <- File model đã huấn luyện (.pkl)
│   ├── dgnl_models.pkl           <- Model ĐGNL (RF+NB, 89% accuracy)
│   ├── hocba_models.pkl          <- Model học bạ (~96 MB)
│   ├── pt1_models.pkl            <- Model THPT QG
│   ├── tt_models.pkl             <- Model tuyển thẳng
│   └── nganh_mapping.pkl         <- Ánh xạ mã ngành -> tên ngành
│
├── data/
│   └── DXDuong.xlsx              <- Dataset huấn luyện model
│
├── research/training/
│   ├── train_dgnl_models.py      <- Script huấn luyện ĐGNL
│   ├── train_hocba_models.py     <- Script huấn luyện học bạ
│   ├── train_thpt_models.py      <- Script huấn luyện THPT QG
│   └── train_tuyenthang_models.py <- Script huấn luyện tuyển thẳng
│
└── installer/
    ├── build_app.ps1             <- Script build .exe
    ├── huit_app.spec             <- Cấu hình PyInstaller
    └── huit_installer.iss        <- Cấu hình Inno Setup
```

---

## 3. Cài đặt môi trường

### Bước 1 — Tải dự án

```powershell
git clone <repository-url>
cd Code_goi_y_huong_nghiep
```

Hoặc giải nén ZIP rồi mở PowerShell tại thư mục gốc dự án.

### Bước 2 — Tạo môi trường ảo

```powershell
python -m venv .venv
```

### Bước 3 — Cài thư viện

Để **chạy app** (không cần build):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Để **phát triển + build .exe**:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

> [!IMPORTANT]
> Luôn chạy lệnh từ **thư mục gốc** (nơi chứa `app_gui.py`), không chạy từ thư mục con.

### Thư viện chính

| Thư viện | Phiên bản | Mục đích |
|---------|-----------|---------|
| `joblib` | >=1.3.0 | Load/save model ML |
| `numpy` | >=1.24.0 | Tính toán ma trận |
| `pandas` | >=2.0.0 | Xử lý dữ liệu bảng |
| `scikit-learn` | >=1.3.0 | Random Forest, Naive Bayes |
| `openpyxl` | >=3.1.0 | Đọc file Excel (dataset) |
| `pillow` | >=10.0.0 | Xử lý ảnh *(dev only)* |
| `pyinstaller` | >=6.0.0 | Build file .exe *(dev only)* |

---

## 4. Chạy ứng dụng

```powershell
.\.venv\Scripts\python.exe .\app_gui.py
```

Khi khởi động, app sẽ:

1. Load các model ML từ `models/` (~2–3 giây)
2. Hiển thị cửa sổ desktop 1360×880 px
3. Mở trang **Tổng quan** mặc định

> [!NOTE]
> Console in dòng `Loaded models with 89.0% accuracy` — đây là thông báo bình thường, không phải lỗi.

### Phím tắt

| Phím | Chức năng |
|------|-----------|
| `Ctrl + Shift + T` | Chuyển đổi Light / Dark mode |

---

## 5. Huấn luyện lại model

Dùng khi cần cập nhật dữ liệu mới hoặc cải thiện độ chính xác.

> [!WARNING]
> Quá trình huấn luyện mất **5–30 phút** tùy máy. Các file `.pkl` trong `models/` sẽ bị **ghi đè**.

**Yêu cầu:** File `data/DXDuong.xlsx` phải tồn tại.

### Huấn luyện từng model

```powershell
# Model ĐGNL (Đánh giá năng lực)
.\.venv\Scripts\python.exe .\research\training\train_dgnl_models.py

# Model Học bạ
.\.venv\Scripts\python.exe .\research\training\train_hocba_models.py

# Model THPT Quốc gia
.\.venv\Scripts\python.exe .\research\training\train_thpt_models.py

# Model Tuyển thẳng
.\.venv\Scripts\python.exe .\research\training\train_tuyenthang_models.py
```

### Huấn luyện tất cả cùng lúc

```powershell
@('dgnl','hocba','thpt','tuyenthang') | ForEach-Object {
    .\.venv\Scripts\python.exe ".\research\training\train_${_}_models.py"
}
```

Model đầu ra ghi vào `models/`:

| File | Phương thức |
|------|------------|
| `dgnl_models.pkl` | ĐGNL |
| `hocba_models.pkl` | Học bạ |
| `pt1_models.pkl` | THPT Quốc gia |
| `tt_models.pkl` | Tuyển thẳng |
| `nganh_mapping.pkl` | Ánh xạ mã ngành |

---

## 6. Đóng gói thành file .exe

> [!IMPORTANT]
> Cần cài `requirements-dev.txt` trước.

```powershell
.\installer\build_app.ps1
```

Script thực hiện:

1. Chạy **PyInstaller** theo `installer/huit_app.spec`
2. Đóng gói app + model + assets vào `dist/`
3. Chạy **Inno Setup** theo `installer/huit_installer.iss` → tạo file installer `.exe`

**Đầu ra:** `installer/installer_output/`

---

## 7. Các phương thức xét tuyển được hỗ trợ

Phiên bản desktop hiện tại tập trung vào 4 phương thức chính. Phương thức ĐGNL chuyên biệt ĐHSP-HCM không nằm trong phạm vi UI hiện tại.

| Phương thức | Đầu vào cần thiết | Model sử dụng |
|------------|------------------|---------------|
| **ĐGNL** | Tổng điểm 600–1200 (hoặc 4 điểm thành phần) | `dgnl_models.pkl` |
| **Học bạ** | Điểm TB 3 môn (thang 10), tổ hợp môn, ưu tiên KV/ĐT | `hocba_models.pkl` |
| **THPT Quốc gia** | Điểm 3 môn thi (thang 10), tổ hợp, ưu tiên KV/ĐT | `pt1_models.pkl` |
| **Tuyển thẳng** | ĐTB 3 năm (tổng thang 30), điểm Tiếng Anh | `tt_models.pkl` |

Tất cả phương thức hỗ trợ bổ sung:

- **Hồ sơ định hướng:** sở thích, tính cách, địa lý, nghề nghiệp gia đình
- **Nhóm ngành ưu tiên:** 9 nhóm chính thức của HUIT
- **Điểm ưu tiên:** Khu vực KV1–KV3 và đối tượng Nhóm 1, 2

### Công thức điểm ưu tiên THPT QG (quy chế 2023+)

| Tổng điểm 3 môn | Công thức |
|----------------|-----------|
| <= 22.5 | Áp dụng đầy đủ điểm KV + ĐT |
| > 22.5 | `UT = (30 - tổng) / 7.5 × mức_ưu_tiên` |
| = 30.0 | UT = 0 |

---

## 8. Kiểm tra nhanh

### Kiểm tra cú pháp toàn bộ code

```powershell
.\.venv\Scripts\python.exe -m compileall -q apps huit_career_advisor research app_gui.py
```

### Chạy regression/UAT smoke test

```powershell
.\.venv\Scripts\python.exe .\qa_test_runner.py
```

### Smoke test khởi động app (không hiện cửa sổ)

```powershell
.\.venv\Scripts\python.exe -c "from apps.desktop.app import App; app=App(); app.update(); print(app.winfo_geometry()); app.destroy()"
```

### Test inference ĐGNL

```powershell
.\.venv\Scripts\python.exe -c "
from huit_career_advisor.inference.dgnl import goi_y_nganh_simple
r = goi_y_nganh_simple(850)
for x in r[:3]: print(x['ten_nganh'], x['xac_suat'])
"
```

---

## 9. Xử lý lỗi thường gặp

### ModuleNotFoundError: No module named 'tkinter'

**Nguyên nhân:** Python không kèm Tkinter (Linux).

```bash
# Ubuntu/Debian:
sudo apt install python3-tk
```

---

### ModuleNotFoundError: No module named 'joblib'

**Nguyên nhân:** Chưa cài thư viện hoặc dùng sai Python.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

### FileNotFoundError: models/dgnl_models.pkl not found

**Nguyên nhân:** Thiếu file model trong thư mục `models/`.

**Cách sửa:** Chạy script huấn luyện ở Mục 5.

---

### App hiển thị nhưng kết quả toàn dấu gạch (—)

**Nguyên nhân thường gặp:** Chưa nhập điểm và bấm nút "Phân tích".

Nếu đã nhập đúng mà vẫn trống: kiểm tra console xem có lỗi từ model không.

---

### UnicodeDecodeError khi chạy trên Windows

**Nguyên nhân:** Console Windows dùng mã hóa CP1252.

```powershell
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe .\app_gui.py
```

---

### App bị đơ khi bấm "Phân tích Học bạ"

**Nguyên nhân:** `hocba_models.pkl` (~96 MB) mất vài giây để load lần đầu.

**Đây là hành vi bình thường** — lần sau sẽ nhanh hơn nhờ OS cache.

---

## Thông tin kỹ thuật

### Kiến trúc Model ML

| Thành phần | Tỷ lệ | Vai trò |
|-----------|-------|---------|
| Random Forest | 70% | Độ chính xác cao, ổn định |
| Naive Bayes | 30% | Nhanh, bổ sung đa dạng |

Kết quả ensemble được **boost** (×1.8) cho ngành thuộc nhóm ưa thích và **penalize** (×0.6) cho ngành ngoài nhóm. Tổ hợp môn phù hợp thêm ×1.15, không phù hợp ×0.35.

### Lưu trữ cài đặt

App lưu cài đặt giao diện (sáng/tối) tại:

```
%APPDATA%\HUITCareerAdvisor\settings.json
```
