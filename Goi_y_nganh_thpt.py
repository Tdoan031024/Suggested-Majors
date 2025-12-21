# -*- coding: utf-8 -*-
"""
Gợi ý ngành theo phương thức PT1 (thi TN THPT 2025)
- Sử dụng mô hình RF+NB (70/30) đã huấn luyện từ All-2023, All-2022
- Đầu vào: điểm 3 môn (Mon1, Mon2, Mon3), ưu tiên KV/ĐT (điểm cộng), thứ tự NV (1..n), mã tổ hợp (A00/A01/D01/B00/C00...) nếu biết
- Đầu ra: danh sách top_n ngành với xác suất xếp hạng
"""
import os
import re
import math
import joblib
import numpy as np
import pandas as pd
from typing import Optional, List, Dict
from hoc_ba_analyzer import NGANH_TO_HOP  # dùng mapping tổ hợp 2025

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'pt1_models.pkl')


def _group_mapping_codes() -> Dict[str, List[str]]:
    """Mapping 9 nhóm ngành (đồng nhất với DGNL/Học bạ). Bao gồm alias ngắn và tên đầy đủ."""
    return {
        # Alias ngắn
        'CNTT': ['7480201', '7480202', '7460108', '7340205'],
        'Kinh doanh': ['7340101', '7340115', '7340120', '7340122', '7340129'],
        'Kỹ thuật': ['7510202', '7510203', '7520115', '7510301', '7510303'],
        'Thực phẩm - Môi trường': ['7540101', '7540106', '7540105', '7819009', '7819010', '7340129'],
        'Tài chính': ['7340301', '7340201', '7340205'],
        'Hóa sinh': ['7510401', '7510406', '7850101', '7420201', '7510402'],
        'Luật - Ngôn ngữ': ['7380101', '7380107', '7220201', '7220204'],
        'Logistics': ['7510605', '7340123', '7540204'],
        'Du lịch': ['7810101', '7810103', '7810201', '7810202'],

        # Tên đầy đủ từ menu (đồng bộ hiển thị)
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

def get_group_mapping_codes() -> Dict[str, List[str]]:
    """Public accessor for group->majors mapping (9 nhóm)."""
    return _group_mapping_codes()

def _resolve_group_key(user_input: Optional[str]) -> Optional[str]:
    if not user_input:
        return None
    m = _group_mapping_codes()
    if user_input in m:
        return user_input
    ui = user_input.lower()
    for k in m:
        kl = k.lower()
        if ui in kl or kl in ui:
            return k
    return None

def allowed_tohops_for_group(user_input: Optional[str]) -> set:
    """Return set of tổ hợp codes available in all majors of the selected group."""
    key = _resolve_group_key(user_input)
    if not key:
        return set()
    majors = _group_mapping_codes().get(key, [])
    allowed = set()
    for code in majors:
        info = NGANH_TO_HOP.get(code)
        if info:
            allowed.update(info.get('to_hop', []))
    return allowed


def _load_pt1_model():
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def _detect_tohop_from_subjects(mon1_name: str, mon2_name: str, mon3_name: str) -> str:
    # Đoán mã tổ hợp cơ bản theo 3 môn (tùy chọn). Hàm này đơn giản hóa, có thể cải tiến sau.
    s = {mon1_name.upper(), mon2_name.upper(), mon3_name.upper()}
    if {'TOÁN','LÝ','HÓA'} <= s:
        return 'A00'
    if {'TOÁN','LÝ','ANH'} <= s or {'TOÁN','VẬT LÝ','TIẾNG ANH'} <= s:
        return 'A01'
    if {'TOÁN','VĂN','ANH'} <= s or {'NGỮ VĂN','TOÁN','TIẾNG ANH'} <= s:
        return 'D01'
    if {'TOÁN','HÓA','SINH'} <= s:
        return 'B00'
    if {'VĂN','SỬ','ĐỊA'} <= s or {'NGỮ VĂN','LỊCH SỬ','ĐỊA LÍ'} <= s:
        return 'C00'
    return 'KHAC'


def goi_y_nganh_thpt(mon1: float, mon2: float, mon3: float,
                       diem_ut: float = 0.0,
                       thu_tu_nv: int = 1,
                       tohop: Optional[str] = None,
                       nguyen_vong: Optional[str] = None,
                       top_n: int = 10) -> List[Dict]:
    """
    mon1/2/3: điểm từng môn (0-10)
    diem_ut: tổng ưu tiên KV+ĐT (điểm cộng)
    thu_tu_nv: thứ tự nguyện vọng
    tohop: mã tổ hợp nếu biết (A00/A01/D01/B00/C00/...)
    nguyen_vong: tên nhóm ưa thích (CNTT, Kỹ thuật, ...)
    """
    payload = _load_pt1_model()
    if payload is None:
        # Không có mô hình → trả rỗng kèm lý do
        return [{'ma_nganh': None, 'ten_nganh': 'Không có mô hình PT1', 'xac_suat': 0.0, 'ly_do': 'Chưa huấn luyện pt1_models.pkl'}]

    rf = payload['rf_model']
    nb = payload['nb_model']
    le_nganh = payload['le_nganh']
    le_tohop = payload['le_tohop']
    name_map = payload.get('name_map', {})
    features = payload.get('features', ['Mon1','Mon2','Mon3','Diem_UT','ThuTuNV','ToHop_Enc','Year','Diem_Tong'])

    if tohop is None or not str(tohop).strip():
        # Nếu không biết, gán 'KHAC' (đã có trong train nếu có) hoặc mặc định 'A00'
        tohop = 'KHAC'
    tohop = str(tohop).strip().upper()

    # Xử lý mã tổ hợp chưa thấy trong train -> dùng unknown code
    try:
        tohop_enc = le_tohop.transform([tohop])[0]
    except Exception:
        # Nếu unseen, map về mã phổ biến như A00 nếu tồn tại, else 0
        try:
            tohop_enc = le_tohop.transform(['A00'])[0]
        except Exception:
            tohop_enc = 0

    year = 2024  # PT1 áp dụng cho 2025, dùng 2024 như mốc nội suy
    diem_tong = float(mon1) + float(mon2) + float(mon3) + float(diem_ut)

    row = {
        'Mon1': float(mon1),
        'Mon2': float(mon2),
        'Mon3': float(mon3),
        'Diem_UT': float(diem_ut),
        'ThuTuNV': int(thu_tu_nv),
        'ToHop_Enc': float(tohop_enc),
        'Year': float(year),
        'Diem_Tong': float(diem_tong)
    }
    X = pd.DataFrame([row], columns=features)

    # Ensemble 70/30
    try:
        proba_rf = rf.predict_proba(X)[0]
    except Exception:
        proba_rf = np.zeros(len(le_nganh.classes_), dtype=float)
    try:
        proba_nb = nb.predict_proba(X)[0]
    except Exception:
        proba_nb = np.zeros(len(le_nganh.classes_), dtype=float)

    proba = 0.7 * proba_rf + 0.3 * proba_nb

    # Boost theo nhóm ưa thích + tổ hợp + tiếng Anh (D01)
    group_map = _group_mapping_codes()
    prefer_raw = str(nguyen_vong or '').strip()
    prefer = prefer_raw.lower()
    english_boost = 1.10 if tohop == 'D01' else 1.0

    preferred_codes = set()
    if prefer_raw:
        if prefer_raw in group_map:
            preferred_codes.update(group_map[prefer_raw])
        else:
            for gname, codes in group_map.items():
                if prefer in gname.lower() or gname.lower() in prefer:
                    preferred_codes.update(codes)

    results_tmp = []
    for idx, code in enumerate(le_nganh.classes_):
        base = proba[idx]
        boost = 1.0

        # Ưa thích nhóm: x1.8 nếu thuộc; x0.6 nếu có chọn nhóm nhưng không thuộc
        if prefer_raw:
            if code in preferred_codes:
                boost *= 1.8
                nhom_flag = True
            else:
                boost *= 0.6
                nhom_flag = False
        else:
            nhom_flag = False

        # Tổ hợp tương thích (dựa vào NGANH_TO_HOP của HB)
        tohop_flag = False
        if code in NGANH_TO_HOP:
            if tohop in NGANH_TO_HOP[code]['to_hop']:
                boost *= 1.15
                tohop_flag = True
            else:
                boost *= 0.35
                tohop_flag = False

        # Boost tiếng Anh nếu D01
        boost *= english_boost

        adj = base * boost
        results_tmp.append((code, adj, tohop_flag, nhom_flag))

    # Gộp lại proba sau boost
    codes_order = [c for c, *_ in results_tmp]
    proba = np.array([p for _, p, *_ in results_tmp], dtype=float)

    # Chuẩn hóa và clamp
    s = proba.sum()
    if s > 0:
        proba = proba / s
    proba = np.clip(proba, 0.01, 0.95)

    # Sắp xếp top_n và ưu tiên ngành có tổ hợp phù hợp
    order = np.argsort(-proba)
    items = []
    for i in order:
        code = codes_order[i]
        ten = name_map.get(code, f"Ngành {code}")
        p = float(proba[i] * 100)
        tohop_ok = False
        nhom_ok = False
        # Lấy flags từ results_tmp theo code
        for c, _p, th_ok, nh_ok in results_tmp:
            if c == code:
                tohop_ok = th_ok
                nhom_ok = nh_ok
                break
        items.append({
            'ma_nganh': code,
            'ten_nganh': ten,
            'xac_suat': round(p, 2),
            'to_hop_phu_hop': tohop_ok,
            'thuoc_nhom_mong_muon': nhom_ok
        })

    # Nếu có chọn nhóm: chỉ giữ ngành thuộc nhóm
    if prefer_raw:
        group_codes = set()
        if prefer_raw in group_map:
            group_codes.update(group_map[prefer_raw])
        else:
            for gname, codes in group_map.items():
                if prefer in gname.lower() or gname.lower() in prefer:
                    group_codes.update(codes)
        items = [r for r in items if r['ma_nganh'] in group_codes]

    # Ưu tiên ngành có tổ hợp phù hợp trong phạm vi còn lại
    matching = [r for r in items if r['to_hop_phu_hop']]
    non_matching = [r for r in items if not r['to_hop_phu_hop']]
    if len(matching) >= top_n:
        return matching[:top_n]
    need = top_n - len(matching)
    return matching + non_matching[:need]
