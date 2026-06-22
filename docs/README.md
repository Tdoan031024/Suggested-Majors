# HUIT Career Advisor AI — Tài liệu bàn giao kỹ thuật

**Loại sản phẩm:** Ứng dụng desktop Windows  
**Phiên bản hiển thị trong source:** 2.0  
**Ngày đối chiếu source:** 21/06/2026

## 1. Giới thiệu

HUIT Career Advisor AI là ứng dụng desktop hỗ trợ thí sinh tham khảo ngành đào tạo tại Trường Đại học Công Thương TP.HCM (HUIT). Ứng dụng nhận điểm và thông tin định hướng cá nhân, gọi các mô hình Machine Learning đã huấn luyện để xếp hạng ngành, đồng thời hỗ trợ so sánh bốn phương thức xét tuyển:

- Điểm thi Đánh giá năng lực (ĐGNL).
- Điểm học bạ THPT.
- Tuyển thẳng.
- Điểm thi THPT Quốc gia.

Ngoài các luồng dự đoán, ứng dụng có trang tổng quan hồ sơ, trợ lý hướng nghiệp offline/Gemini, light/dark mode, lưu cấu hình người dùng và xuất báo cáo HTML.

## 2. Phạm vi thực tế của hệ thống

Source code hiện tại là ứng dụng **Tkinter chạy cục bộ**, không phải ứng dụng web. Dự án không có:

- Frontend web JavaScript/HTML độc lập.
- Backend HTTP server.
- Database quan hệ hoặc NoSQL.
- Cơ chế tài khoản người dùng hoặc đồng bộ dữ liệu qua máy chủ.

HTML trong source chỉ là mẫu báo cáo được sinh ra trên máy người dùng và mở bằng trình duyệt mặc định.

## 3. Công nghệ sử dụng

| Nhóm | Công nghệ | Vai trò |
|---|---|---|
| Ngôn ngữ | Python 3.10+ | Toàn bộ ứng dụng, xử lý dữ liệu và ML |
| Giao diện | Tkinter, ttk | Desktop UI |
| Xử lý dữ liệu | pandas, NumPy, openpyxl | Đọc và tiền xử lý Excel |
| Machine Learning | scikit-learn | Random Forest, Gaussian Naive Bayes, encoder và đánh giá |
| Lưu model | joblib/pickle | Đóng gói model, encoder và metadata |
| AI ngoài hệ thống | Google Gemini REST API | Chat tự do khi có API key và consent |
| Bảo mật khóa | Windows Credential Manager API | Lưu Gemini API key trên Windows |
| Đóng gói | PyInstaller | Tạo thư mục ứng dụng Windows |
| Cài đặt | Inno Setup 6 | Tạo bộ cài `.exe` |
| Kiểm thử hiện có | Python regression runner | 35 ca regression/UAT |

## 4. Cấu trúc thư mục

```text
Code_goi_y_huong_nghiep/
├── app_gui.py                         Entry point desktop
├── _runtime_hook.py                   Hook PyInstaller đặt working directory
├── qa_test_runner.py                  Regression/UAT runner
├── requirements.txt                   Phụ thuộc runtime
├── requirements-dev.txt               Phụ thuộc build/phát triển
├── apps/desktop/
│   ├── app.py                         UI, điều phối và tích hợp Gemini
│   ├── theme.py                       Theme, font, navigation metadata
│   └── assets/                        Logo, icon và font Roboto
├── huit_career_advisor/
│   ├── domain/
│   │   ├── advisory.py                Hồ sơ định hướng và xếp hạng phương thức
│   │   └── catalog.py                 Danh mục ngành, tổ hợp, nhóm ngành
│   ├── inference/
│   │   ├── dgnl.py                    Inference ĐGNL
│   │   ├── academic_record.py         Inference học bạ
│   │   ├── direct_admission.py        Inference tuyển thẳng
│   │   └── thpt.py                    Inference THPT
│   └── paths.py                       Đường dẫn source/PyInstaller
├── data/DXDuong.xlsx                  Dữ liệu nghiên cứu và huấn luyện
├── models/*.pkl                       Model, encoder, mapping và metadata
├── research/
│   ├── training/                      Script huấn luyện bốn nhóm model
│   └── evaluation/                    Script và kết quả đánh giá
├── scripts/                           Wrapper tương thích và tiện ích font
├── tools/                             Tiện ích chuyển icon
├── installer/
│   ├── huit_app.spec                  Cấu hình PyInstaller
│   ├── build_app.ps1                  Script build Windows
│   └── huit_installer.iss             Cấu hình Inno Setup
└── docs/tailieu/                      Bộ tài liệu bàn giao này
```

## 5. Chạy nhanh từ source

```powershell
cd D:\ADuong_HUIT\Code_goi_y_huong_nghiep
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\app_gui.py
```

Xem hướng dẫn đầy đủ tại [INSTALL.md](INSTALL.md).

## 6. Kiểm tra chất lượng hiện tại

Tại thời điểm lập tài liệu:

- `compileall`: đạt.
- `qa_test_runner.py`: `35 PASS / 0 FAIL`.
- Smoke test tạo cửa sổ: **không đạt** do `profile_interest_display` chưa được khởi tạo trước khi dựng trang Tổng quan. Nguyên nhân thể hiện trực tiếp trong `apps/desktop/app.py`: phần khởi tạo các biến hiển thị hồ sơ đang nằm trong `_update_api_key()` thay vì `_init_advisory_profile()`.

Vì lỗi smoke test, trạng thái hiện tại chưa đủ điều kiện bàn giao bản chạy production dù các bài kiểm thử inference đều đạt.

## 7. Chỉ mục tài liệu

- [ARCHITECTURE.md](ARCHITECTURE.md): kiến trúc, thành phần và luồng xử lý.
- [FEATURES.md](FEATURES.md): chức năng theo module.
- [DATABASE.md](DATABASE.md): dữ liệu Excel, model, settings và quan hệ logic.
- [INSTALL.md](INSTALL.md): cài đặt, cấu hình, kiểm thử và đóng gói.

## 8. Lưu ý bảo mật

- Không commit Gemini API key vào Git, tài liệu hoặc mã nguồn.
- API key trên Windows được source lưu vào Credential Manager với target `HUIT_Career_Advisor_Gemini_Key`.
- Dữ liệu điểm, sở thích, họ tên và câu hỏi chỉ được gửi tới Gemini sau khi người dùng đồng ý trong ứng dụng.
- File `DXDuong.xlsx` có các cột mã hồ sơ/SBD; cần quản lý như dữ liệu nghiên cứu có khả năng chứa thông tin nhạy cảm.

