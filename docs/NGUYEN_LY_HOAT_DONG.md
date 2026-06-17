# HỆ THỐNG GỢI Ý NGÀNH NGHỀ HUIT - NGUYÊN LÝ HOẠT ĐỘNG

## 📋 Tổng quan hệ thống

Hệ thống gợi ý ngành nghề HUIT sử dụng **Machine Learning** với 4 phương thức khác nhau, mỗi phương thức đều áp dụng mô hình **Random Forest (70%) + Naive Bayes (30%)**. Tất cả hoạt động theo nguyên lý: **Dữ liệu đầu vào** → **Tiền xử lý** → **Suy luận mô hình** → **Điều chỉnh theo quy tắc nghiệp vụ** → **Xếp hạng và đầu ra**.

---

## 🎯 1. PHƯƠNG THỨC DGNL (Đánh giá năng lực)

### 📊 Nguyên lý hoạt động

```
Điểm DGNL (600-1200) → Chuẩn hóa → Vector đặc trưng → RF+NB → Điều chỉnh theo nhóm ưa thích → Top ngành
```

### 🔧 Chi tiết từng bước

#### Bước 1: Thu thập đầu vào
- **Điểm DGNL**: 600-1200 (thang điểm mới)
- **Điểm ưu tiên**: KV (khu vực) + ĐT (đối tượng)
- **Nhóm ngành ưa thích**: 9 nhóm (tùy chọn)

#### Bước 2: Tiền xử lý dữ liệu
```python
# Chuẩn hóa điểm DGNL về [0,1]
diem_tong_norm = (diem_dgnl - 600) / (1200 - 600)
# ⚖️ Tại sao Machine Learning cần chuẩn hóa:
# Tránh bias: Nếu không chuẩn hóa, mô hình sẽ "nghiêng" về feature có giá trị lớn nhất (DGNL) và bỏ qua các feature nhỏ khác
# Cân bằng trọng số: Sau chuẩn hóa, tất cả features đều trong khoảng [0,1], giúp mô hình học được tầm quan trọng thực sự của từng yếu tố
# Hiệu suất mô hình: Random Forest và Naive Bayes hoạt động tốt hơn khi dữ liệu đồng nhất về thang đo

# Tạo vector đặc trưng cho từng ngành
feature_vector = [diem_tong_norm, thu_tu_nv, diem_kv, diem_dt, ty_le_chung, ma_nganh_encoded, year]
```

#### Bước 3: Suy luận mô hình
**Tại sao dùng Ensemble (RF + NB)?**
- **Random Forest**: Mạnh về xử lý features đa dạng, tránh overfitting
- **Naive Bayes**: Nhanh, ổn định với dữ liệu ít, xử lý tốt features categorical
- **Kết hợp 70/30**: Tận dụng ưu điểm của cả hai, độ chính xác cao hơn mô hình đơn lẻ

```python
# Ensemble prediction - Dự đoán xác suất trúng tuyển cho từng ngành
rf_prob = rf_model.predict_proba(feature_vector)[0][1]    # Class 1 (trúng tuyển)
nb_prob = nb_model.predict_proba(feature_vector)[0][1]    # Class 1 (trúng tuyển)

# Weighted ensemble: RF có trọng số cao hơn vì ổn định với data phức tạp
ensemble_prob = 0.7 * rf_prob + 0.3 * nb_prob  # [0,1] - Xác suất thô từ ML
base_prob = ensemble_prob * 100                 # [0,100] - Chuyển về %
```

#### Bước 4: Điều chỉnh theo quy tắc nghiệp vụ
**Tại sao cần điều chỉnh sau ML?**
- **ML thuần túy** chỉ dựa trên dữ liệu lịch sử → có thể thiếu sự ưu tiên cá nhân
- **Business rules** phản ánh sở thích thực tế của học sinh → kết quả personalized hơn
- **Cân bằng** giữa dự đoán khách quan (ML) và mong muốn chủ quan (người dùng)

```python
# Boost/Penalty theo nhóm ưa thích (Personal preference weighting)
if ngành thuộc nhóm ưa thích:
    xác_suất *= 1.8  # Boost +80%: Ưu tiên mạnh ngành yêu thích
else:
    xác_suất *= 0.6  # Penalty -40%: Hạ thấp ngành không quan tâm

# Safety clamp: Tránh xác suất quá cực đoan (0% hoặc 100%)
final_prob = max(5, min(90, xác_suất))  # Giữ trong [5%, 90%]
# - Min 5%: Luôn có hy vọng nhỏ, khuyến khích thử sức
# - Max 90%: Tránh tự mãn, vẫn cần chuẩn bị kỹ càng
```

#### Bước 5: Xếp hạng và đầu ra
- Sắp xếp theo xác suất giảm dần
- Trả về top N ngành kèm biểu tượng 🎯 cho ngành thuộc nhóm ưa thích

---

## 📚 2. PHƯƠNG THỨC HỌC BẠ (5 học kỳ THPT)

### 📊 Nguyên lý hoạt động

```
Chọn nhóm → Lọc tổ hợp → Nhập điểm 3 môn → Tính ĐHB → RF+NB → Boost nhóm+tổ hợp → Kết quả có cờ
```

### 🔧 Chi tiết từng bước

#### Bước 1: Lọc tổ hợp theo nhóm
```python
# Lấy tổ hợp khả dụng cho nhóm đã chọn
def allowed_tohops_for_group(group):
    majors = GROUP_MAPPING[group]
    allowed_tohops = set()
    for major_code in majors:
        allowed_tohops.update(NGANH_TO_HOP[major_code]['to_hop'])
    return allowed_tohops
```

#### Bước 2: Tính điểm học bạ theo công thức HUIT
```python
# Công thức chính thức HUIT
diem_hb = diem_tb_mon1 + diem_tb_mon2 + diem_tb_mon3  # Thang 30
diem_xet_tuyen = diem_hb + diem_uu_tien
```

#### Bước 3: Tạo vector đặc trưng
```python
features = [
    diem_tb_mon1,    # Điểm TB môn 1 (5 học kỳ)
    diem_tb_mon2,    # Điểm TB môn 2 (5 học kỳ)  
    diem_tb_mon3,    # Điểm TB môn 3 (5 học kỳ)
    diem_xet_tuyen,  # Điểm cuối (đã cộng ưu tiên)
    year             # Năm (2024)
]
```

#### Bước 4: Suy luận và điều chỉnh
```python
# Ensemble prediction
rf_proba = rf_model.predict_proba(X)[0]
nb_proba = nb_model.predict_proba(X)[0]
ensemble_proba = 0.7 * rf_proba + 0.3 * nb_proba

# Điều chỉnh theo nhóm ưa thích
if thuộc_nhóm_ưa_thích:
    prob *= 1.8
else:
    prob *= 0.6

# Điều chỉnh theo tổ hợp
if ngành_mở_tổ_hợp_đã_chọn:
    prob *= 1.15     # Boost nhẹ
    to_hop_phu_hop = True
else:
    prob *= 0.35     # Penalty mạnh
    to_hop_phu_hop = False
```

#### Bước 5: Ưu tiên hiển thị
```python
# Ưu tiên ngành có tổ hợp phù hợp
matching = [r for r in results if r['to_hop_phu_hop']]
non_matching = [r for r in results if not r['to_hop_phu_hop']]

if len(matching) >= top_n:
    return matching[:top_n]
else:
    return matching + non_matching[:needed]
```

#### Kết quả với cờ
- ✅ **Phù hợp tổ hợp**: Ngành mở đúng tổ hợp đã chọn
- ⚠️ **Không mở tổ hợp**: Ngành không mở tổ hợp này
- 🎯 **Thuộc nhóm**: Ngành thuộc nhóm mong muốn
- 📊 **Ngoài nhóm**: Ngành không thuộc nhóm đã chọn

---

## 🏆 3. PHƯƠNG THỨC TUYỂN THẲNG

### 📊 Nguyên lý hoạt động

```
Chọn nhóm → Nhập TB 3 năm + Tiếng Anh → RF+NB → Boost nhóm+Anh → Lọc chỉ nhóm đã chọn → Kết quả
```

### 🔧 Chi tiết từng bước

#### Bước 1: Thu thập đầu vào tối thiểu
- **Tổng TB 3 năm**: Thang 30
- **Điểm Tiếng Anh**: 0-10 (tùy chọn)
- **Nhóm ngành**: Bắt buộc chọn

#### Bước 2: Tạo vector đặc trưng từ thông tin hạn chế
```python
# Suy luận từ tổng TB
tb_mon = tb_tong / 3.0  # Giả định TB đều các môn

features = [
    tb_mon,        # TB10 (suy luận)
    tb_mon,        # TB11 (suy luận)  
    tb_mon,        # TBHK1_12 (suy luận)
    tb_tong,       # TB_total (thực tế)
    diem_anh,      # EngAvg
    0.0,           # UT_DT (mặc định)
    0.0,           # UT_KV (mặc định)
    2024           # Year
]
```

#### Bước 3: Suy luận và điều chỉnh
```python
# Ensemble prediction
ensemble = 0.7 * rf_proba + 0.3 * nb_proba

# Boost theo nhóm ưa thích
if thuộc_nhóm_đã_chọn:
    prob *= 1.8
else:
    prob *= 0.6

# Boost Tiếng Anh (nếu ≥ 9.0)
if diem_anh >= 9:
    prob *= 1.1
```

#### Bước 4: Lọc nghiêm ngặt theo nhóm
```python
# CHỈ trả về ngành thuộc nhóm đã chọn
if có_chọn_nhóm:
    group_codes = GROUP_MAPPING[nhóm_đã_chọn]
    results = [r for r in results if r['ma_nganh'] in group_codes]
```

#### Đặc điểm
- **Lọc nghiêm ngặt**: Chỉ hiển thị ngành thuộc nhóm đã chọn
- **Boost Tiếng Anh**: Ưu tiên nhẹ cho học sinh giỏi Anh
- **Dành cho học sinh xuất sắc**: Điểm TB cao (≥ 24/30)

---

## 📝 4. PHƯƠNG THỨC PT1 (THPT 2025)

### 📊 Nguyên lý hoạt động

```
Chọn nhóm → Lọc tổ hợp → Nhập 3 môn + ưu tiên + NV → RF+NB → Boost nhóm+tổ hợp+Anh → Lọc nhóm → Ưu tiên tổ hợp → Kết quả
```

### 🔧 Chi tiết từng bước

#### Bước 1: Lọc tổ hợp theo nhóm (như Học bạ)
```python
# Chỉ hiển thị tổ hợp thuộc ngành của nhóm đã chọn
tohop_set = allowed_tohops_for_group(group)
```

#### Bước 2: Thu thập thông tin đầy đủ
- **3 môn**: Điểm từng môn (0-10)
- **Điểm ưu tiên**: KV + ĐT (điểm cộng)
- **Thứ tự NV**: 1-5
- **Tổ hợp**: A00, A01, D01, B00, C00...

#### Bước 3: Tạo vector đặc trưng phong phú
```python
features = [
    mon1,                    # Điểm môn 1
    mon2,                    # Điểm môn 2
    mon3,                    # Điểm môn 3
    diem_ut,                 # Điểm ưu tiên
    thu_tu_nv,               # Thứ tự nguyện vọng
    tohop_encoded,           # Mã tổ hợp (encoded)
    year,                    # Năm (2024)
    mon1 + mon2 + mon3 + diem_ut  # Tổng điểm
]
```

#### Bước 4: Suy luận với nhiều lớp điều chỉnh
```python
# Ensemble prediction
ensemble = 0.7 * rf_proba + 0.3 * nb_proba

# Boost theo nhóm ưa thích
if thuộc_nhóm_đã_chọn:
    boost *= 1.8
else:
    boost *= 0.6

# Boost theo tổ hợp
if ngành_mở_tổ_hợp_đã_chọn:
    boost *= 1.15
    tohop_flag = True
else:
    boost *= 0.35
    tohop_flag = False

# Boost Tiếng Anh (nếu D01)
if tohop == 'D01':
    boost *= 1.10  # +10%
```

#### Bước 5: Lọc và ưu tiên kết quả
```python
# Chỉ giữ ngành thuộc nhóm đã chọn
if có_chọn_nhóm:
    results = [r for r in results if r['ma_nganh'] in group_codes]

# Ưu tiên ngành có tổ hợp phù hợp
matching = [r for r in results if r['to_hop_phu_hop']]
non_matching = [r for r in results if not r['to_hop_phu_hop']]
return matching + non_matching[:needed]
```

#### Kết quả với cờ kép
- ✅ **Phù hợp tổ hợp** | ⚠️ **Không mở tổ hợp**
- 🎯 **Thuộc nhóm** | 📊 **Ngoài nhóm**

---

## 🤖 Kiến trúc Machine Learning chung

### 📊 Mô hình Ensemble
```python
# Tất cả 4 phương thức đều dùng
final_prediction = 0.7 * RandomForest + 0.3 * NaiveBayes
```

### 🎯 9 nhóm ngành thống nhất
1. 🧪 **Công nghệ – Chế biến – Thực phẩm**
2. ⚙️ **Kỹ thuật – Cơ khí – Tự động hóa**  
3. 🌿 **Hóa học – Sinh học – Môi trường – Vật liệu**
4. 💻 **Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu**
5. 💼 **Kinh doanh – Quản trị – Marketing**
6. 💰 **Kế toán – Tài chính – Ngân hàng**
7. 🚚 **Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt**
8. ⚖️ **Luật – Xã hội – Ngôn ngữ**
9. 🏨 **Du lịch – Nhà hàng – Khách sạn – Dịch vụ**

### 🔧 Quy tắc boost/penalty chung
```python
# Nhóm ưa thích
preferred_boost = 1.8      # +80%
non_preferred_penalty = 0.6  # -40%

# Tổ hợp tương thích (HB, PT1)
tohop_boost = 1.15         # +15%
tohop_penalty = 0.35       # -65%

# Tiếng Anh (TT, PT1)
english_boost = 1.1        # +10%
```

### 🎯 Nguyên tắc xếp hạng
1. **Ưu tiên tổ hợp phù hợp** (nếu có)
2. **Sắp xếp theo xác suất** (cao → thấp)
3. **Backfill nếu thiếu** (đảm bảo đủ top N)
4. **Clamp an toàn** (5% ≤ xác suất ≤ 95%)

---

## 📁 Luồng dữ liệu hệ thống

```
[Dữ liệu thô]
     ↓
[Training Scripts] → [Models .pkl]
     ↓
[Runtime Inference] ← [User Input]
     ↓
[Post-processing] → [Business Rules]
     ↓
[Ranking & Filtering] → [Desktop GUI Output]
```

### 🔄 Runtime không phụ thuộc Excel
- **Training time**: Đọc `data/DXDuong.xlsx` → huấn luyện → lưu `models/*.pkl`
- **Runtime**: Chỉ load `.pkl` → suy luận nhanh
- **Benefit**: Tốc độ cao, không cần Excel khi triển khai

---

## 🎯 Tóm tắt điểm mạnh từng phương thức

| Phương thức | Đầu vào chính | Điểm mạnh | Phù hợp với |
|-------------|---------------|-----------|-------------|
| **DGNL** | Điểm DGNL (600-1200) | Đơn giản, nhanh | Học sinh có điểm DGNL |
| **Học bạ** | TB 5 học kỳ + nhóm + tổ hợp | Chi tiết, chính xác | Học sinh THPT muốn phân tích kỹ |
| **Tuyển thẳng** | TB 3 năm + nhóm | Đặc thù học sinh xuất sắc | HSG cấp tỉnh/quốc gia |
| **PT1** | 3 môn THPT + nhóm + tổ hợp | Toàn diện nhất | Thí sinh thi THPT 2025 |

---

*Tài liệu này mô tả nguyên lý hoạt động của hệ thống gợi ý ngành nghề HUIT. Để biết thêm chi tiết triển khai, xem mã nguồn trong các file .py tương ứng.*
