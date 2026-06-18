# Bàn giao kết quả kiểm thử - HUIT Career Advisor AI Desktop

**Ngày kiểm thử:** 19/06/2026  
**Vai trò:** Tester / QA Lead độc lập  
**Phạm vi:** Desktop app Tkinter, inference layer, advisory domain, model loading, regression/UAT smoke test  
**Kết luận ngắn:** Ứng dụng chạy ổn định ở các luồng chính; chưa nên công bố kết quả Học bạ như kết quả có độ tin cậy cao vì model Học bạ còn accuracy thấp.

---

## 1. Kế hoạch kiểm thử

### 1.1. Phạm vi kiểm thử

- Build/compile Python source.
- Load app desktop và xác minh các trang chính.
- Regression các lỗi đã sửa:
  - DGNL validate điểm dưới 600.
  - THPT priority dùng công thức `/7.5` và boundary `22.5`.
  - Tuyển thẳng chặn điểm âm, điểm 0, điểm vượt thang.
  - Học bạ chặn điểm vượt thang và không penalize sai khi không chọn nhóm ngành.
- UAT smoke theo vai trò học sinh:
  - Chỉ nhập ĐGNL.
  - Chỉ nhập Học bạ.
  - Chỉ nhập THPT QG.
  - Nhập đầy đủ hồ sơ.
  - Nhập dữ liệu sai.
- Side-effect test các module liên quan:
  - `huit_career_advisor.inference.*`
  - `huit_career_advisor.domain.advisory`
  - `apps.desktop.app`
- Kiểm tra metadata model Học bạ.

### 1.2. Ngoài phạm vi kiểm thử

- Không kiểm thử thủ công bằng mắt toàn bộ responsive/dark mode trên nhiều màn hình.
- Không kiểm thử installer `.exe`.
- Không kiểm thử độ chính xác nghiệp vụ như hội đồng tuyển sinh chính thức.
- Không huấn luyện lại model trong lượt bàn giao này.

---

## 2. Môi trường kiểm thử

- **Workspace:** `D:\ADuong_HUIT\Code_goi_y_huong_nghiep`
- **Python:** `.venv\Scripts\python.exe`
- **OS:** Windows
- **Entry point:** `app_gui.py`
- **Regression runner:** `qa_test_runner.py`
- **Model files:** `models/*.pkl`

### Trạng thái working tree tại thời điểm test

Repo đang có thay đổi chưa commit:

```text
M README.md
M apps/desktop/app.py
M apps/desktop/theme.py
M huit_career_advisor/inference/academic_record.py
M huit_career_advisor/inference/dgnl.py
M huit_career_advisor/inference/direct_admission.py
M huit_career_advisor/inference/thpt.py
M models/hocba_models.pkl
?? docs/QA_Report.md
?? qa_test_runner.py
```

---

## 3. Lệnh đã chạy

### 3.1. Compile source

```powershell
.\.venv\Scripts\python.exe -m compileall apps\desktop huit_career_advisor app_gui.py qa_test_runner.py
```

**Kết quả:** PASS

### 3.2. Regression/UAT runner

```powershell
.\.venv\Scripts\python.exe .\qa_test_runner.py
```

**Kết quả:** `35 PASS / 0 FAIL`

### 3.3. Smoke test khởi tạo app

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -c "from apps.desktop.app import App; app=App(); app.update(); print('APP_GEOMETRY', app.winfo_geometry()); print('PAGES', sorted(app._pages.keys())); app.destroy()"
```

**Kết quả:** PASS

```text
APP_GEOMETRY 1360x880+280+100
PAGES ['Học bạ', 'THPT QG', 'Trợ lý AI', 'Tuyển thẳng', 'Tổng quan', 'ĐGNL']
```

### 3.4. Edge-case suite bổ sung

Kiểm thử thêm trực tiếp qua inference/domain:

- DGNL: `599`, `600`, `1200`, `1201`, `abc`, `None`.
- THPT: điểm `0`, `10`, `11`, âm, null.
- Tuyển thẳng: `0`, âm, `30.1`, English `11`.
- Học bạ: điểm môn `11`, `diem_hb > 30`, `diem_xet_tuyen > 33`.
- Advisory ranking: dữ liệu rỗng, từng phương thức đơn lẻ, hồ sơ đầy đủ.

**Kết quả:** `39 PASS / 0 FAIL`

---

## 4. Kết quả theo nhóm kiểm thử

| Nhóm kiểm thử | Kết quả | Ghi chú |
|---|---:|---|
| Compile source | PASS | Không lỗi cú pháp |
| Module loading | PASS | DGNL, Học bạ, THPT, Tuyển thẳng, Advisory đều load được |
| App startup smoke | PASS | App tạo đủ 6 trang desktop |
| Regression lỗi cũ | PASS | Không thấy lỗi cũ tái xuất hiện |
| UAT luồng chính | PASS | 4 luồng chính trả kết quả |
| Data validation | PASS | Chặn dữ liệu âm, vượt thang, null ở các tầng chính |
| Priority formula | PASS | Boundary `22.5`, divisor `/7.5` đúng |
| Model metadata | PASS | Học bạ có metadata, nhưng accuracy thấp |

---

## 5. Regression Summary

### Đã xác minh fixed

- **DGNL score=599**: đã trả lỗi `Điểm DGNL không hợp lệ`.
- **DGNL score=600**: được chấp nhận là điểm sàn hợp lệ.
- **THPT priority boundary 22.5**: giữ đủ điểm ưu tiên.
- **THPT priority >22.5**: dùng công thức `/7.5`.
- **THPT priority âm hoặc >30**: trả `0.0`.
- **Tuyển thẳng score=0/âm/>30**: bị chặn.
- **Tuyển thẳng English >10**: bị chặn.
- **Học bạ điểm >10**: bị chặn ở model layer.
- **Học bạ empty interest group**: không còn bị penalize toàn cục kiểu cũ.
- **Hồ sơ đầy đủ**: xếp hạng được phương thức và chỉ có 1 phương thức recommended.

### Reopened Bugs

Không có.

---

## 6. UAT Summary

| Kịch bản | Kết quả | Nhận xét |
|---|---:|---|
| Chỉ nhập ĐGNL | PASS | Trả danh sách ngành |
| Chỉ nhập Học bạ | PASS | Trả danh sách ngành, nhưng cần xem là tham khảo do model yếu |
| Chỉ nhập THPT QG | PASS | Trả danh sách ngành |
| Nhập đầy đủ hồ sơ | PASS | Xếp hạng phương thức và ngành nổi bật |
| Nhập dữ liệu sai | PASS | Chặn dữ liệu không hợp lệ ở các tầng chính |

---

## 7. Logic Findings

### ĐGNL

- Validation hợp lệ: `600-1200`.
- Điểm dưới 600 và trên 1200 bị chặn.
- Kết quả deterministic với cùng input.

### THPT QG

- Công thức ưu tiên:
  - `<= 22.5`: giữ nguyên mức ưu tiên.
  - `> 22.5`: `[(30 - tổng điểm) / 7.5] x mức ưu tiên`.
  - `30`: ưu tiên về `0`.
- Điểm môn ngoài `0-10` bị chặn.

### Học bạ

- Điểm môn ngoài `0-10` bị chặn.
- `diem_hb > 30` hoặc `diem_xet_tuyen > 33` bị chặn.
- Có cảnh báo UI rằng kết quả Học bạ chỉ nên tham khảo.

### Tuyển thẳng

- Tổng điểm thang 30 hợp lệ.
- Điểm 0, âm, lớn hơn 30 bị chặn.
- Điểm Tiếng Anh ngoài `0-10` bị chặn.

### Advisory / AI hỗ trợ

- `rank_admission_methods({})` trả danh sách rỗng.
- Hồ sơ đầy đủ có đúng 1 phương thức recommended.
- `enrich_major_results` giữ xác suất trong khoảng `0-100`.

---

## 8. Rủi ro còn lại

### R1 - Model Học bạ accuracy thấp

Metadata hiện tại:

```text
RF accuracy: 16.26%
NB accuracy: 4.26%
Rows: 15,743
Created at: 2026-06-19T00:26:40
```

Đây là rủi ro lớn nhất về độ tin cậy kết quả. App đã có notice cảnh báo, nhưng nếu phát hành như sản phẩm tư vấn chính thức thì cần cải thiện model/dữ liệu.

### R2 - Chưa test visual thủ công đầy đủ

Smoke test xác nhận app khởi tạo được, nhưng chưa kiểm thử bằng mắt trên:

- Kích thước cửa sổ nhỏ.
- Fullscreen.
- Dark mode qua nhiều trang.
- Scroll dài trên màn hình thấp.

### R3 - PT5 không nằm trong scope desktop hiện tại

Desktop hiện hỗ trợ 4 phương thức chính. Nếu yêu cầu sản phẩm là bám đầy đủ tuyển sinh HUIT 2026 với 5 phương thức, cần quyết định lại scope.

---

## 9. Release Assessment

| Tiêu chí | Điểm | Ghi chú |
|---|---:|---|
| Chức năng chính | 8.5/10 | Luồng chính hoạt động |
| Validation dữ liệu | 9/10 | Các điểm âm/vượt thang đã chặn |
| Độ ổn định runtime | 8.5/10 | Compile/smoke/regression pass |
| UI/UX | 8/10 | Giao diện đã hiện đại hơn, cần visual pass cuối |
| Độ tin cậy kết quả | 6/10 | Bị kéo xuống bởi model Học bạ |
| Tài liệu vận hành | 8/10 | README đã có lệnh chạy/test |

**Final Score:** 82/100

**Release recommendation:** Có thể bàn giao demo/nội bộ. Chưa nên phát hành như công cụ tư vấn tuyển sinh chính thức nếu chưa cải thiện model Học bạ và hoàn tất visual QA thủ công.

---

## 10. Khuyến nghị tiếp theo

1. Cải thiện model Học bạ bằng feature tốt hơn hoặc cách đánh giá Top-K phù hợp.
2. Chạy visual QA thủ công trên Light/Dark mode.
3. Test resize desktop: 1024x768, 1366x768, 1920x1080.
4. Quyết định rõ scope PT5 ĐGNL chuyên biệt ĐHSP-HCM.
5. Thêm test automation cho UI state cơ bản nếu tiếp tục phát triển.
6. Thêm log file khi app gặp lỗi runtime.
7. Hiển thị giải thích ngắn cho từng ngành được gợi ý.
8. Thêm export kết quả tư vấn ra PDF/Excel.
9. Thêm version/build number trong app.
10. Đóng gói installer và test trên máy sạch.

---

## 11. Kết luận bàn giao

Phiên bản hiện tại đã vượt qua các bài kiểm thử tự động và smoke test ở tầng desktop/inference/domain:

```text
Compile: PASS
Regression/UAT: 35 PASS / 0 FAIL
Edge-case suite: 39 PASS / 0 FAIL
App startup smoke: PASS
```

Ứng dụng đủ điều kiện bàn giao cho demo, review nội bộ hoặc tiếp tục phát triển. Điểm cần xử lý trước production là độ tin cậy model Học bạ và visual QA thủ công trên nhiều kích thước màn hình.
