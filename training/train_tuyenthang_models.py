# -*- coding: utf-8 -*-
"""
Huấn luyện mô hình Tuyển thẳng (RF + NB 70/30) từ DXDuong.xlsx (TT-2023, TT-2022, TT-2021)
Lưu models/tt_models.pkl gồm: rf_model, nb_model, le_nganh, name_map, metadata
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    return df


def _pick_first(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _load_tt_sheets(xlsx_path: str) -> pd.DataFrame:
    xl = pd.ExcelFile(xlsx_path)
    all_rows = []
    for name in ['TT-2023', 'TT-2022', 'TT-2021']:
        if name not in xl.sheet_names:
            continue
        df = xl.parse(name)
        df = _normalize_columns(df)
        df['Year'] = int(name.split('-')[1])

        col_ma = _pick_first(df, ['Mã ngành', 'Mã  ngành'])
        col_ten = _pick_first(df, ['Tên  ngành', 'Tên ngành'])
        col_tb10 = _pick_first(df, ['Điểm TB  cả năm lớp 10 ', 'Điểm TB cả năm lớp 10'])
        col_tb11 = _pick_first(df, ['Điểm TB cả năm lớp 11 ', 'Điểm TB cả năm lớp 11'])
        col_tb12 = _pick_first(df, ['Điểm TB HK1 lớp 12 ', 'Điểm TB HK1 lớp 12'])
        col_tb_all = _pick_first(df, ['Điểm TB', 'Tổng TB'])
        col_ut_dt = _pick_first(df, ['Điểm ƯT ĐT'])
        col_ut_kv = _pick_first(df, ['Điểm ƯT KV'])
        col_eng10 = _pick_first(df, ['Điểm TB Tiếng Anh lớp 10'])
        col_eng11 = _pick_first(df, ['Điểm TB Tiếng Anh lớp 11'])
        col_eng12 = _pick_first(df, ['Điểm TB Tiếng Anh HK1 lớp 12 '])

        for _, r in df.iterrows():
            try:
                ma = r.get(col_ma)
                ten = r.get(col_ten)
                if pd.isna(ma) or pd.isna(ten):
                    continue
                ma = int(ma)
                
                tb10 = pd.to_numeric(r.get(col_tb10), errors='coerce') if col_tb10 else np.nan
                tb11 = pd.to_numeric(r.get(col_tb11), errors='coerce') if col_tb11 else np.nan
                tb12 = pd.to_numeric(r.get(col_tb12), errors='coerce') if col_tb12 else np.nan
                tb_all = pd.to_numeric(r.get(col_tb_all), errors='coerce') if col_tb_all else np.nan
                
                # nếu thiếu tổng, suy ra từ 3 thành phần
                if pd.isna(tb_all):
                    vals = [v for v in [tb10, tb11, tb12] if pd.notna(v)]
                    tb_all = sum(vals) if vals else np.nan
                
                ut_dt = pd.to_numeric(r.get(col_ut_dt), errors='coerce') if col_ut_dt else 0.0
                ut_kv = pd.to_numeric(r.get(col_ut_kv), errors='coerce') if col_ut_kv else 0.0
                
                e10 = pd.to_numeric(r.get(col_eng10), errors='coerce') if col_eng10 else np.nan
                e11 = pd.to_numeric(r.get(col_eng11), errors='coerce') if col_eng11 else np.nan
                e12 = pd.to_numeric(r.get(col_eng12), errors='coerce') if col_eng12 else np.nan
                e_vals = [v for v in [e10, e11, e12] if pd.notna(v)]
                eng = float(np.mean(e_vals)) if e_vals else np.nan
                
                all_rows.append({
                    'Ma_Nganh': str(ma),
                    'Ten_Nganh': str(ten).strip(),
                    'TB10': tb10, 'TB11': tb11, 'TBHK1_12': tb12,
                    'TB_total': tb_all,
                    'UT_DT': ut_dt, 'UT_KV': ut_kv,
                    'EngAvg': eng,
                    'Year': df.at[_, 'Year']
                })
            except Exception:
                continue
    return pd.DataFrame(all_rows)


def train_and_save(xlsx_path: str = None, out_path: str = None):
    if xlsx_path is None:
        xlsx_path = os.path.join(os.path.dirname(__file__), 'DXDuong.xlsx')
    if out_path is None:
        out_dir = os.path.join(os.path.dirname(__file__), 'models')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'tt_models.pkl')

    df = _load_tt_sheets(xlsx_path)
    if df.empty:
        raise RuntimeError('Không load được dữ liệu TT từ DXDuong.xlsx')

    # Impute
    for c in ['TB10','TB11','TBHK1_12','TB_total','UT_DT','UT_KV','EngAvg']:
        if c not in df.columns:
            df[c] = np.nan
        med = df[c].median(skipna=True)
        df[c] = df[c].fillna(med if not np.isnan(med) else 0.0)

    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(2023).astype(int)

    # Features & label
    features = ['TB10','TB11','TBHK1_12','TB_total','EngAvg','UT_DT','UT_KV','Year']
    X = df[features].astype(float)
    le = LabelEncoder()
    y = le.fit_transform(df['Ma_Nganh'].astype(str))

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
        'le_nganh': le,
        'name_map': name_map,
        'features': features,
        'metadata': {
            'rf_acc': float(rf_acc),
            'nb_acc': float(nb_acc),
            'records': int(len(df))
        }
    }

    joblib.dump(payload, out_path)
    print(f"✅ Saved TT models to {out_path}")
    print(f"📊 RF acc={rf_acc:.1%} | NB acc={nb_acc:.1%} | N={len(df)}")


if __name__ == '__main__':
    train_and_save()
