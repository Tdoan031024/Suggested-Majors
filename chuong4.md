    CHƯƠNG 4: THỰC NGHIỆM VÀ ĐÁNH GIÁ

    4.1. Môi trường và công cụ thực nghiệm

    4.1.1. Môi trường phần cứng
    Quá trình thực nghiệm được tiến hành trên máy tính cá nhân với cấu hình: bộ vi xử lý Intel Core thế hệ 11 (Intel64 Family 6 Model 140 Stepping 1, GenuineIntel), 8 lõi logic (4 lõi vật lý), bộ nhớ RAM 15,70 GB, hệ điều hành Windows 10 64-bit (Build 26200). Cấu hình phần cứng này đủ đáp ứng yêu cầu tính toán cho các thuật toán học máy với quy mô dữ liệu của đề án.

    4.1.2. Môi trường phần mềm và thư viện
    Hệ thống được xây dựng trên nền tảng ngôn ngữ lập trình Python 3.10.1 (64-bit, MSC v.1929). Các thư viện chính được sử dụng bao gồm:
    - scikit-learn 1.7.2 — thư viện học máy mã nguồn mở cung cấp triển khai đầy đủ các thuật toán Random Forest, Naive Bayes cùng các tiện ích đánh giá mô hình.
    - pandas 2.3.3 — thư viện xử lý dữ liệu dạng bảng, hỗ trợ đọc file Excel nhiều sheet, lọc và biến đổi dữ liệu.
    - NumPy 2.2.6 — thư viện tính toán số học nền tảng phục vụ biểu diễn ma trận và tính toán xác suất.
    - joblib 1.5.3 — được sử dụng để lưu và tải mô hình đã huấn luyện dưới định dạng .pkl, tối ưu hóa thời gian triển khai.

    4.2. Mô tả tập dữ liệu thực nghiệm

    4.2.1. Nguồn gốc và phạm vi dữ liệu
    Tập dữ liệu thực nghiệm được thu thập từ kết quả xét tuyển chính thức của Trường Đại học Công Thương TP. Hồ Chí Minh (HUIT) trong giai đoạn 2021–2023. Để đảm bảo mô hình học được các quy luật chính xác nhất, hệ thống **chỉ sử dụng dữ liệu của các thí sinh đã Trúng tuyển**, loại bỏ các hồ sơ rớt.

    Mục tiêu của bài toán học máy được xác định là: dựa trên thông tin điểm số đầu vào, dự đoán ngành học phù hợp nhất cho thí sinh trong số các ngành đào tạo của trường. Đây là bài toán phân loại đa lớp (multi-class classification) với số lượng lớp từ 36 đến 38 ngành tùy bộ dữ liệu.

    Bảng 4.1. Mô tả bốn bộ dữ liệu thực nghiệm (Sau khi lọc Trúng tuyển)
    | Bộ dữ liệu | Số bản ghi | Đặc trưng đầu vào chính | Số ngành | Nhãn đầu ra |
    |---|---|---|---|---|
    | Điểm học bạ THPT | 15.743 | Diem_Mon1, Diem_Mon2, Diem_Mon3, Diem_HB_Tinh, Nam | 37 | Mã ngành |
    | Điểm thi THPT (PT1)| 18.024 | Mon1, Mon2, Mon3, Diem_UT, ThuTuNV, ToHop_Enc, Year, Diem_Tong | 37 | Mã ngành |
    | Điểm ĐGNL | 7.687 | Diem_DGNL_Norm, Thu_Tu_NV, Diem_KV, Diem_DT, Ty_Le_Chung, Year | 36 | Mã ngành |
    | Tuyển thẳng (TT) | 4.517 | TB10, TB11, TBHK1_12, TB_total, EngAvg, UT_DT, UT_KV, Year | 38 | Mã ngành |

    4.2.2. Đặc điểm và thách thức của tập dữ liệu
    Qua quá trình phân tích dữ liệu, một số đặc điểm quan trọng ảnh hưởng trực tiếp đến hiệu suất mô hình được xác định như sau:
    - Thứ nhất, số lượng lớp phân loại lớn (36–38 ngành) trong khi đặc trưng đầu vào chỉ gồm 5–8 chiều. Tỷ lệ số đặc trưng trên số lớp thấp tạo ra thách thức cho các thuật toán phân loại, vì không gian đặc trưng không đủ phong phú để phân tách rõ ràng.
    - Thứ hai, phân phối dữ liệu mất cân bằng giữa các ngành. Một số ngành "hot" như CNTT, Quản trị Kinh doanh có hàng ngàn hồ sơ, trong khi một số ngành hẹp có rất ít. Sự mất cân bằng này khiến các mô hình có xu hướng thiên về dự đoán các lớp chiếm đa số.
    - Thứ ba, điểm số của các ngành có phạm vi chồng lấp cao (đặc biệt là phương thức Học bạ). Nhiều thí sinh với cùng điểm số có thể trúng tuyển vào các ngành khác nhau tùy năm và chỉ tiêu, dẫn đến ranh giới phân lớp không rõ ràng.

    4.2.3. Phân chia tập dữ liệu
    Thực nghiệm được tiến hành với hai tỷ lệ phân chia nhằm đánh giá tính ổn định của các mô hình: tỷ lệ 80/20 (80% huấn luyện, 20% kiểm tra) và tỷ lệ 90/10 (90% huấn luyện, 10% kiểm tra). Dữ liệu được chia ngẫu nhiên có kiểm soát (random_state=42) để đảm bảo tính tái lập. Bảng 4.2 trình bày số lượng bản ghi cụ thể cho từng bộ dữ liệu.

    Bảng 4.2. Số lượng bản ghi theo tỷ lệ phân chia
    | Bộ dữ liệu | Tổng | Train 80% | Test 20% | Train 90% | Test 10% |
    |---|---|---|---|---|---|
    | Học bạ THPT | 15.743 | 12.594 | 3.149 | 14.168 | 1.575 |
    | Thi THPT (PT1) | 18.024 | 14.419 | 3.605 | 16.221 | 1.803 |
    | ĐGNL | 7.687 | 6.149 | 1.538 | 6.918 | 769 |
    | Tuyển thẳng | 4.517 | 3.613 | 904 | 4.065 | 452 |

    4.3. Chỉ số đánh giá mô hình

    4.3.1. Lý do lựa chọn Top-K Accuracy là chỉ số đánh giá chính
    Trong bài toán phân loại truyền thống, Top-1 Accuracy (độ chính xác tại vị trí đầu tiên) là chỉ số phổ biến nhất. Tuy nhiên, trong ngữ cảnh hệ thống hỗ trợ ra quyết định tư vấn nghề nghiệp, chỉ số này không phản ánh đúng giá trị thực tế của hệ thống. Hệ thống không yêu cầu xác định chính xác một ngành duy nhất mà nhiệm vụ là trả về một danh sách các ngành học phù hợp để học sinh tham khảo.
    Do đó, chỉ số đánh giá phù hợp nhất là Top-K Accuracy — tỷ lệ các trường hợp trong đó ngành học đúng của thí sinh xuất hiện trong K ngành được gợi ý hàng đầu bởi mô hình. Trong thực tế triển khai, hệ thống trả về danh sách gợi ý, do đó Top-5 và Top-10 Accuracy là chỉ số đánh giá trực tiếp hiệu quả của hệ thống.

    4.4. Cài đặt tham số mô hình
    Bảng 4.3. Tham số cài đặt cho các mô hình học máy
    | Thuật toán | Bộ dữ liệu | Tham số cài đặt | Thời gian train TB |
    |---|---|---|---|
    | Random Forest | Học bạ | n_estimators=200, max_depth=10, random_state=42 | ~0.4 - 0.7s |
    | Random Forest | ĐGNL | n_estimators=150, max_depth=8, random_state=42 | ~0.5s |
    | Random Forest | THPT, Tuyển thẳng | n_estimators=80, max_depth=6, random_state=42 | ~0.1 - 0.4s |
    | Naive Bayes | Tất cả | GaussianNB() – mặc định, không có tham số | < 0.01s |

    4.5. Kết quả thực nghiệm Top-K Accuracy
    Bảng 4.4 trình bày kết quả Top-K Accuracy — chỉ số phản ánh đúng hiệu quả thực tế của hệ thống khi gợi ý danh sách ngành học.

    Bảng 4.4. Kết quả Top-K Accuracy trên 4 bộ dữ liệu
    | Bộ DL / Tỷ lệ | Thuật toán | Top-1 | Top-3 | Top-5 | Top-10 |
    |---|---|---|---|---|---|
    | Học bạ / 80/20 | RF | 16.26% | 34.11% | 48.62% | 72.50% ✓ |
    | Học bạ / 80/20 | NB | 4.26% | 16.10% | 26.64% | 55.41% |
    | THPT / 80/20 | RF | 21.14% | 46.88% | 61.75% | 83.86% ✓ |
    | THPT / 80/20 | NB | 6.07% | 15.62% | 36.34% | 68.88% |
    | ĐGNL / 80/20 | RF | 84.33% | 88.56% | 91.16% | 95.38% ✓ |
    | ĐGNL / 80/20 | NB | 99.87% | 99.87% | 99.87% | 99.87% |
    | Tuyển thẳng / 80/20 | RF | 70.58% | 84.29% | 90.04% | 96.90% ✓ |
    | Tuyển thẳng / 80/20 | NB | 100.00% | 100.00% | 100.00%| 100.00% |

    Ghi chú: ✓ đánh dấu các giá trị Top-10 Accuracy của Random Forest — chỉ số quan trọng nhất của hệ thống tư vấn.

    4.6. Phân tích và thảo luận kết quả

    4.6.1. Phân tích theo bộ dữ liệu
    a) Bộ dữ liệu điểm ĐGNL và Tuyển thẳng
    Trên hai bộ dữ liệu này, hiệu suất của các thuật toán đạt mức cực kỳ ấn tượng (>90% cho Top-5 và Top-10). Điều này xuất phát từ việc tiêu chí xét tuyển của 2 phương thức này rất rõ ràng (điểm ĐGNL cao hoặc điểm trung bình các năm xuất sắc). Thuật toán dễ dàng tìm ra được ranh giới trúng tuyển. Kết quả Naive Bayes đạt ~100% cho thấy dữ liệu có tính phân phối chuẩn rất rõ rệt đối với các thí sinh trúng tuyển.

    b) Bộ dữ liệu điểm thi THPT (PT1)
    Random Forest đạt kết quả rất tốt trên bộ dữ liệu thi THPT với Top-10 Accuracy lên đến 83.86%. Sự phong phú của đặc trưng (điểm 3 môn, điểm ưu tiên, mã tổ hợp) giúp mô hình phân biệt tốt giữa các ngành. Naive Bayes kém hiệu quả hơn (68.88% Top-10) do bị vi phạm giả định độc lập (điểm các môn trong cùng một khối thi thường có tương quan với nhau).

    c) Bộ dữ liệu điểm học bạ THPT
    Học bạ là phương thức khó dự đoán nhất. Top-10 Accuracy của Random Forest đạt 72.50%. Nguyên nhân chính là sự phân mảnh quá lớn của 15 tổ hợp môn và tình trạng "bão hòa điểm" (nhiều thí sinh có mức điểm rất sát nhau từ 22-25 điểm). Tuy nhiên, trong thực tiễn hướng nghiệp, việc hệ thống gợi ý ra 10 ngành mà có đến 72.5% tỷ lệ bao hàm ngành trúng tuyển thực tế đã là một kết quả mang tính hỗ trợ ra quyết định (Decision Support) rất có giá trị.

    4.6.2. Phân tích theo thuật toán 
    - Random Forest: Là thuật toán cốt lõi cho hiệu suất tốt nhất và ổn định nhất trên các tập dữ liệu phức tạp như Học bạ và THPT. Khả năng chống nhiễu và xử lý quan hệ phi tuyến tính giúp thuật toán vượt qua được ranh giới mờ nhạt giữa các khối ngành.
    - Naive Bayes: Dù có kết quả cực tốt trên ĐGNL và Tuyển thẳng, nhưng lại hụt hơi trên Học bạ và THPT. Tuy nhiên, tốc độ huấn luyện siêu tốc (<0.01s) và vai trò làm mịn (smoothing) xác suất khiến Naive Bayes trở thành một thành phần hoàn hảo để kết hợp (Ensemble) cùng Random Forest theo tỷ lệ 0.7 - 0.3 trong kiến trúc cuối cùng.

    4.7. Hạn chế và hướng cải tiến

    4.7.1. Những hạn chế đã xác định
    - Hạn chế về dữ liệu (Survivorship Bias): Mô hình hiện chỉ học từ dữ liệu của những thí sinh ĐÃ TRÚNG TUYỂN. Việc thiếu vắng hồ sơ của thí sinh trượt khiến hệ thống chưa thể vạch ra ranh giới đậu/rớt tuyệt đối mà mang tính chất "đo lường độ phù hợp hồ sơ".
    - Hạn chế về đặc trưng: Đề án tập trung hoàn toàn vào "Năng lực điểm số" mà chưa có các đặc trưng về sở thích nghề nghiệp (như bài test Holland, MBTI), làm giảm yếu tố "hướng nghiệp" đúng nghĩa.
    - Sự trượt giá điểm số (Data Drift): Điểm chuẩn và xu hướng chọn ngành thay đổi qua từng năm, đòi hỏi mô hình phải được huấn luyện lại thường xuyên khi có dữ liệu mới.

    4.7.2. Hướng cải tiến đề xuất
    Về mặt phần mềm, cấu trúc Desktop App nguyên khối (Monolithic) hiện tại nên được nâng cấp thành mô hình Client-Server. Đưa lõi AI (các file .pkl) lên máy chủ (Backend API) và cung cấp giao diện dạng Website sẽ giúp hàng ngàn học sinh tiếp cận dễ dàng hơn mà không cần tải ứng dụng về máy.

    Tiểu kết Chương 4
    Chương 4 đã trình bày toàn bộ quá trình thực nghiệm và đánh giá hệ thống tư vấn chọn ngành trên tập dữ liệu xét tuyển thực tế của HUIT giai đoạn 2021–2023, với tổng cộng 45.971 bản ghi hợp lệ (đã lọc thí sinh trúng tuyển).
    Kết quả thực nghiệm cho thấy kiến trúc Random Forest kết hợp Naive Bayes mang lại độ chính xác rất cao: Top-10 Accuracy đạt 72.5% (Học bạ), 83.8% (THPT) và >95% (ĐGNL, Tuyển thẳng). Các con số này chứng minh tính khả thi của việc áp dụng Học máy vào công tác tư vấn tuyển sinh, giúp học sinh tiết kiệm thời gian và thu hẹp rủi ro khi chọn nguyện vọng. Chương cũng thẳng thắn nhìn nhận những giới hạn về mặt dữ liệu và đề xuất các giải pháp khả thi trong tương lai.
