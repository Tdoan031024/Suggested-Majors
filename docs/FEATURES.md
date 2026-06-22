# Danh mục chức năng hiện có

## 1. Giao diện chung

### 1.1 Điều hướng

Sidebar cung cấp bảy mục:

1. Tổng quan.
2. ĐGNL.
3. Học bạ.
4. Tuyển thẳng.
5. THPT QG.
6. Trợ lý AI.
7. Cài đặt.

Sidebar có thể thu gọn, có trạng thái hover/active và footer phiên bản `v2.0`. Status bar hiển thị phương thức/trạng thái đang xử lý.

### 1.2 Theme và hiển thị

- Light mode và dark mode.
- Phím tắt `Ctrl+Shift+T`.
- Lưu lựa chọn theme vào `settings.json`.
- Font Roboto đóng gói trong assets; fallback Segoe UI.
- Hỗ trợ Windows DPI awareness.
- Các trang dài sử dụng canvas cuộn và mouse wheel.

### 1.3 Thành phần dùng lại

- Card bo góc.
- Button vẽ bằng Canvas với hover, press và focus.
- Bảng kết quả ngành có trạng thái loading/empty.
- Bảng xếp hạng phương thức.
- Divider và trang cuộn.

## 2. Hồ sơ định hướng cá nhân

Hồ sơ `AdvisoryProfile` quản lý:

- Nhóm ngành yêu thích.
- Nền tảng nghề nghiệp gia đình.
- Khu vực địa lý.
- Đặc trưng kinh tế địa phương.
- Đặc điểm tính cách.
- Khả năng học xa nhà.

UI mở rộng thêm mục tiêu nghề nghiệp, phong cách học tập, môi trường làm việc và các trait dạng chip. Các lựa chọn hiển thị được đồng bộ về chín nhóm ngành chính thức để dùng trong domain layer.

Điểm hỗ trợ hồ sơ hiện có các luật:

- Cộng điểm nếu ngành cùng nhóm sở thích.
- Cộng điểm nếu cùng nhóm nghề gia đình.
- Cộng điểm theo kinh tế địa phương.
- Cộng điểm theo nhóm tính cách.
- Điều chỉnh nhỏ cho khả năng học/làm linh hoạt ở vùng xa.
- Giới hạn tổng điều chỉnh trong khoảng `-4` đến `12`.

## 3. Trang Tổng quan

### Đầu vào

- Điểm ĐGNL tổng.
- Ba điểm học bạ và tổ hợp.
- Ba điểm thi THPT và tổ hợp.
- Ba điểm trung bình dùng cho tuyển thẳng.
- Điểm tiếng Anh.
- Khu vực và đối tượng ưu tiên.
- Hồ sơ định hướng.

Người dùng chỉ cần nhập ít nhất một phương thức; các bộ ba điểm nếu đã nhập phải đủ cả ba và nằm trong `0–10`. ĐGNL phải nằm trong `600–1200`.

### Xử lý và đầu ra

- Chuẩn hóa mức sẵn sàng của từng phương thức.
- Đánh dấu đúng một phương thức được khuyên dùng khi có dữ liệu.
- Chạy các model tương ứng với dữ liệu đã nhập.
- Gộp kết quả trùng mã ngành.
- Hiển thị metric dashboard, insight, phương thức ưu tiên và tối đa 12 ngành.
- Nút xóa dữ liệu tổng quan.
- Xuất báo cáo hướng nghiệp HTML.

## 4. Gợi ý ngành theo ĐGNL

### Đầu vào

- Tổng điểm ĐGNL, thang `600–1200`.
- UI có cơ chế chuyển chế độ nhập và tính tổng từ các thành phần ĐGNL.
- Nhóm ngành mong muốn từ hồ sơ.

### Xử lý

- Chuẩn hóa điểm về `0–1`.
- Tạo sáu feature theo schema model.
- Ensemble RF/NB theo tỷ lệ `70/30`.
- Boost ngành cùng nhóm mong muốn, penalty ngành ngoài nhóm.
- Điều chỉnh theo điểm và ưu tiên; clamp điểm kết quả `5–95`.

### Đầu ra

- Mã ngành.
- Tên ngành.
- Điểm xếp hạng trong trường `xac_suat`.
- Cờ thuộc nhóm mong muốn.

## 5. Gợi ý ngành theo học bạ

### Đầu vào

- Tổ hợp xét tuyển.
- Ba điểm trung bình môn.
- Khu vực, đối tượng và điểm khuyến khích khi gọi nghiệp vụ tương ứng.
- Nhóm ngành mong muốn.

### Xử lý

- `tinh_diem_hoc_ba()` có thể tính điểm từ dữ liệu năm học/học kỳ theo từng môn.
- `get_priority_points()` ánh xạ điểm ưu tiên và giới hạn tổng cộng.
- Kiểm tra điểm môn `0–10`, tổng học bạ tối đa 30 và điểm xét tuyển tối đa 33.
- Ensemble RF/NB.
- Boost/penalty theo nhóm ngành và mức tương thích tổ hợp.

### Đầu ra

- Top-K ngành.
- Điểm xếp hạng.
- Cờ tổ hợp phù hợp.
- Cờ thuộc nhóm mong muốn.

## 6. Gợi ý ngành theo tuyển thẳng

### Đầu vào

- Điểm trung bình lớp 10, lớp 11 và HK1 lớp 12/tổng ba thành phần.
- Điểm tiếng Anh `0–10`.
- Nhóm ngành mong muốn.

### Xử lý

- Kiểm tra tổng điểm trong `(0, 30]` và điểm Anh trong `[0, 10]`.
- Suy ra các feature năm học từ tổng đầu vào theo logic inference hiện tại.
- Ensemble RF/NB.
- Điều chỉnh theo nhóm mong muốn và điểm tiếng Anh.

### Đầu ra

- Top-K mã/tên ngành và điểm xếp hạng.
- Thông tin thuộc nhóm mong muốn.

Module còn giữ một giao diện CLI lịch sử và hàm `demo()` để smoke test thủ công.

## 7. Gợi ý ngành theo điểm thi THPT

### Đầu vào

- Ba điểm môn, mỗi môn `0–10`.
- Mã tổ hợp.
- Khu vực và đối tượng ưu tiên.
- Thứ tự nguyện vọng.
- Nhóm ngành mong muốn.

### Xử lý

- Tính điểm ưu tiên theo công thức giảm dần từ ngưỡng tổng điểm 22,5.
- Encoder mã tổ hợp; fallback về A00 hoặc 0 nếu gặp tổ hợp chưa biết.
- Ensemble RF/NB.
- Boost theo nhóm ngành, tổ hợp phù hợp và D01.
- Ưu tiên kết quả có tổ hợp tương thích.

### Đầu ra

- Top-K ngành.
- Điểm xếp hạng.
- Cờ tổ hợp phù hợp.
- Cờ thuộc nhóm mong muốn.

## 8. Trợ lý AI

### 8.1 Hội thoại định hướng có cấu trúc

Chatbot dùng state cục bộ để lần lượt thu thập:

- Họ tên.
- Phương thức xét tuyển.
- Điểm dự kiến.
- Nhóm ngành quan tâm.

Sau đó chatbot gọi module ML phù hợp và tạo báo cáo tư vấn ngay trong khung chat.

### 8.2 Câu hỏi nhanh và trả lời offline

Có quick prompt và bộ rule theo từ khóa cho:

- Học phí.
- Tuyển thẳng.
- Ký túc xá/chỗ ở.
- Nhóm ngành.
- Địa chỉ trường.
- Website chính thức.

### 8.3 Gemini

- Dùng model alias `gemini-flash-latest`.
- Gửi request bất đồng bộ bằng daemon thread.
- Timeout 10 giây.
- Chỉ gọi sau khi có API key và consent.
- Tự động fallback offline khi lỗi.
- Prompt gửi kèm hồ sơ học sinh và thông tin HUIT hard-code trong source.

## 9. Cài đặt trong ứng dụng

- Nhập Gemini API key.
- Ẩn/hiện API key.
- Xóa API key.
- Hiển thị trạng thái consent.
- Đặt lại consent để ứng dụng hỏi lại.
- Chuyển light/dark mode.
- Trên Windows, lưu khóa vào Credential Manager.

## 10. Xuất báo cáo

- Sinh HTML có CSS nội tuyến.
- Gồm thông tin hồ sơ, điểm, bảng phương thức, top 12 ngành và lời khuyên.
- Escape các trường văn bản hồ sơ chính.
- Có nút in bằng `window.print()`.
- Ghi vào `Desktop\Bao_cao_Huong_nghiep_HUIT.html`.
- Tự động mở bằng trình duyệt mặc định.

## 11. Danh mục ngành và tổ hợp

`domain/catalog.py` quản lý:

- Mã/tên ngành HUIT.
- 15 mã tổ hợp: A00, A01, B00, B08, C00, C01, C02, C03, C14, D01, D07, D09, D14, D15 và X26.
- Chín nhóm ngành chính thức.
- Alias nhóm riêng cho ĐGNL, học bạ, THPT và tuyển thẳng.

## 12. Chức năng nghiên cứu ML

### Training

- ĐGNL: đọc các sheet DGNL 2021–2023, tạo feature và huấn luyện RF/NB.
- Học bạ: đọc HB 2021–2023, lọc bản ghi trúng tuyển, tính trung bình môn và huấn luyện RF/NB.
- THPT: đọc All-2022, All-2023, DT-2021; encode tổ hợp và huấn luyện RF/NB.
- Tuyển thẳng: đọc TT 2021–2023, impute median và huấn luyện RF/NB.

### Evaluation

- Accuracy train/test.
- Precision, recall và F1 macro.
- Classification report và confusion matrix.
- Top-1, Top-3, Top-5, Top-10.
- So sánh tỷ lệ train/test 80/20 và 90/10.

## 13. Kiểm thử và đóng gói

- `qa_test_runner.py`: module loading, validation biên, công thức ưu tiên, tính deterministic và sáu UAT flow.
- `huit_app.spec`: đóng gói app, model, assets và Excel theo dạng onedir.
- `build_app.ps1`: kiểm tra PyInstaller, dọn build cũ, build và kiểm tra executable.
- `huit_installer.iss`: tạo bộ cài v2.0, shortcut Start Menu/Desktop và uninstall.

## 14. Chức năng chưa tồn tại

Source không có đăng nhập, phân quyền, database CRUD, đồng bộ cloud, backend API riêng, frontend web, mobile app, auto-update hoặc telemetry.

