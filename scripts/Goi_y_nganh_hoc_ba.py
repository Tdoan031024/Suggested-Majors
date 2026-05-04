# -*- coding: utf-8 -*-
"""
HỆ THỐNG GỢI Ý NGÀNH HỌC THEO HỌC BẠ HUIT - PHIÊN BẢN HOÀN CHỈNH
Sử dụng công thức: ĐHB = (ĐHBM1 + ĐHBM2 + ĐHBM3)/3 + Điểm ưu tiên
Tích hợp Random Forest + Naive Bayes với dữ liệu thực tế 3 năm
"""

try:
    from scripts.hoc_ba_interface import goi_y_hoc_ba_main
    from scripts.hoc_ba_analyzer import HocBaAnalyzer
except ImportError:
    from hoc_ba_interface import goi_y_hoc_ba_main
    from hoc_ba_analyzer import HocBaAnalyzer

def goi_y_nganh_hoc_ba():
    """
    Hàm wrapper cho hệ thống gợi ý học bạ - tương thích với main.py
    """
    try:
        goi_y_hoc_ba_main()
    except Exception as e:
        print(f"❌ Lỗi hệ thống học bạ: {e}")
        print("🔄 Chuyển sang hệ thống dự phòng...")
        goi_y_hoc_ba_simple()

def goi_y_hoc_ba_simple():
    """Hệ thống học bạ đơn giản cho trường hợp dự phòng"""
    print("\n📚 HỆ THỐNG HỌC BẠ DỰ PHÒNG")
    print("="*50)
    
    # Nhập điểm đơn giản
    try:
        tb_10 = float(input("📊 Điểm TB lớp 10: "))
        tb_11 = float(input("📊 Điểm TB lớp 11: "))  
        tb_12 = float(input("📊 Điểm TB lớp 12: "))
        
        diem_tong = (tb_10 + tb_11 + tb_12) / 3
        
        print(f"\n✅ Điểm TB 3 năm: {diem_tong:.2f}")
        
        # Gợi ý cơ bản dựa trên điểm
        if diem_tong >= 8.5:
            print("🏆 Xuất sắc - Có thể chọn mọi ngành")
            nganh_goi_y = [
                "Công nghệ thông tin",
                "Kế toán", 
                "Quản trị kinh doanh",
                "Ngôn ngữ Anh"
            ]
        elif diem_tong >= 7.0:
            print("🥈 Khá - Cơ hội tốt với hầu hết ngành")
            nganh_goi_y = [
                "Marketing",
                "Du lịch",
                "Logistics",
                "Công nghệ thực phẩm"
            ]
        else:
            print("📈 Cần cải thiện - Chọn ngành phù hợp")
            nganh_goi_y = [
                "Quản trị dịch vụ du lịch",
                "Quản trị nhà hàng",
                "Công nghệ dệt may"
            ]
        
        print(f"\n🎯 GỢI Ý NGÀNH PHÙ HỢP:")
        for i, nganh in enumerate(nganh_goi_y, 1):
            print(f"{i}. {nganh}")
            
    except ValueError:
        print("❌ Lỗi nhập liệu!")

# Test function
def test_hoc_ba_system():
    """Test hệ thống học bạ hoàn chỉnh"""
    print("🧪 TEST HỆ THỐNG HỌC BẠ")
    print("="*50)
    
    analyzer = HocBaAnalyzer()
    
    # Test load data
    if analyzer.load_data():
        print("✅ Load data thành công")
    else:
        print("❌ Load data thất bại")
        return
    
    # Test train models
    if analyzer.train_models():
        print("✅ Train models thành công")
    else:
        print("❌ Train models thất bại")
        return
    
    print("🎯 Hệ thống học bạ hoạt động bình thường!")

if __name__ == "__main__":
    test_hoc_ba_system()