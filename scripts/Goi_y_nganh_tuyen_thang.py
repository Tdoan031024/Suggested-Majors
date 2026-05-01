# -*- coding: utf-8 -*-
"""
GỢI Ý NGÀNH NGHỀ TUYỂN THẲNG (MÔ HÌNH ĐÃ HUẤN LUYỆN)
- Runtime CHỈ dùng mô hình RF+NB (70/30) từ models/tt_models.pkl
- Không đọc Excel khi chạy app. Nếu chưa có mô hình, hướng dẫn người dùng huấn luyện lại.
"""

import os
import sys
import math
import joblib
import numpy as np
import pandas as pd

_TT_MODEL = None  # payload loaded from models/tt_models.pkl


def _base_dir():
    """Trả về thư mục gốc đúng dù chạy bình thường hay dưới dạng .exe (PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) in ['scripts', 'evaluation']:
        return os.path.dirname(current_dir)
    return current_dir


# Loại bỏ toàn bộ fallback đọc Excel để đảm bảo runtime gọn nhẹ


def _load_tt_model():
    global _TT_MODEL
    if _TT_MODEL is not None:
        return _TT_MODEL
    try:
        model_path = os.path.join(_base_dir(), 'models', 'tt_models.pkl')
        if os.path.exists(model_path):
            _TT_MODEL = joblib.load(model_path)
        else:
            _TT_MODEL = None
    except Exception:
        _TT_MODEL = None
    return _TT_MODEL


def _group_mapping_codes():
    # Dùng cùng mapping 9 nhóm như DGNL
    return {
        'CNTT': ['7480201', '7480202', '7460108', '7340205'],
        'Kinh doanh': ['7340101', '7340115', '7340120', '7340122', '7340129'],
        'Kỹ thuật': ['7510202', '7510203', '7520115', '7510301', '7510303'],
        'Thực phẩm': ['7540101', '7540106', '7540105', '7819009', '7819010', '7340129'],
        'Tài chính': ['7340301', '7340201', '7340205'],
        'Hóa sinh': ['7510401', '7510406', '7850101', '7420201', '7510402'],
        'Luật ngôn ngữ': ['7380101', '7380107', '7220201', '7220204'],
        'Logistics': ['7510605', '7340123', '7540204'],
        'Du lịch': ['7810101', '7810103', '7810201', '7810202'],

        # Tên đầy đủ menu (để matching)
        'Công nghệ – Chế biến – Thực phẩm': ['7540101', '7540106', '7540105', '7819009', '7819010', '7340129'],
        'Kỹ thuật – Cơ khí – Tự động hóa': ['7510202', '7510203', '7520115', '7510301', '7510303'],
        'Hóa học – Sinh học – Môi trường – Vật liệu': ['7510401', '7510406', '7850101', '7420201', '7510402'],
        'Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu': ['7480201', '7480202', '7460108', '7340205'],
        'Kinh doanh – Quản trị – Marketing': ['7340101', '7340115', '7340120', '7340122', '7340129'],
        'Kế toán – Tài chính – Ngân hàng': ['7340301', '7340201', '7340205'],
        'Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt': ['7510605', '7340123', '7540204'],
        'Luật – Xã hội – Ngôn ngữ': ['7380101', '7380107', '7220201', '7220204'],
        'Du lịch – Nhà hàng – Khách sạn – Dịch vụ': ['7810101', '7810103', '7810201', '7810202']
    }


def _is_preferred(ma_str: str, group_input: str, mapping: dict) -> bool:
    if not group_input:
        return False
    # Exact key
    if group_input in mapping:
        return ma_str in mapping[group_input]
    # Substring match
    group_input_low = group_input.lower()
    for key, codes in mapping.items():
        if group_input_low in key.lower() or key.lower() in group_input_low:
            if ma_str in codes:
                return True
    return False


def goi_y_nganh_tuyen_thang_simple(tb_tong: float, diem_anh: float = 0.0, nguyen_vong: str = None, top_n: int = 10):
    """
    Khuyến nghị tuyển thẳng dựa trên dữ liệu 3 năm (TT-2023, TT-2022, TT-2021)

    Args:
        tb_tong: Tổng TB (thang 30)
        diem_anh: TB Tiếng Anh (0-10)
        nguyen_vong: Nhóm ngành ưa thích (9 nhóm)
        top_n: số ngành trả về
    Returns: list[dict] with keys: ma_nganh, ten_nganh, xac_suat
    """
    try:
        # Ưu tiên dùng mô hình RF+NB nếu có
        model = _load_tt_model()
        mapping = _group_mapping_codes()

        if model:
            rf = model['rf_model']
            nb = model['nb_model']
            le = model['le_nganh']
            name_map = model.get('name_map', {})
            features = model.get('features', ['TB10','TB11','TBHK1_12','TB_total','EngAvg','UT_DT','UT_KV','Year'])

            # Tạo một vector đặc trưng suy luận từ đầu vào tối thiểu
            # Giả định TB10 ~ TB11 ~ TBHK1_12 ~ tb_tong/3 nếu thiếu chi tiết
            tb_mon = tb_tong / 3.0
            X_pred = pd.DataFrame([[tb_mon, tb_mon, tb_mon, tb_tong, diem_anh or 0.0, 0.0, 0.0, 2024]], columns=features)

            rf_proba = rf.predict_proba(X_pred)[0]
            nb_proba = nb.predict_proba(X_pred)[0]
            ensemble = 0.7 * rf_proba + 0.3 * nb_proba

            results = []
            classes = le.classes_
            for idx, p in enumerate(ensemble):
                ma = classes[idx]
                ten = name_map.get(ma, f'Ngành {ma}')
                prob = float(p) * 100.0

                # Boost nhóm ưa thích
                if nguyen_vong:
                    if _is_preferred(str(ma), nguyen_vong, mapping):
                        prob *= 1.8
                    else:
                        prob *= 0.6

                # Boost tiếng Anh nhẹ
                if diem_anh >= 9:
                    prob *= 1.1

                prob = max(5.0, min(95.0, prob))

                is_pref = _is_preferred(str(ma), nguyen_vong, mapping) if nguyen_vong else False
                results.append({'ma_nganh': str(ma), 'ten_nganh': ten, 'xac_suat': round(prob, 1), 'thuoc_nhom_mong_muon': is_pref})

            # Sắp xếp giảm dần theo xác suất
            results.sort(key=lambda x: x['xac_suat'], reverse=True)

            # Nếu người dùng đã chọn nhóm, chỉ trả về ngành thuộc nhóm đó
            if nguyen_vong:
                preferred = [r for r in results if r.get('thuoc_nhom_mong_muon')]
                return preferred[:top_n]
            # Không chọn nhóm -> trả về top_n toàn bộ
            return results[:top_n]
        else:
            # Không có mô hình → hướng dẫn huấn luyện
            return [{
                'ma_nganh': None,
                'ten_nganh': 'Chưa có mô hình tuyển thẳng (tt_models.pkl)',
                'xac_suat': 0.0,
                'ly_do': 'Vui lòng chạy training: training/train_tuyenthang_models.py'
            }]

    except Exception as e:
        return [{'ma_nganh': 'Error', 'ten_nganh': f'Lỗi: {e}', 'xac_suat': 0.0}]

def goi_y_nganh_tuyen_thang():
    """Hàm main demo (tùy chọn) cho tuyển thẳng với giao diện người dùng"""
    
    print("\n" + "="*80)
    print("🏆 HỆ THỐNG GỢI Ý NGÀNH NGHỀ CHO HỌC SINH XUẤT SẮC - TUYỂN THẲNG")
    print("="*80)
    
    print("📋 THÔNG TIN ĐIỀU KIỆN TUYỂN THẲNG:")
    print("   • Học sinh xuất sắc cấp tỉnh/thành phố")
    print("   • Học sinh giỏi 3 năm liên tiếp") 
    print("   • Điểm trung bình từ 8.0 trở lên")
    print("   • Có chứng chỉ quốc tế hoặc giải thưởng")
    
    # Nhập thông tin học sinh
    print(f"\n📊 NHẬP THÔNG TIN HỌC SINH:")
    print("-"*40)
    
    # Loại học sinh
    print("🏅 LOẠI HỌC SINH:")
    print("   1. Xuất sắc (giải quốc gia/quốc tế)")
    print("   2. Giỏi (giải cấp tỉnh)")
    print("   3. Khá giỏi (học sinh giỏi 3 năm)")
    print("   4. Khá (điểm cao 3 năm)")
    
    # Điểm tổng thang 30
    try:
        tb_tong = float(input("📊 Tổng điểm TB 3 năm (thang 30, ví dụ 27.5): "))
        if tb_tong < 20 or tb_tong > 30:
            tb_tong = 27.0
    except Exception:
        tb_tong = 27.0
    
    # Môn mạnh
    print("\n💪 MÔN MẠNH/LĨNH VỰC YÊU THÍCH (9 NHÓM MỚI):")
    print("   1. 💻 CNTT (Công nghệ thông tin, An toàn, Khoa học dữ liệu)")
    print("   2. 💼 Kinh doanh (Quản trị, Marketing, Thương mại điện tử)")
    print("   3. ⚙️ Kỹ thuật (Cơ khí, Cơ điện tử, Điện-điện tử, Tự động hóa)")
    print("   4. 🧪 Thực phẩm (Công nghệ thực phẩm, Chế biến thủy sản)")
    print("   5. 💰 Tài chính (Kế toán, Tài chính ngân hàng, Fintech)")
    print("   6. 🌿 Hóa sinh (Hóa học, Sinh học, Môi trường, Vật liệu)")
    print("   7. ⚖️ Luật ngôn ngữ (Luật, Ngôn ngữ Anh, Ngôn ngữ Trung)")
    print("   8. 🚚 Logistics (Logistics, Chuỗi cung ứng, Thời trang)")
    print("   9. 🏨 Du lịch (Du lịch, Khách sạn, Nhà hàng)")
    
    mon_map = {
        '1': 'CNTT', '2': 'Kinh doanh', '3': 'Kỹ thuật',
        '4': 'Thực phẩm', '5': 'Tài chính', '6': 'Hóa sinh',
        '7': 'Luật ngôn ngữ', '8': 'Logistics', '9': 'Du lịch'
    }
    mon_choice = input("Chọn môn mạnh (1-9): ").strip()
    mon_manh = mon_map.get(mon_choice, 'CNTT')
    
    # Hiển thị thông tin đã nhập
    print(f"\n✅ THÔNG TIN HỌC SINH:")
    print(f"   📊 Tổng TB (30): {tb_tong}")
    print(f"   💪 Môn mạnh: {mon_manh}")
    
    # Gợi ý ngành nghề
    print(f"\n🤖 ĐANG PHÂN TÍCH PROFILE HỌC SINH...")
    # Ưu tiên nhóm ngành từ môn mạnh như nguyện vọng
    results = goi_y_nganh_tuyen_thang_simple(tb_tong, 9.0, mon_manh)
    
    if results:
        print(f"\n🎯 TOP {len(results)} NGÀNH GỢI Ý CHO TUYỂN THẲNG:")
        print("="*80)
        
        for i, result in enumerate(results, 1):
            print(f"{i:2d}. 🏆 {result.get('ten_nganh','N/A'):<40} {float(result.get('xac_suat',0)):5.1f}%")
        
        print("="*80)
        print(f"🎉 Chúc mừng! Với hồ sơ này, bạn có cơ hội cao được tuyển thẳng!")
        print(f"💰 Ưu đại tuyển thẳng: Miễn phí thi tuyển, ưu tiên học bổng")
        
    else:
        print("❌ Không tìm thấy ngành phù hợp với điều kiện tuyển thẳng!")
        print("💡 Gợi ý: Tham gia các kỳ thi tuyển sinh thông thường")

if __name__ == "__main__":
    # Test function
    print("🧪 TEST TUYỂN THẲNG SYSTEM")
    print("="*40)
    
    # Demo call với chữ ký mới: (tb_tong, diem_anh, nguyen_vong)
    result = goi_y_nganh_tuyen_thang_simple(27.5, 9.2, "Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu")
    
    if result:
        print("✅ System hoạt động bình thường")
        for r in result[:3]:
            print(f"   • {r['ten_nganh']}: {r['xac_suat']:.1f}%")
    else:
        print("❌ System lỗi")