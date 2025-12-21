# HỆ THỐNG GỢI Ý HƯỚNG NGHIỆP HUIT

> Ứng dụng CLI gợi ý ngành học HUIT theo 4 phương thức (DGNL, Học bạ, Tuyển thẳng, PT1) sử dụng mô hình Machine Learning (Random Forest + Naive Bayes). Runtime chỉ dùng mô hình đã huấn luyện (.pkl), không đọc Excel.

## 📁 Cấu trúc dự án

```
├── main.py                         # 🚀 Ứng dụng CLI: menu 4 phương thức
├── Goi_y_nganh_nghe.py             # 📊 DGNL: inference bằng mô hình đã huấn luyện
├── Goi_y_nganh_hoc_ba.py           # 📚 Wrapper giao diện học bạ
├── hoc_ba_interface.py             # � Giao diện Học bạ: chọn nhóm → tổ hợp → nhập điểm
├── hoc_ba_analyzer.py              # 🤖 Engine Học bạ: tính điểm, load model, suy luận
├── Goi_y_nganh_tuyen_thang.py      # � Tuyển thẳng: inference model-only, lọc theo nhóm
├── Goi_y_nganh_thpt.py             # � PT1: inference; ưu tiên theo nhóm & tổ hợp
├── training/
│   ├── train_tuyenthang_models.py  # 🏗️ Huấn luyện mô hình Tuyển thẳng → models/tt_models.pkl
│   ├── train_thpt_models.py        # 🏗️ Huấn luyện mô hình PT1 → models/pt1_models.pkl
│   └── train_hocba_models.py       # 🏗️ Huấn luyện mô hình Học bạ → models/hocba_models.pkl
├── models/
│   ├── dgnl_models.pkl             # ✅ Mô hình DGNL đã huấn luyện
│   ├── tt_models.pkl               # ✅ Mô hình Tuyển thẳng đã huấn luyện
│   ├── pt1_models.pkl              # ✅ Mô hình PT1 đã huấn luyện
│   └── hocba_models.pkl            # ✅ Mô hình Học bạ đã huấn luyện
├── DXDuong.xlsx                    # 📑 Dữ liệu nguồn (chỉ dùng khi huấn luyện)
└── README.md                       # � Tài liệu này
```

## � Chạy ứng dụng

- Chạy bằng giao diện GUI (khuyến nghị):
  - Windows PowerShell: vào thư mục dự án và chạy: `python .\\app_gui.py`
  - Ứng dụng mở cửa sổ với 4 tab: DGNL, Học bạ, Tuyển thẳng, PT1.

- Chạy bằng CLI (tuỳ chọn):
  - Windows PowerShell: vào thư mục dự án và chạy: `python .\\main.py`
  - Chọn một trong 4 phương thức trên menu.

Lưu ý: Ứng dụng sẽ sử dụng các file mô hình trong `models/`. Nếu thiếu mô hình của một phương thức, dùng script trong `training/` để huấn luyện trước.

## 🎯 9 nhóm ngành (đồng bộ trên mọi phương thức)

1) 🧪 Công nghệ – Chế biến – Thực phẩm
    - Công nghệ thực phẩm; Đảm bảo chất lượng và an toàn thực phẩm; Công nghệ chế biến thủy sản; Khoa học dinh dưỡng và ẩm thực; Khoa học chế biến món ăn; Quản trị kinh doanh Thực phẩm (giao thoa với Nhóm 5)
2) ⚙️ Kỹ thuật – Cơ khí – Tự động hóa
    - Công nghệ chế tạo máy; Công nghệ kỹ thuật cơ điện tử; Kỹ thuật Nhiệt; Công nghệ kỹ thuật điện – điện tử; Công nghệ kỹ thuật điều khiển và tự động hóa
3) 🌿 Hóa học – Sinh học – Môi trường – Vật liệu
    - Công nghệ kỹ thuật Hóa học; Công nghệ kỹ thuật môi trường; Quản lý tài nguyên và môi trường; Công nghệ sinh học; Công nghệ vật liệu
4) 💻 Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu
    - Công nghệ thông tin; An toàn thông tin; Khoa học dữ liệu; Công nghệ Tài chính (Fintech) (giao thoa với Nhóm 6)
5) 💼 Kinh doanh – Quản trị – Marketing
    - Quản trị kinh doanh; Marketing; Thương mại điện tử; Kinh doanh quốc tế; Quản trị kinh doanh Thực phẩm (giao thoa với Nhóm 1)
6) 💰 Kế toán – Tài chính – Ngân hàng
    - Kế toán; Tài chính ngân hàng; Công nghệ Tài chính (Fintech) (giao thoa với Nhóm 4)
7) 🚚 Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt
    - Logistics và quản lý chuỗi cung ứng; Kinh doanh thời trang và dệt may; Công nghệ dệt, may
8) ⚖️ Luật – Xã hội – Ngôn ngữ
    - Luật; Luật kinh tế; Ngôn ngữ Anh; Ngôn ngữ Trung Quốc
9) 🏨 Du lịch – Nhà hàng – Khách sạn – Dịch vụ
    - Du lịch; Quản trị dịch vụ du lịch và lữ hành; Quản trị Nhà hàng và Dịch vụ ăn uống; Quản trị khách sạn

Các ngành “giao thoa” xuất hiện ở 2 nhóm sẽ được xử lý ưu tiên theo nhóm bạn chọn trong từng phương thức.

## 🤖 Mô hình & nguyên tắc chung

- Ensemble: 70% Random Forest + 30% Naive Bayes (trên vector đặc trưng phù hợp từng phương thức).
- Ưa thích nhóm (9 nhóm): boost x1.8 cho ngành thuộc nhóm; penalty x0.6 cho ngành ngoài nhóm khi người dùng đã chọn nhóm.
- Tổ hợp xét tuyển (nếu áp dụng):
  - Ngành có mở tổ hợp được chọn: x1.15 (ưu tiên nhẹ)
  - Ngành không mở tổ hợp đó: x0.35 (phạt mạnh) và ghi chú ⚠️
- English boost: nhẹ cho PT1 với D01 (+10%); Tuyển thẳng tăng nhẹ nếu Tiếng Anh ≥ 9.0.
- Kết quả được chuẩn hóa và clamp trong ngưỡng an toàn; xếp hạng ưu tiên ngành phù hợp tổ hợp trước, sau đó mới backfill nếu thiếu.

## 🧭 Cách gợi ý theo từng phương thức

### 1) DGNL – Đánh giá năng lực (`Goi_y_nganh_nghe.py`)
- Input: Tổng điểm DGNL (0–1200) hoặc chi tiết 4 thành phần (tùy UI) + (tùy chọn) nhóm ngành ưa thích.
- Xử lý: Tính đặc trưng; mô hình RF+NB suy luận xác suất ngành; áp dụng boost/penalty theo nhóm; clamp; sắp xếp giảm dần.
- Output: Danh sách ngành kèm xác suất; icon 🎯 cho ngành thuộc nhóm đã chọn.

### 2) Học bạ – 5 học kỳ THPT (`hoc_ba_interface.py` + `hoc_ba_analyzer.py`)
- Luồng nhập:
  1. Chọn nhóm ngành → lọc và chỉ hiển thị các tổ hợp thuộc nhóm → chọn tổ hợp.
  2. Nhập điểm (5 học kỳ hoặc nhập nhanh TB 3 năm từng môn).
  3. (Tùy chọn) Điểm ưu tiên KV/ĐT được cộng vào tổng (thang 30).
- Xử lý:
  - Tính ĐHB = ĐHBM1 + ĐHBM2 + ĐHBM3 (thang 30).
  - Tạo vector đặc trưng và suy luận với mô hình `models/hocba_models.pkl`.
  - Áp dụng boost/penalty nhóm (x1.8/x0.6) và tổ hợp (x1.15/x0.35).
  - Ưu tiên hiển thị ngành mở đúng tổ hợp trong Top N; chỉ backfill nếu thiếu.
- Output: Top ngành có icon:
  - ✅ phù hợp tổ hợp | ⚠️ không mở tổ hợp
  - 🎯 thuộc nhóm mong muốn | 📊 ngoài nhóm

### 3) Tuyển thẳng – Học sinh xuất sắc (`Goi_y_nganh_tuyen_thang.py`)
- Input: Tổng điểm TB 3 năm (thang 30), (tùy chọn) Tiếng Anh và nhóm ngành ưa thích.
- Xử lý:
  - Suy luận với mô hình `models/tt_models.pkl`.
  - Áp dụng boost/penalty nhóm (x1.8/x0.6); English boost nhẹ nếu Tiếng Anh ≥ 9.0.
  - Nếu đã chọn nhóm, kết quả CHỈ hiển thị các ngành thuộc nhóm đó.
- Output: Top ngành trong nhóm đã chọn, theo xác suất.

### 4) PT1 – Kết quả thi THPT 2025 (`Goi_y_nganh_thpt.py`)
- Luồng nhập:
  1. Chọn nhóm ngành → lọc tổ hợp theo nhóm → chọn tổ hợp.
  2. Nhập điểm theo 2 cách: tổng điểm 3 môn (nhanh) hoặc từng môn (chính xác).
  3. Nhập điểm ưu tiên (KV+ĐT) và thứ tự NV.
- Xử lý:
  - Tính đặc trưng: Mon1/2/3, Diem_UT, ThuTuNV, ToHop_Enc, Year, Diem_Tong.
  - Suy luận với mô hình `models/pt1_models.pkl`; boost/penalty nhóm + tổ hợp; English boost nếu D01.
  - Chỉ giữ ngành thuộc nhóm đã chọn; ưu tiên ngành mở đúng tổ hợp.
- Output: Top ngành với icon ✅/⚠️ (tổ hợp) và 🎯/📊 (nhóm).

## 🏗️ Huấn luyện mô hình (chỉ cần khi thiếu .pkl)

- Học bạ: `python .\training\train_hocba_models.py` → `models/hocba_models.pkl`
- PT1: `python .\training\train_thpt_models.py` → `models/pt1_models.pkl`
- Tuyển thẳng: `python .\training\train_tuyenthang_models.py` → `models/tt_models.pkl`

Sau khi có các file .pkl trong thư mục `models/`, ứng dụng chạy không cần đọc Excel.

## 🔧 Yêu cầu môi trường

- Python ≥ 3.8
- Thư viện: pandas, numpy, scikit-learn, joblib, openpyxl

## � Ghi chú

- Số liệu chính xác/độ đo thay đổi theo dữ liệu huấn luyện; các hệ số boost/penalty đã được chuẩn hóa trên 4 phương thức để đảm bảo trải nghiệm nhất quán.
- Dữ liệu nguồn (`DXDuong.xlsx`, thư mục `Data/`) chỉ cần cho huấn luyện; nên để trong `training/` khi triển khai.

---

🎉 Hệ thống đã sẵn sàng cho sinh viên HUIT trải nghiệm gợi ý ngành theo 4 phương thức!#   s u g g e s t e d - m a j o r s  
 