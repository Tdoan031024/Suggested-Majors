# -*- coding: utf-8 -*-
import joblib
import numpy as np
import os

def load_models():
    try:
        models_path = os.path.join(os.path.dirname(__file__), 'models', 'dgnl_models.pkl')
        nganh_path = os.path.join(os.path.dirname(__file__), 'models', 'nganh_mapping.pkl')
        
        dgnl_models = joblib.load(models_path)
        nganh_huit = joblib.load(nganh_path)
        
        print(f'Loaded models with {dgnl_models["metadata"]["ensemble_accuracy"]:.1%} accuracy')
        return dgnl_models, nganh_huit
    except Exception as e:
        print(f'Error: {e}')
        return None, None

DGNL_MODELS, NGANH_HUIT = load_models()

def goi_y_nganh_simple(diem_dgnl, diem_dt=0, diem_kv=3, thu_tu_nv=1, nguyen_vong=None, top_n=10):
    """
    Gợi ý ngành nghề dựa trên điểm DGNL và pre-trained models
    
    Args:
        diem_dgnl (float): Điểm DGNL (600-1200)
        diem_dt (float): Điểm ưu tiên đối tượng (default: 0)
        diem_kv (float): Điểm ưu tiên khu vực (default: 3)
        thu_tu_nv (int): Thứ tự nguyện vọng (default: 1) 
        nguyen_vong (str): Nguyện vọng ('CNTT', 'Kinh tế', 'Kỹ thuật', etc.)
        top_n (int): Số ngành gợi ý
        
    Returns:
        list: Danh sách ngành được gợi ý với xác suất
    """
    if DGNL_MODELS is None or NGANH_HUIT is None:
        return [{'ma_nganh': 'Error', 'ten_nganh': 'Models not loaded', 'xac_suat': 0}]
    
    try:
        rf_model = DGNL_MODELS['rf_model']
        nb_model = DGNL_MODELS['nb_model'] 
        le_nganh = DGNL_MODELS['le_nganh']
        
        if not (600 <= diem_dgnl <= 1200):
            return [{'ma_nganh': 'Error', 'ten_nganh': 'Điểm DGNL phải từ 600-1200', 'xac_suat': 0}]
        
        results = []
        
        for ma_nganh_str, ten_nganh in NGANH_HUIT.items():
            try:
                ma_nganh = int(ma_nganh_str)
                
                # Create feature vector using actual parameters
                # Chuẩn hóa về [0,1] theo thang 600–1200
                diem_tong_norm = (diem_dgnl - 600) / (1200 - 600)
                ty_le = 15.0   # Admission rate
                ma_nganh_encoded = le_nganh.transform([ma_nganh])[0] if ma_nganh in le_nganh.classes_ else 0
                year = 2023
                
                # Use actual parameters passed to function
                feature_vector = np.array([[diem_tong_norm, thu_tu_nv, diem_kv, diem_dt, ty_le, ma_nganh_encoded, year]])
                
                rf_prob = rf_model.predict_proba(feature_vector)[0][1]
                nb_prob = nb_model.predict_proba(feature_vector)[0][1]
                
                ensemble_prob = 0.7 * rf_prob + 0.3 * nb_prob
                base_prob = ensemble_prob * 100
                
                to_hop_boost = 1.0
                if ma_nganh_str in ['7480201', '7480202', '7460108']:
                    to_hop_boost = 1.2
                elif ma_nganh_str in ['7340101', '7340115', '7340120']:
                    to_hop_boost = 1.1
                
                adjusted_prob = base_prob * to_hop_boost
                
                # Preference group boost với mapping 9 nhóm ngành (đã chuẩn hóa theo HUIT)
                if nguyen_vong:
                    # Mapping đầy đủ các nhóm ngành và alias
                    nguyen_vong_map = {
                        # Alias ngắn
                        'CNTT': ['7480201', '7480202', '7460108', '7340205'],
                        'Kinh tế': ['7340101', '7340115', '7340120', '7340122', '7340129'],
                        'Kỹ thuật': ['7510202', '7510203', '7520115', '7510301', '7510303'],
                        'Y tế': ['7420201', '7540101', '7540106', '7540105', '7819009', '7819010'],
                        'Ngôn ngữ': ['7220201', '7220204'],
                        'Luật': ['7380101', '7380107'],
                        'Du lịch': ['7810101', '7810103', '7810201', '7810202'],
                        'Logistics': ['7510605', '7340123', '7540204'],

                        # Tên đầy đủ từ menu (không emoji)
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
                    
                    # Kiểm tra xem ngành có trong nhóm nguyện vọng không
                    is_preferred = False
                    if nguyen_vong in nguyen_vong_map:
                        if ma_nganh_str in nguyen_vong_map[nguyen_vong]:
                            is_preferred = True
                    else:
                        # Kiểm tra substring matching cho tên dài
                        for group, majors in nguyen_vong_map.items():
                            if nguyen_vong in group or group in nguyen_vong:
                                if ma_nganh_str in majors:
                                    is_preferred = True
                                    break
                    
                    if is_preferred:
                        adjusted_prob *= 1.8  # Boost mạnh hơn cho ngành ưa thích
                    else:
                        adjusted_prob *= 0.6  # Penalty mạnh hơn cho ngành không ưa thích
                
                # Clamp probability với range rộng hơn để tạo sự khác biệt
                final_prob = max(5, min(90, adjusted_prob))
                
                results.append({
                    'ma_nganh': ma_nganh_str,
                    'ten_nganh': ten_nganh,
                    'xac_suat': round(final_prob, 1)
                })
                
            except Exception as e:
                continue
        
        results.sort(key=lambda x: x['xac_suat'], reverse=True)
        return results[:top_n]
        
    except Exception as e:
        return [{'ma_nganh': 'Error', 'ten_nganh': f'Lỗi: {str(e)}', 'xac_suat': 0}]

def test_system():
    print('Testing DGNL system...')
    
    test_cases = [
        {'diem': 750, 'nguyen_vong': 'CNTT'},
        {'diem': 600, 'nguyen_vong': 'Kinh tế'},
        {'diem': 450, 'nguyen_vong': None}
    ]
    
    for test in test_cases:
        print(f'Test: Điểm {test["diem"]}, Nguyện vọng: {test["nguyen_vong"]}')
        # Gọi theo chữ ký đúng: (diem_dgnl, diem_dt=0, diem_kv=3, thu_tu_nv=1, nguyen_vong=None, top_n=10)
        results = goi_y_nganh_simple(test['diem'], 0, 3, 1, test['nguyen_vong'], 5)
        for i, result in enumerate(results, 1):
            print(f'  {i}. [{result["ma_nganh"]}] {result["ten_nganh"]}: {result["xac_suat"]}%')
        print()

if __name__ == '__main__':
    test_system()
