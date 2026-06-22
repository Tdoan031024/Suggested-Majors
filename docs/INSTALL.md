# Hướng dẫn cài đặt và vận hành

## 1. Yêu cầu môi trường

### Chạy từ source

- Windows 10/11 64-bit là môi trường mục tiêu thực tế.
- Python 3.10 trở lên.
- RAM tối thiểu 4 GB; khuyến nghị 8 GB do model học bạ khoảng 96 MB.
- Khoảng 500 MB dung lượng trống cho môi trường, model và build.
- Tkinter đi kèm bản Python Windows tiêu chuẩn.

### Build bộ cài

- Các yêu cầu trên.
- PyInstaller 6+.
- Inno Setup 6 nếu cần tạo installer.

## 2. Tạo môi trường Python

Mở PowerShell tại thư mục dự án:

```powershell
cd D:\ADuong_HUIT\Code_goi_y_huong_nghiep
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Để phát triển, test tài nguyên build và đóng gói:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

### Phụ thuộc runtime

```text
joblib>=1.3.0
numpy>=1.24.0
openpyxl>=3.1.0
pandas>=2.0.0
scikit-learn>=1.3.0
```

`pillow`, `psutil` và `pyinstaller` chỉ nằm trong requirements phát triển.

## 3. Kiểm tra tài nguyên bắt buộc

Trước khi chạy, xác nhận:

```powershell
Get-ChildItem .\models\*.pkl
Get-Item .\data\DXDuong.xlsx
Get-ChildItem .\apps\desktop\assets
```

Runtime chính cần bốn model phương thức và mapping ĐGNL:

- `models/dgnl_models.pkl`.
- `models/hocba_models.pkl`.
- `models/pt1_models.pkl`.
- `models/tt_models.pkl`.
- `models/nganh_mapping.pkl`.

## 4. Khởi động

```powershell
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe .\app_gui.py
```

Entry point gọi `App().mainloop()`.

### Lỗi chặn khởi động của revision hiện tại

Tại thời điểm lập tài liệu, smoke test thất bại với:

```text
AttributeError: '_tkinter.tkapp' object has no attribute 'profile_interest_display'
```

Nguyên nhân trong source: `profile_interest_display` và các biến hiển thị hồ sơ liên quan được khởi tạo trong `_update_api_key()` thay vì `_init_advisory_profile()`. Cần chuyển phần khởi tạo hồ sơ về đúng hàm trước khi coi hướng dẫn khởi động là đạt nghiệm thu.

## 5. Cấu hình Gemini

Sau khi ứng dụng khởi động được:

1. Mở trang **Cài đặt**.
2. Nhập Gemini API key vào ô cấu hình.
3. Khóa được lưu vào Windows Credential Manager khi API Windows hoạt động thành công.
4. Khi hỏi Gemini lần đầu, đọc hộp thoại dữ liệu sẽ gửi và chọn đồng ý hoặc từ chối.
5. Có thể xóa key hoặc đặt lại consent trong trang Cài đặt.

Không đặt API key trong source, `.env` được commit, lệnh build, ảnh chụp hoặc tài liệu bàn giao.

Endpoint được source sử dụng:

```text
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent
```

Nếu không có key, không consent hoặc request lỗi, trợ lý chuyển sang bộ trả lời offline.

## 6. Database và dữ liệu

Dự án không có database để import. File `DXDuong.xlsx` là dữ liệu huấn luyện, không được ứng dụng CRUD như cơ sở dữ liệu vận hành.

Nếu đã có model trong `models/`, người dùng không cần chạy training để sử dụng inference. Dataset vẫn được PyInstaller đóng gói theo cấu hình hiện tại.

## 7. Huấn luyện lại model

Sao lưu thư mục `models` trước khi chạy vì script sẽ ghi đè artifact đầu ra.

```powershell
# ĐGNL
.\.venv\Scripts\python.exe .\research\training\train_dgnl_models.py

# Học bạ
.\.venv\Scripts\python.exe .\research\training\train_hocba_models.py

# THPT
.\.venv\Scripts\python.exe .\research\training\train_thpt_models.py

# Tuyển thẳng
.\.venv\Scripts\python.exe .\research\training\train_tuyenthang_models.py
```

Sau training phải chạy evaluation và regression. Không chỉ dựa vào accuracy in ra từ train/test split của script training.

## 8. Đánh giá model

```powershell
.\.venv\Scripts\python.exe .\research\evaluation\topk_accuracy_evaluation.py
.\.venv\Scripts\python.exe .\research\evaluation\thu_thap_metrics_luan_van.py
```

Các script ghi kết quả vào:

- `research/evaluation/topk_accuracy_output.txt`.
- `research/evaluation/metrics_luan_van_output.txt`.

## 9. Kiểm thử

### Compile toàn bộ source

```powershell
.\.venv\Scripts\python.exe -m compileall -q apps huit_career_advisor research scripts app_gui.py qa_test_runner.py
```

### Regression/UAT

```powershell
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe .\qa_test_runner.py
```

Baseline ngày 21/06/2026: `35 PASS / 0 FAIL`.

### Desktop smoke test

```powershell
.\.venv\Scripts\python.exe -c "from apps.desktop.app import App; a=App(); print(sorted(a._pages)); a.destroy()"
```

Baseline ngày 21/06/2026: thất bại do lỗi khởi tạo biến hồ sơ được mô tả ở Mục 4.

## 10. Build bằng PyInstaller

Chạy từ thư mục gốc:

```powershell
.\installer\build_app.ps1
```

Script thực hiện:

1. Kiểm tra/cài PyInstaller trong `.venv`.
2. Xóa `build` và `dist` cũ.
3. Chạy `installer/huit_app.spec`.
4. Kiểm tra `dist\HUIT_GoiYNganh\HUIT_GoiYNganh.exe`.

PyInstaller đóng gói:

- Source desktop và domain/inference.
- `models/`.
- `apps/desktop/assets/`.
- `data/DXDuong.xlsx`.
- Runtime hook `_runtime_hook.py`.

Đầu ra là dạng onedir; khi chuyển máy phải giữ toàn bộ thư mục `dist\HUIT_GoiYNganh`.

## 11. Tạo installer bằng Inno Setup

Sau khi build PyInstaller thành công:

1. Cài Inno Setup 6.
2. Mở `installer\huit_installer.iss`.
3. Compile bằng Inno Setup Compiler.
4. Lấy kết quả trong `installer\installer_output`.

Installer hiện khai báo:

- App name: `HUIT - Gợi ý Ngành học`.
- Version: `2.0`.
- Quyền: `PrivilegesRequired=lowest`.
- Shortcut Start Menu và Desktop tùy chọn.
- Chạy app sau cài đặt.

Trước phát hành cần kiểm tra chữ ký số, cài mới, nâng cấp, gỡ cài đặt và chạy trên máy Windows sạch.

## 12. Cấu hình và dữ liệu người dùng

### Settings

```text
%APPDATA%\HUITCareerAdvisor\settings.json
```

Để reset theme/consent có thể đóng ứng dụng, sao lưu rồi xóa file này. API key Windows cần xóa qua trang Cài đặt hoặc Credential Manager target `HUIT_Career_Advisor_Gemini_Key`.

### Báo cáo

```text
%USERPROFILE%\Desktop\Bao_cao_Huong_nghiep_HUIT.html
```

## 13. Xử lý lỗi thường gặp

### `ModuleNotFoundError`

Đảm bảo dùng đúng Python trong `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Không load được model

- Kiểm tra đủ file trong `models`.
- Chạy từ thư mục gốc.
- Không dùng model `.pkl` từ nguồn không tin cậy.

### Gemini luôn trả lời offline

- Kiểm tra key đã được nhập ở trang Cài đặt.
- Kiểm tra consent.
- Kiểm tra Internet, quota và quyền model của project Google.
- Source hiện che chi tiết exception và tự fallback, vì vậy cần chạy debugger/log bổ sung nếu cần biết lỗi HTTP cụ thể.

### Font không hiển thị Roboto

- Kiểm tra ba file `.ttf` trong `apps\desktop\assets\fonts`.
- Nếu đăng ký GDI thất bại, theme tự fallback về Segoe UI.

### Console lỗi tiếng Việt

```powershell
$env:PYTHONIOENCODING = 'utf-8'
```

## 14. Checklist bàn giao bản chạy

- [ ] Sửa desktop smoke test.
- [ ] Compile đạt.
- [ ] Regression/UAT đạt.
- [ ] Kiểm tra bốn model và metadata.
- [ ] Kiểm thử Gemini với key thử nghiệm không commit.
- [ ] Test light/dark mode và resize.
- [ ] Test xuất báo cáo.
- [ ] Build PyInstaller từ worktree sạch.
- [ ] Test installer trên Windows sạch.
- [ ] Xác nhận installer có chữ ký số trước khi phát hành công khai.

