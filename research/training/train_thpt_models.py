# -*- coding: utf-8 -*-
"""
Huấn luyện mô hình PT1 (thi TN THPT 2025) bằng Random Forest + Naive Bayes (70/30)
Dữ liệu: DXDuong.xlsx sheets All-2023, All-2022 (sheet 4, 5)
Lưu: models/pt1_models.pkl
"""
import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from research.paths import DATASET_PATH, MODEL_DIR


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).replace('\n',' ').strip() for c in df.columns]
    return df


def _load_all_sheets(xlsx_path: str) -> pd.DataFrame:
    xl = pd.ExcelFile(xlsx_path)
    rows = []
    for name in ['All-2023','All-2022','DT-2021']:
        if name not in xl.sheet_names:
            continue
        df = xl.parse(name)
        df = _normalize_columns(df)
        year = int(name.split('-')[1])
        # key columns
        col_ma = 'Mã ngành trúng tuyển'
        col_ten = 'Tên ngành trúng tuyển'
        col_pt = 'Mã PTXT trúng tuyển'
        col_th = 'Mã tổ hợp trúng tuyển'
        col_nv = 'Thứ tự NV trúng tuyển'
        col_dg = 'Điểm trúng tuyển'
        # subject scores are in Unnamed: 9/11/13
        c1 = 'Unnamed: 9'
        c2 = 'Unnamed: 11'
        c3 = 'Unnamed: 13'
        c_dtut = 'ĐTƯT'
        c_kvut = 'KVƯT'
        # map KVƯT to points
        def map_kv(val):
            if pd.isna(val):
                return 0.0
            s = str(val).strip().upper()
            if s in ('3','KV3'):
                return 0.0
            if s in ('2NT','KV2-NT','KV2NT'):
                return 0.25
            if s in ('2','KV2'):
                return 0.5
            if s in ('1','KV1'):
                return 0.75
            return 0.0
        for _, r in df.iterrows():
            try:
                ma = r.get(col_ma)
                ten = r.get(col_ten)
                if pd.isna(ma) or pd.isna(ten):
                    continue
                ma = str(int(ma))
                tohop = str(r.get(col_th) or '').strip()
                nv = pd.to_numeric(r.get(col_nv), errors='coerce')
                dg = pd.to_numeric(r.get(col_dg), errors='coerce')
                m1 = pd.to_numeric(r.get(c1), errors='coerce')
                m2 = pd.to_numeric(r.get(c2), errors='coerce')
                m3 = pd.to_numeric(r.get(c3), errors='coerce')
                dt = pd.to_numeric(r.get(c_dtut), errors='coerce') if c_dtut in df.columns else np.nan
                kv = map_kv(r.get(c_kvut)) if c_kvut in df.columns else 0.0
                if pd.isna(m1) or pd.isna(m2) or pd.isna(m3):
                    continue
                ut = (0.0 if pd.isna(dt) else float(dt)) + float(kv)
                # derive dg if missing
                if pd.isna(dg):
                    dg = m1 + m2 + m3 + ut
                rows.append({
                    'Ma_Nganh': ma,
                    'Ten_Nganh': str(ten).strip(),
                    'ToHop': tohop,
                    'ThuTuNV': int(nv) if not pd.isna(nv) else 1,
                    'Mon1': float(m1), 'Mon2': float(m2), 'Mon3': float(m3),
                    'Diem_UT': float(ut), 'Diem_Tong': float(dg),
                    'Year': year
                })
            except Exception:
                continue
    return pd.DataFrame(rows)


def train_and_save(xlsx_path: str = None, out_path: str = None):
    if xlsx_path is None:
        xlsx_path = str(DATASET_PATH)
    if out_path is None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        out_path = str(MODEL_DIR / 'pt1_models.pkl')

    df = _load_all_sheets(xlsx_path)
    if df.empty:
        raise RuntimeError('Không load được dữ liệu PT1 từ DXDuong.xlsx')

    # Encoders
    le_nganh = LabelEncoder()
    le_tohop = LabelEncoder()

    df['ToHop_Enc'] = le_tohop.fit_transform(df['ToHop'].astype(str))
    y = le_nganh.fit_transform(df['Ma_Nganh'].astype(str))

    features = ['Mon1','Mon2','Mon3','Diem_UT','ThuTuNV','ToHop_Enc','Year','Diem_Tong']
    X = df[features].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf = RandomForestClassifier(n_estimators=80, max_depth=6, random_state=42)
    rf.fit(X_train, y_train)
    nb = GaussianNB()
    nb.fit(X_train, y_train)

    rf_acc = rf.score(X_test, y_test)
    nb_acc = nb.score(X_test, y_test)

    name_map = df.groupby('Ma_Nganh')['Ten_Nganh'].agg(lambda s: s.dropna().iloc[0] if not s.dropna().empty else f"Ngành {s.name}").to_dict()

    payload = {
        'rf_model': rf,
        'nb_model': nb,
        'le_nganh': le_nganh,
        'le_tohop': le_tohop,
        'name_map': name_map,
        'features': features,
        'metadata': {
            'rf_acc': float(rf_acc),
            'nb_acc': float(nb_acc),
            'records': int(len(df))
        }
    }

    joblib.dump(payload, out_path)
    print(f"✅ Saved PT1 models to {out_path}")
    print(f"📊 RF acc={rf_acc:.1%} | NB acc={nb_acc:.1%} | N={len(df)}")


if __name__ == '__main__':
    train_and_save()
