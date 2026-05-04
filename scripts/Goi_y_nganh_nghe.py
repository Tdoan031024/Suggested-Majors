# -*- coding: utf-8 -*-
import joblib
import numpy as np
import os
import sys

def _base_dir():
    """Trả về thư mục gốc đúng dù chạy bình thường hay dưới dạng .exe (PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Nếu đang ở trong thư mục scripts hoặc evaluation, lùi lại 1 cấp để tìm thư mục gốc
    if os.path.basename(current_dir) in ['scripts', 'evaluation']:
        return os.path.dirname(current_dir)
    return current_dir

def load_models():
    try:
        models_path = os.path.join(_base_dir(), 'models', 'dgnl_models.pkl')
        nganh_path = os.path.join(_base_dir(), 'models', 'nganh_mapping.pkl')
        
        if not os.path.exists(models_path) or not os.path.exists(nganh_path):
            return None, None
            
        dgnl_models = joblib.load(models_path)
        nganh_huit = joblib.load(nganh_path)
        
        print(f'Loaded models with {dgnl_models["metadata"]["ensemble_accuracy"]:.1%} accuracy')
        return dgnl_models, nganh_huit
    except Exception as e:
        print(f'Error loading models: {e}')
        return None, None

DGNL_MODELS, NGANH_HUIT = load_models()

def goi_y_nganh_simple(diem_dgnl, diem_dt=0, diem_kv=3, thu_tu_nv=1, nguyen_vong=None, top_n=15):
    """
    Gợi ý ngành nghề dựa trên điểm DGNL và pre-trained models
    """
    if DGNL_MODELS is None or NGANH_HUIT is None:
        return [{'ma_nganh': 'Error', 'ten_nganh': 'Models not loaded', 'xac_suat': 0}]
    
    try:
        rf_model = DGNL_MODELS['rf_model']
        nb_model = DGNL_MODELS['nb_model'] 
        le_nganh = DGNL_MODELS['le_nganh']
        
        if not (0 <= diem_dgnl <= 1200):
            return [{'ma_nganh': 'Error', 'ten_nganh': 'Điểm DGNL không hợp lệ', 'xac_suat': 0}]
        
        results = []
        
        # Mapping 9 nhóm ngành HUIT
        nguyen_vong_map = {
            'CNTT': ['7480201', '7480202', '7460108'],
            'Kinh tế': ['7340101', '7340115', '7340120', '7340122', '7340129'],
            'Kỹ thuật': ['7510202', '7510203', '7520115', '7510301', '7510303'],
            'Thực phẩm': ['7540101', '7540106', '7540105', '7819009', '7819010', '7340129'],
            'Ngôn ngữ': ['7220201', '7220204'],
            'Luật': ['7380101', '7380107'],
            'Du lịch': ['7810101', '7810103', '7810201', '7810202'],
            'Logistics': ['7510605', '7340123', '7540204'],
            'Tài chính': ['7340301', '7340201', '7340205'],

            # Tên đầy đủ từ menu giao diện
            'Công nghệ – Chế biến – Thực phẩm': ['7540101', '7540106', '7540105', '7819009', '7819010', '7340129'],
            'Kỹ thuật – Cơ khí – Tự động hóa': ['7510202', '7510203', '7520115', '7510301', '7510303'],
            'Hóa học – Sinh học – Môi trường – Vật liệu': ['7510401', '7510406', '7850101', '7420201', '7510402'],
            'Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu': ['7480201', '7480202', '7460108'],
            'Kinh doanh – Quản trị – Marketing': ['7340101', '7340115', '7340120', '7340122', '7340129'],
            'Kế toán – Tài chính – Ngân hàng': ['7340301', '7340201', '7340205'],
            'Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt': ['7510605', '7340123', '7540204'],
            'Luật – Xã hội – Ngôn ngữ': ['7380101', '7380107', '7220201', '7220204'],
            'Du lịch – Nhà hàng – Khách sạn – Dịch vụ': ['7810101', '7810103', '7810201', '7810202']
        }

        def normalize_dash(s):
            if not s: return ""
            return s.replace('–', '-').replace('—', '-')

        for ma_nganh_str, ten_nganh in NGANH_HUIT.items():
            try:
                ma_nganh_str_clean = str(ma_nganh_str).strip()
                if ma_nganh_str_clean in le_nganh.classes_:
                    ma_nganh_encoded = le_nganh.transform([ma_nganh_str_clean])[0]
                else:
                    ma_nganh_encoded = 0
                
                # Features
                diem_tong_norm = (diem_dgnl - 600) / (1200 - 600)
                ty_le = 15.0
                year = 2023
                
                fv = np.array([[diem_tong_norm, thu_tu_nv, diem_kv, diem_dt, ty_le, ma_nganh_encoded, year]])
                
                rf_p = rf_model.predict_proba(fv)[0][ma_nganh_encoded]
                nb_p = nb_model.predict_proba(fv)[0][ma_nganh_encoded]
                
                prob = (0.7 * rf_p + 0.3 * nb_p) * 100
                
                # Boost logic
                is_pref = False
                if nguyen_vong:
                    nv_norm = normalize_dash(nguyen_vong)
                    if nv_norm in nguyen_vong_map:
                        if ma_nganh_str_clean in nguyen_vong_map[nv_norm]:
                            is_pref = True
                    else:
                        for g, codes in nguyen_vong_map.items():
                            if nv_norm in normalize_dash(g) or normalize_dash(g) in nv_norm:
                                if ma_nganh_str_clean in codes:
                                    is_pref = True
                                    break
                
                boost = 1.0
                if is_pref:
                    boost = 1.8
                elif nguyen_vong:
                    boost = 0.6
                
                # Score factor
                score_factor = max(0.5, min(3.0, (diem_dgnl + (diem_dt + diem_kv)*20) / 750.0))
                
                final_prob = max(5.0, min(95.0, prob * boost * score_factor))
                
                results.append({
                    'ma_nganh': ma_nganh_str_clean,
                    'ten_nganh': ten_nganh,
                    'xac_suat': round(final_prob, 1),
                    'thuoc_nhom_mong_muon': is_pref if nguyen_vong else None
                })
            except Exception:
                continue
        
        # Sort: Preferred first, then by probability
        results.sort(key=lambda x: (bool(x.get('thuoc_nhom_mong_muon')), x['xac_suat']), reverse=True)
        return results[:top_n]
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return []

def test_system():
    print('Testing DGNL system...')
    results = goi_y_nganh_simple(850, 0, 3, 1, "Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu", 5)
    for i, r in enumerate(results, 1):
        pref = "🎯" if r.get('thuoc_nhom_mong_muon') else "  "
        print(f'{i}. {pref} [{r["ma_nganh"]}] {r["ten_nganh"]}: {r["xac_suat"]}%')

if __name__ == '__main__':
    test_system()
