# -*- coding: utf-8 -*-
"""
HỆ THỐNG GỢI Ý NGÀNH NGHỀ DỰA TRÊN HỌC BẠ THPT
Sử dụng công thức HUIT: ĐHB = (ĐHBM1 + ĐHBM2 + ĐHBM3)/3 + Điểm ưu tiên
"""

import pandas as pd
import numpy as np
import os
import sys
import joblib
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

def _base_dir():
    """Trả về thư mục gốc đúng dù chạy bình thường hay dưới dạng .exe (PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) in ['scripts', 'evaluation']:
        return os.path.dirname(current_dir)
    return current_dir

# Mapping 37 ngành HUIT với tổ hợp môn xét tuyển 2025
NGANH_TO_HOP = {
    '7810103': {'ten_nganh': 'Quản trị dịch vụ du lịch và lữ hành', 'to_hop': ['D01', 'C03', 'D15', 'C00']},
    '7810201': {'ten_nganh': 'Quản trị khách sạn', 'to_hop': ['D01', 'C03', 'D15', 'C00']},
    '7810202': {'ten_nganh': 'Quản trị nhà hàng và dịch vụ ăn uống', 'to_hop': ['D01', 'C03', 'D15', 'C00']},
    '7380107': {'ten_nganh': 'Luật kinh tế', 'to_hop': ['D01', 'C03', 'C14', 'C00']},
    '7220201': {'ten_nganh': 'Ngôn ngữ Anh', 'to_hop': ['D01', 'A01', 'D09', 'D14']},
    '7220204': {'ten_nganh': 'Ngôn ngữ Trung Quốc', 'to_hop': ['D01', 'A01', 'D09', 'D14']},
    '7480201': {'ten_nganh': 'Công nghệ thông tin', 'to_hop': ['D01', 'A00', 'C01', 'X26']},
    '7480202': {'ten_nganh': 'An toàn thông tin', 'to_hop': ['D01', 'A00', 'C01', 'X26']},
    '7460108': {'ten_nganh': 'Khoa học dữ liệu', 'to_hop': ['D01', 'A00', 'C01', 'X26']},
    '7340301': {'ten_nganh': 'Kế toán', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7340201': {'ten_nganh': 'Tài chính ngân hàng', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7340205': {'ten_nganh': 'Công nghệ tài chính', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7340115': {'ten_nganh': 'Marketing', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7340101': {'ten_nganh': 'Quản trị kinh doanh', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7340120': {'ten_nganh': 'Kinh doanh quốc tế', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7340122': {'ten_nganh': 'Thương mại điện tử', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7510605': {'ten_nganh': 'Logistics và quản lý chuỗi cung ứng', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7340123': {'ten_nganh': 'Kinh doanh thời trang và dệt may', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7540204': {'ten_nganh': 'Công nghệ dệt, may', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7510202': {'ten_nganh': 'Công nghệ chế tạo máy', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7510203': {'ten_nganh': 'Công nghệ kỹ thuật cơ điện tử', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7510301': {'ten_nganh': 'Công nghệ kỹ thuật điện - điện tử', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7510303': {'ten_nganh': 'Công nghệ kỹ thuật điều khiển và tự động hóa', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7520115': {'ten_nganh': 'Kỹ thuật nhiệt', 'to_hop': ['D01', 'A01', 'C01', 'A00']},
    '7510406': {'ten_nganh': 'Công nghệ kỹ thuật môi trường', 'to_hop': ['B00', 'A01', 'A00', 'D07']},
    '7850101': {'ten_nganh': 'Quản lý tài nguyên và môi trường', 'to_hop': ['B00', 'A01', 'A00', 'D07']},
    '7510401': {'ten_nganh': 'Công nghệ kỹ thuật hóa học', 'to_hop': ['B00', 'B08', 'A00', 'D07']},
    '7510402': {'ten_nganh': 'Công nghệ vật liệu', 'to_hop': ['B00', 'B08', 'A00', 'D07']},
    '7420201': {'ten_nganh': 'Công nghệ sinh học', 'to_hop': ['B00', 'B08', 'A00', 'D07']},
    '7540105': {'ten_nganh': 'Công nghệ chế biến thủy sản', 'to_hop': ['B00', 'B08', 'A00', 'D07']},
    '7540101': {'ten_nganh': 'Công nghệ thực phẩm', 'to_hop': ['B00', 'B08', 'A00', 'D07']},
    '7540106': {'ten_nganh': 'Đảm bảo chất lượng và an toàn thực phẩm', 'to_hop': ['B00', 'B08', 'A00', 'D07']},
    '7340129': {'ten_nganh': 'Quản trị kinh doanh thực phẩm', 'to_hop': ['B00', 'D01', 'C02', 'D07']},
    '7819009': {'ten_nganh': 'Khoa học dinh dưỡng và ẩm thực', 'to_hop': ['B00', 'A01', 'C02', 'D07']},
    '7819010': {'ten_nganh': 'Khoa học chế biến món ăn', 'to_hop': ['B00', 'A01', 'C02', 'D07']},
    '7810101': {'ten_nganh': 'Du lịch', 'to_hop': ['D01', 'C03', 'D15', 'C00']},
    '7380101': {'ten_nganh': 'Luật', 'to_hop': ['D01', 'C03', 'C14', 'C00']}
}

# Mapping tổ hợp môn với các môn học
TO_HOP_MON = {
    'A00': ['Toán', 'Lý', 'Hóa'],
    'A01': ['Toán', 'Lý', 'Anh'],
    'B00': ['Toán', 'Hóa', 'Sinh'],
    'B08': ['Toán', 'Sinh', 'Anh'],
    'C00': ['Văn', 'Sử', 'Địa'],
    'C01': ['Văn', 'Toán', 'Lý'],
    'C02': ['Văn', 'Toán', 'Hóa'],
    'C03': ['Văn', 'Toán', 'Sử'],
    'C14': ['Toán', 'Văn', 'GDKTPL'],
    'D01': ['Toán', 'Văn', 'Anh'],
    'D07': ['Toán', 'Hóa', 'Anh'],
    'D09': ['Toán', 'Sử', 'Anh'],
    'D14': ['Văn', 'Anh', 'Sử'],
    'D15': ['Văn', 'Anh', 'Địa'],
    'X26': ['Toán', 'Tin', 'Anh']
}

class HocBaAnalyzer:
    def __init__(self):
        self.rf_model = None
        self.nb_model = None
        self.le_nganh = None
        self.feature_names = None
        self.name_map = {}
        self._models_loaded = False

    def load_models(self):
        """Load pre-trained HB models from models/hocba_models.pkl"""
        model_path = os.path.join(_base_dir(), 'models', 'hocba_models.pkl')
        if not os.path.exists(model_path):
            print("⚠️ Chưa có models/hocba_models.pkl. Hãy chạy training/train_hocba_models.py trước.")
            return False
        try:
            payload = joblib.load(model_path)
            self.rf_model = payload.get('rf_model')
            self.nb_model = payload.get('nb_model')
            self.le_nganh = payload.get('le_nganh')
            self.feature_names = payload.get('feature_names', ['Diem_Mon1', 'Diem_Mon2', 'Diem_Mon3', 'Diem_HB_Tinh', 'Nam'])
            self.name_map = payload.get('name_map', {})
            meta = payload.get('metadata', {})
            acc_txt = f"RF={meta.get('rf_acc', 0):.1%} | NB={meta.get('nb_acc', 0):.1%}"
            print(f"✅ Đã load HB models ({acc_txt})")
            self._models_loaded = True
            return True
        except Exception as e:
            print(f"❌ Lỗi load models HB: {e}")
            return False
    
    def get_priority_points(self, khu_vuc, doi_tuong, diem_khuyen_khich=0):
        """
        Tính điểm ưu tiên theo quy chế HUIT 2026
        KV1: 0.75, KV2-NT: 0.5, KV2: 0.25, KV3: 0
        Nhóm 1 (01-04): 2.0, Nhóm 2 (05-07): 1.0
        Khuyến khích (IELTS/Năng khiếu): tối đa 1.5
        Tổng ưu tiên tối đa: 3.0
        """
        map_kv = {'KV1': 0.75, 'KV2-NT': 0.5, 'KV2': 0.25, 'KV3': 0}
        map_dt = {
            'Nhóm 1 (01-04)': 2.0, 
            'Nhóm 2 (05-07)': 1.0,
            'Không thuộc diện ưu tiên': 0
        }
        
        p_kv = map_kv.get(khu_vuc, 0)
        p_dt = map_dt.get(doi_tuong, 0)
            
        total = p_kv + p_dt
        return min(3.0, total)
    
    def tinh_diem_hoc_ba(self, to_hop, diem_5_hk):
        """
        Tính điểm học bạ theo công thức HUIT
        
        Args:
            to_hop: Tổ hợp môn (VD: 'D01')
            diem_5_hk: Dict điểm 5 học kỳ cho 3 môn
                      {'mon1': [hk1_10, hk2_10, hk1_11, hk2_11, hk1_12],
                       'mon2': [...], 'mon3': [...]}
        
        Returns:
            dict: Thông tin điểm chi tiết
        """
        
        if to_hop not in TO_HOP_MON:
            return None
        
        mon_hoc = TO_HOP_MON[to_hop]
        
        # Tính điểm trung bình từng môn (5 học kỳ)
        diem_tb_mon = {}
        for i, mon in enumerate(['mon1', 'mon2', 'mon3'], 1):
            if mon in diem_5_hk:
                tb_mon = sum(diem_5_hk[mon]) / 5
                diem_tb_mon[f'mon{i}'] = round(tb_mon, 2)
            else:
                return None
        
        # Điểm học bạ theo công thức HUIT CHÍNH XÁC: CỘNG (không chia trung bình)
        diem_hb = diem_tb_mon['mon1'] + diem_tb_mon['mon2'] + diem_tb_mon['mon3']
        
        return {
            'to_hop': to_hop,
            'mon_hoc': mon_hoc,
            'diem_tb_mon1': diem_tb_mon['mon1'],
            'diem_tb_mon2': diem_tb_mon['mon2'], 
            'diem_tb_mon3': diem_tb_mon['mon3'],
            'diem_hb': round(diem_hb, 2),  # Thang điểm 30
            'chi_tiet_5hk': diem_5_hk
        }
    
    def predict_nganh(self, diem_hb_info, top_k=10, nguyen_vong=''):
        """Dự đoán ngành phù hợp dựa trên điểm học bạ"""
        if not self._models_loaded:
            if not self.load_models():
                return []
        
        try:
            # Lấy điểm cuối (đã cộng ưu tiên nếu có)
            diem_final = diem_hb_info.get('diem_xet_tuyen', diem_hb_info['diem_hb'])
            
            # Chuẩn bị features
            features = [
                diem_hb_info['diem_tb_mon1'],
                diem_hb_info['diem_tb_mon2'],
                diem_hb_info['diem_tb_mon3'],
                diem_final,  # Sử dụng điểm đã cộng ưu tiên
                2024  # Năm hiện tại
            ]
            
            X_pred = np.array([features])
            
            # Predict with pre-trained models
            rf_proba = self.rf_model.predict_proba(X_pred)[0]
            nb_proba = self.nb_model.predict_proba(X_pred)[0]
            
            # Ensemble (70% RF + 30% NB)
            ensemble_proba = 0.7 * rf_proba + 0.3 * nb_proba
            
            # Lấy top ngành
            nganh_codes = self.le_nganh.classes_
            results = []
            
            # Mapping 9 nhóm (đồng nhất với DGNL): gồm alias ngắn và tên đầy đủ
            NGUYEN_VONG_MAP = {
                'CNTT': ['7480201', '7480202', '7460108', '7340205'],
                'Kinh doanh': ['7340101', '7340115', '7340120', '7340122', '7340129'],
                'Kỹ thuật': ['7510202', '7510203', '7520115', '7510301', '7510303'],
                'Thực phẩm - Môi trường': ['7540101', '7540106', '7540105', '7819009', '7819010', '7340129'],
                'Tài chính': ['7340301', '7340201', '7340205'],
                'Hóa sinh': ['7510401', '7510406', '7850101', '7420201', '7510402'],
                'Luật - Ngôn ngữ': ['7380101', '7380107', '7220201', '7220204'],
                'Logistics': ['7510605', '7340123', '7540204'],
                'Du lịch': ['7810101', '7810103', '7810201', '7810202'],

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
            
            for i, prob in enumerate(ensemble_proba):
                nganh_code = nganh_codes[i]
                if nganh_code in NGANH_TO_HOP:
                    nganh_info = NGANH_TO_HOP[nganh_code]
                    
                    # BOOST MẠNH như DGNL
                    boost = 1.0
                    preferred = False
                    if nguyen_vong:
                        if nguyen_vong in NGUYEN_VONG_MAP:
                            preferred = nganh_code in NGUYEN_VONG_MAP[nguyen_vong]
                        else:
                            for group, majors in NGUYEN_VONG_MAP.items():
                                if nguyen_vong.lower() in group.lower() or group.lower() in nguyen_vong.lower():
                                    if nganh_code in majors:
                                        preferred = True
                                        break
                    if preferred:
                        boost *= 1.8
                    else:
                        boost *= 0.6
                    # Tổ hợp phù hợp/phạt mạnh
                    to_hop_phu_hop = diem_hb_info['to_hop'] in nganh_info['to_hop']
                    if to_hop_phu_hop:
                        boost *= 1.15
                    else:
                        boost *= 0.35
                    # Boost thêm nếu thuộc nhóm ngành mong muốn
                    if preferred:
                        boost *= 1.3
                    # Điều chỉnh theo điểm cuối (thang 30)
                    score_factor = min(1.5, diem_final / 20)
                    final_prob = prob * 100 * boost * score_factor
                    # Clamp xác suất giống DGNL
                    final_prob = max(5, min(final_prob, 90))
                    results.append({
                        'ma_nganh': nganh_code,
                        'ten_nganh': nganh_info['ten_nganh'],
                        'xac_suat': final_prob,
                        'to_hop_phu_hop': to_hop_phu_hop,
                        'thuoc_nhom_mong_muon': preferred
                    })
            
            # Ưu tiên ngành thuộc nhóm/nguyện vọng lên đầu, sau đó đến tổ hợp phù hợp, rồi xác suất
            def sort_key(x):
                # 3 mức ưu tiên: vừa thuộc nhóm vừa hợp tổ hợp > thuộc nhóm > hợp tổ hợp > còn lại
                nhom = bool(x.get('thuoc_nhom_mong_muon'))
                tohop = bool(x.get('to_hop_phu_hop'))
                # Sắp xếp: (nhom, tohop, xác suất)
                return (nhom and tohop, nhom, tohop, x['xac_suat'])
            results = sorted(results, key=sort_key, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"❌ Lỗi prediction: {e}")
            return []

# Test function
def test_hoc_ba_system():
    """Test hệ thống học bạ"""
    analyzer = HocBaAnalyzer()
    
    # Test data: học sinh mạnh D01 (Toán, Văn, Anh)
    test_diem = {
        'mon1': [8.0, 8.2, 8.5, 8.3, 8.4],  # Toán
        'mon2': [7.5, 7.8, 8.0, 7.9, 8.1],  # Văn
        'mon3': [8.5, 8.7, 8.9, 8.6, 8.8]   # Anh
    }
    
    # Tính điểm học bạ
    diem_hb_info = analyzer.tinh_diem_hoc_ba('D01', test_diem)
    print("🧪 Test tính điểm học bạ:")
    print(f"   Tổ hợp: {diem_hb_info['to_hop']} ({diem_hb_info['mon_hoc']})")
    print(f"   Điểm TB môn 1: {diem_hb_info['diem_tb_mon1']}")
    print(f"   Điểm TB môn 2: {diem_hb_info['diem_tb_mon2']}")
    print(f"   Điểm TB môn 3: {diem_hb_info['diem_tb_mon3']}")
    print(f"   Điểm học bạ: {diem_hb_info['diem_hb']}")
    
    # Dự đoán ngành
    if analyzer.train_models():
        results = analyzer.predict_nganh(diem_hb_info)
        print(f"\n🎯 TOP 5 NGÀNH GỢI Ý:")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. {result['ten_nganh']:<40} {result['xac_suat']:5.1f}%")

if __name__ == "__main__":
    test_hoc_ba_system()