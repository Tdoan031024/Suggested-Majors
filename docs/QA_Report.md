# Báo cáo QA – HUIT Career Advisor AI
**Phiên bản:** Desktop v2.0 (Tkinter)  
**Ngày kiểm thử:** 19/06/2026  
**Người kiểm thử:** Senior QA Tester (AI)  
**Phạm vi:** Toàn bộ ứng dụng – 71 test case tự động + kiểm tra thủ công code

---

## 1. Tổng quan chất lượng

| Hạng mục | Kết quả |
|---------|---------|
| **Tổng test case** | 71 |
| **PASS** | 61 (86%) |
| **FAIL** | 1 (1.4%) |
| **WARN (bugs tiềm ẩn)** | 9 |
| **Model DGNL accuracy** | 89.0% |
| **Model HocBa accuracy** | RF=16.3% / NB=4.3% |
| **Crash/Exception** | 0 |
| **Đánh giá UX/UI** | **6.2 / 10** |

> [!IMPORTANT]
> Model Học bạ có accuracy **RF=16.3% / NB=4.3%** – rất thấp so với chuẩn production. Kết quả gợi ý ngành từ phương thức này **không đáng tin cậy** và cần huấn luyện lại.

---

## 2. Danh sách lỗi tìm thấy

### 🔴 CRITICAL

#### BUG-C1: DGNL score=599 không bị chặn ở tầng inference
- **ID:** DG-01
- **Mức độ:** Critical
- **Mô tả:** Hàm `goi_y_nganh_simple()` chỉ validate `0 <= diem <= 1200`. Điểm 599 (dưới sàn 600) vẫn **trả về kết quả ngành** thay vì trả về lỗi.
- **Bước tái hiện:**
  1. Gọi `goi_y_nganh_simple(599)`
  2. Hàm trả về: `[{'ma_nganh': '7850101', 'ten_nganh': 'Quản lý tài nguyên...', 'xac_suat': 28.0}]`
- **Kết quả mong đợi:** Trả về lỗi `"Điểm DGNL không hợp lệ"` hoặc danh sách rỗng (vì dưới sàn 600)
- **Kết quả thực tế:** Trả về danh sách ngành bình thường
- **Gợi ý sửa:** Đổi validation từ `0 <= diem <= 1200` thành `600 <= diem <= 1200` trong `dgnl.py` line 39:
  ```python
  # Hiện tại (sai):
  if not (0 <= diem_dgnl <= 1200):
  # Sửa thành:
  if not (600 <= diem_dgnl <= 1200):
  ```
  Lưu ý: UI trong `app.py` đã validate đúng (`600 <= diem <= 1200`), nhưng tầng inference chưa đồng bộ.

---

### 🟠 HIGH

#### BUG-H1: HocBa model accuracy quá thấp (RF=16.3%, NB=4.3%)
- **ID:** ML-05 / HB-08
- **Mức độ:** High
- **Mô tả:** Model `hocba_models.pkl` có accuracy chỉ 16.3% (RF) và 4.3% (NB). Kết quả gợi ý ngành từ phương thức Học bạ không đáng tin cậy. Xác suất top ngành chỉ đạt 8.8% thay vì mức kỳ vọng >50%.
- **Bước tái hiện:** Nhập điểm học bạ hợp lệ → Bấm "Phân tích học bạ" → Xem kết quả xác suất
- **Kết quả mong đợi:** Xác suất top ngành > 50%
- **Kết quả thực tế:** Xác suất cao nhất chỉ ~8.8-9%
- **Gợi ý sửa:** Huấn luyện lại `hocba_models.pkl` với dữ liệu đầy đủ hơn

#### BUG-H2: HocBa boost logic sai khi không chọn nhóm ngành
- **ID:** BUG-04
- **Mức độ:** High
- **Mô tả:** Trong `academic_record.py`, khi `nguyen_vong=''` (chuỗi rỗng), code áp dụng nhánh `if nguyen_vong:` → False, nhưng **toàn bộ ngành vẫn bị phạt `boost *= 0.6`** vì code kiểm tra `if preferred: boost *= 1.8 else: boost *= 0.6` không phân biệt "không chọn" vs "chọn nhưng không thuộc".
- **Kết quả thực tế:** `no_group top1: CNTT 8.3%` vs `cntt_group top1: CNTT 32.3%` – chênh lệch gần 4x
- **Gợi ý sửa:** Trong `academic_record.py` line 154-167:
  ```python
  # Hiện tại (sai):
  if preferred:
      boost *= 1.8
  else:
      boost *= 0.6  # <- sai khi nguyen_vong=''

  # Sửa thành:
  if nguyen_vong:   # chỉ boost/penalize khi người dùng có chọn nhóm
      if preferred:
          boost *= 1.8
      else:
          boost *= 0.6
  # không chọn nhóm -> boost = 1.0 (neutral)
  ```

---

### 🟡 MEDIUM

#### BUG-M1: THPT Priority – sai hệ số chia (dùng 7 thay vì 7.5)
- **ID:** BUG-01
- **Mức độ:** Medium
- **Mô tả:** `calculate_priority_pt1()` dùng hệ số `7` trong công thức giảm tuyến tính, nhưng theo quy chế Bộ GD&ĐT 2023 chuẩn là `7.5`.
- **Kết quả thực tế:** score=25, KV1+Group1 → `1.96` (với /7), trong khi đúng phải là `1.83` (với /7.5)
- **Gợi ý sửa:** Trong `thpt.py` line 96: đổi `/ 7` thành `/ 7.5`

#### BUG-M2: THPT Priority – boundary condition sai (< vs <=)
- **ID:** BUG-02  
- **Mức độ:** Medium
- **Mô tả:** Code dùng `if tong < 22.5:` khiến điểm 22.5 rơi vào nhánh giảm dần và trả về `2.95` thay vì `2.75`.
- **Kết quả thực tế:** score=22.5, KV1+Group1 → `2.95` (sai, phải là `2.75`)
- **Gợi ý sửa:** Trong `thpt.py` line 92: đổi `< 22.5` thành `<= 22.5`

#### BUG-M3: TuyenThang – không validate điểm âm và điểm = 0
- **ID:** TT-03, TT-05
- **Mức độ:** Medium
- **Mô tả:** `goi_y_nganh_tuyen_thang_simple()` không có guard cho `tb_tong <= 0` hoặc âm. Cả hai đều trả 10 kết quả, khiến người dùng có thể nhập điểm vô lý và nhận được gợi ý sai.
- **Ghi chú:** UI `_run_tuyenthang()` có check `if tb30 <= 0: raise ValueError` → bắt được. Nhưng nếu gọi trực tiếp inference thì không an toàn.
- **Gợi ý sửa:** Thêm guard trong `direct_admission.py`:
  ```python
  if tb_tong <= 0 or tb_tong > 30:
      return [{'ma_nganh': None, 'ten_nganh': 'Điểm không hợp lệ', 'xac_suat': 0}]
  ```

#### BUG-M4: HocBa model không validate điểm > 10
- **ID:** HB-10
- **Mức độ:** Medium
- **Mô tả:** Tầng inference HocBa không chặn điểm > 10. Nhập 11/môn vẫn trả 5 kết quả bình thường.
- **Ghi chú:** UI đã có guard `if not all(0 <= x <= 10 ...)`. Nhưng tầng model thiếu bảo vệ.

---

### 🟢 LOW

#### BUG-L1: DGNL score=600 (điểm sàn) không hiển thị cảnh báo
- **ID:** BUG-03
- **Mức độ:** Low  
- **Mô tả:** Điểm 600 là mức sàn tối thiểu, nhưng app không hiển thị cảnh báo "điểm đang ở mức sàn" – chỉ trả kết quả bình thường. UX nên thông báo cho học sinh biết họ đang ở ngưỡng cận dưới.

#### BUG-L2: THPT Priority không validate điểm âm
- **ID:** PT-06
- **Mức độ:** Low
- **Mô tả:** `calculate_priority_pt1(-5, 'KV1', 'Nhóm 1')` trả về `2.75` thay vì lỗi. Điểm âm vô nghĩa về mặt nghiệp vụ.

#### BUG-L3: HocBa max priority cap không hoạt động đúng
- **ID:** HB-02
- **Mức độ:** Low
- **Mô tả:** `get_priority_points(khu_vuc, doi_tuong, diem_khuyen_khich=2.0)` cap tại 3.0, nhưng tham số `diem_khuyen_khich` không được cộng vào tổng (chỉ là placeholder trong hàm hiện tại).

---

## 3. Kiểm tra thủ công giao diện (Static Analysis)

### Phát hiện từ đọc code app.py

| Vấn đề | Vị trí | Mức độ |
|--------|--------|--------|
| Sidebar dark navy luôn hiện ngay cả khi Light mode | `theme.py` | Low |
| Clock pill dùng `surface_alt` không update khi toggle theme | `_build_header()` | Low |
| `_build_statusbar()` không update `status_dot` khi theme thay đổi | `_build_statusbar()` | Low |
| Profile chip khi chọn dùng `C['accent']` bg nhưng hover check sau lại bị ghi đè | `_hover_profile_chip()` | Low |
| ResultTable rowheight=40 ổn, nhưng khi text dài bị cắt không hiển thị tooltip | `ResultTable` | Low |
| Khi nhập điểm DGNL theo thành phần, không có real-time sum preview | `_build_page_dgnl()` | Medium |
| THPT QG: khi chưa chọn nhóm ngành, tổ hợp dropdown trống nhưng nút Phân tích không disabled | `_build_page_pt1()` | Medium |
| TuyenThang: không hiển thị điều kiện tuyển thẳng (GPA >=8.0, giải thưởng) để người dùng tự đánh giá | `_build_page_tuyenthang()` | Medium |
| Chat page: Không có timeout/loading indicator khi AI xử lý | `_build_page_chat()` | Medium |
| Dark mode: sidebar toggle hover dùng `sidebar_hover` nhưng khi light mode có thể không đủ contrast | `_draw_sidebar_toggle()` | Low |

---

## 4. Danh sách test case đã chạy

| ID | Mô tả | Trạng thái |
|----|-------|-----------|
| ML-01 | DGNL module loads | PASS |
| ML-02 | DGNL models loaded | PASS |
| ML-03 | THPT module loads | PASS |
| ML-04 | HocBa module loads | PASS |
| ML-05 | HocBa models loaded | PASS |
| ML-06 | TuyenThang module loads | PASS |
| ML-07 | Advisory domain loads | PASS |
| DG-01 | DGNL score=599 trả lỗi | **FAIL** |
| DG-02 | DGNL score=600 trả kết quả | PASS |
| DG-02b | DGNL xac_suat trong [0,100] | PASS |
| DG-03 | DGNL score=850 trả ≥1 kết quả | PASS |
| DG-03b | DGNL top xac_suat > 5% | PASS |
| DG-04 | DGNL score=1200 trả kết quả | PASS |
| DG-05 | DGNL score=-1 trả lỗi | PASS |
| DG-06 | DGNL score=1201 trả lỗi | PASS |
| DG-07 | DGNL với nhóm ngành ưu tiên đúng | PASS |
| DG-08 | DGNL tính ổn định (determinism) | PASS |
| PT-01 | THPT priority score=20 KV1+Nhom1 = 2.75 | PASS |
| PT-02 | THPT priority score=20 KV3 = 0.0 | PASS |
| PT-03 | THPT priority boundary 22.5 | WARN |
| PT-04 | THPT priority score=30 = 0.0 | PASS |
| PT-05 | THPT priority formula đúng | PASS |
| PT-06 | THPT priority không guard âm | WARN |
| TH-01 | THPT inference input hợp lệ | PASS |
| TH-01b | THPT xac_suat trong [0,100] | PASS |
| TH-02 | THPT all-zero không crash | PASS |
| TH-03 | THPT D01+Luật trả kết quả | PASS |
| TH-03b | THPT có trường to_hop_phu_hop | PASS |
| HB-01 | HocBa priority KV1+Nhom1 = 2.75 | PASS |
| HB-02 | HocBa priority cap <= 3.0 | PASS |
| HB-03 | HocBa priority KV3 = 0.0 | PASS |
| HB-04 | HocBa tinh_diem trả dict | PASS |
| HB-05 | HocBa diem_hb = tổng 3 môn TB | PASS |
| HB-06 | HocBa invalid to_hop trả None | PASS |
| HB-07 | HocBa predict trả ≥1 kết quả | PASS |
| HB-08 | HocBa xac_suat trong [5,90] | PASS |
| HB-09 | HocBa điểm 0 không crash | PASS |
| HB-10 | HocBa điểm >10 không bị chặn ở model | WARN |
| TT-01 | TuyenThang tb=27 trả kết quả | PASS |
| TT-02 | TuyenThang với nhóm trả kết quả | PASS |
| TT-02b | TuyenThang xac_suat trong [0,100] | PASS |
| TT-03 | TuyenThang tb=0 không guarded | WARN |
| TT-04 | TuyenThang tb=30 trả kết quả | PASS |
| TT-05 | TuyenThang âm không guarded | WARN |
| AD-01 | rank_admission_methods đầy đủ | PASS |
| AD-02 | rank_admission_methods có rank | PASS |
| AD-03 | Đúng 1 phương thức recommended | PASS |
| AD-04 | Thứ tự rank tăng dần | PASS |
| AD-05 | Empty scores trả [] | PASS |
| AD-06 | 1 phương thức → rank=1 | PASS |
| AD-07 | DGNL=600 → score=0% | PASS |
| AD-08 | DGNL=1200 → score=100% | PASS |
| AD-09 | enrich thêm diem_ho_tro | PASS |
| AD-10 | enrich thêm xac_suat_goc | PASS |
| IV-01~12 | Validate input (12 test) | PASS (all 12) |
| BUG-01 | Phát hiện hệ số /7 thay vì /7.5 | WARN |
| BUG-02 | Phát hiện boundary < vs <= | WARN |
| BUG-03 | DGNL=600 không cảnh báo sàn | WARN |
| BUG-04 | HocBa penalize khi nguyen_vong='' | WARN |

---

## 5. Chức năng đã PASS

- ✅ Load toàn bộ module và model thành công
- ✅ DGNL validate đúng input hợp lệ/không hợp lệ
- ✅ DGNL tính ổn định (determinism) – cùng input = cùng output
- ✅ DGNL có boost nhóm ngành ưa thích hoạt động đúng
- ✅ THPT priority tính đúng khi score < 22.5
- ✅ THPT priority = 0 khi score = 30
- ✅ THPT inference trả đúng cấu trúc kết quả
- ✅ HocBa tính điểm ưu tiên đúng
- ✅ HocBa tính diem_hb theo công thức tổng 3 môn TB (thang 30)
- ✅ HocBa predict_nganh không crash với đầu vào hợp lệ
- ✅ Advisory domain rank_admission_methods hoạt động đúng logic
- ✅ Advisory domain luôn có đúng 1 recommended=True
- ✅ enrich_major_results thêm đầy đủ metadata
- ✅ Tất cả 12 test input validation trong UI đều PASS
- ✅ Không có crash/exception khi chạy app (exit code 0)

---

## 6. Chức năng cần cải thiện

### Ưu tiên cao
1. **Retrain HocBa model** – accuracy 16.3% không đạt yêu cầu production
2. **Sửa DGNL validation** – cho phép điểm 0-599 không hợp lý
3. **Sửa HocBa boost logic** – penalty sai khi nguyen_vong=""

### Ưu tiên trung bình
4. **THPT QG**: Sửa hệ số 7 → 7.5 và boundary < → <=
5. **UX**: Thêm real-time sum preview cho DGNL nhập thành phần
6. **UX**: Disable nút "Phân tích" khi chưa chọn đủ nhóm + tổ hợp (THPT QG)
7. **UX**: TuyenThang page thiếu hiển thị điều kiện đủ điều kiện tuyển thẳng
8. **Guard**: Thêm validation điểm âm ở tầng inference (TuyenThang, THPT)

### Ưu tiên thấp
9. Chat page: thêm loading spinner khi AI đang xử lý
10. Tooltip khi text ngành bị cắt trong ResultTable
11. StatusBar: update dot color khi có lỗi vs khi OK
12. Cảnh báo khi điểm DGNL = 600 (ngưỡng sàn)

---

## 7. Đánh giá UX/UI tổng thể

**Điểm: 6.2 / 10**

| Tiêu chí | Điểm | Ghi chú |
|---------|------|---------|
| Cấu trúc điều hướng | 7/10 | Sidebar rõ ràng, 6 trang hợp lý |
| Nhất quán giao diện | 6/10 | Một số card/spacing không đồng đều |
| Phản hồi người dùng | 5/10 | Thiếu loading state, thiếu success toast |
| Input validation | 7/10 | Validate tốt ở UI, yếu ở inference layer |
| Dễ hiểu & onboarding | 6/10 | Cần thêm hướng dẫn trên từng trang |
| Hiệu suất | 8/10 | Chuyển tab nhanh, không lag |
| Xử lý lỗi | 6/10 | messagebox.showwarning OK nhưng thiếu inline validation |
| Dark/Light mode | 6/10 | Tồn tại nhưng sidebar không nhất quán |

---

## 8. Thứ tự ưu tiên sửa lỗi

```
1. [CRITICAL] BUG-C1  - dgnl.py: validate 600 <= diem <= 1200 ở inference layer
2. [HIGH]     BUG-H1  - Huấn luyện lại hocba_models.pkl (accuracy quá thấp)
3. [HIGH]     BUG-H2  - academic_record.py: sửa logic boost khi nguyen_vong=""
4. [MEDIUM]   BUG-M1  - thpt.py: đổi /7 thành /7.5 trong priority formula
5. [MEDIUM]   BUG-M2  - thpt.py: đổi <22.5 thành <=22.5 (boundary)
6. [MEDIUM]   BUG-M3  - direct_admission.py: thêm guard tb_tong <= 0 hoặc > 30
7. [MEDIUM]   BUG-M4  - academic_record.py: thêm guard điểm > 10 ở inference
8. [UX]       THPT QG: disable nút phân tích khi chưa chọn tổ hợp
9. [UX]       DGNL thành phần: thêm real-time tổng điểm preview
10. [LOW]     dgnl.py: thêm warning khi điểm = 600 (sàn tối thiểu)
```

---

## 9. Phụ lục: Môi trường kiểm thử

- **OS:** Windows 10/11
- **Python:** 3.10
- **Tkinter:** stdlib
- **Scikit-learn / Joblib:** từ requirements.txt
- **Test method:** Automated (71 cases) + Static code analysis
- **Không test được:** UI rendering thực tế, dark/light mode visual, scroll behavior, window resize
