# -*- coding: utf-8 -*-
"""
Training script for Học bạ (HB) method.
Reads HB-2023/HB-2022/HB-2021 from DXDuong.xlsx, engineers features,
trains RandomForest + GaussianNB, and saves to models/hocba_models.pkl.

Runtime policy: Use this script offline to produce the .pkl once;
the app should only load the saved models at runtime.
"""

import os
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from datetime import datetime


def load_hb_data(excel_path: str) -> pd.DataFrame:
    sheets = ["HB-2023", "HB-2022", "HB-2021"]
    frames = []
    for sh in sheets:
        df = pd.read_excel(excel_path, sheet_name=sh)
        df.columns = df.columns.str.replace("\n", " ").str.strip()
        df["Nam"] = int(sh.split("-")[1])
        frames.append(df)
    df_all = pd.concat(frames, ignore_index=True)
    return df_all


def find_ma_nganh_col(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        col_clean = col.replace("\n", " ").strip().lower()
        if "mã" in col_clean and "ngành" in col_clean:
            return col
    return None


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    dfc = df.copy()

    diem_cols = [
        'Điểm TB cả năm lớp 10 (môn 1)', 'Điểm TB cả năm lớp 11 (môn 1)', 'Điểm TB HK1 lớp 12 (môn 1)',
        'Điểm TB cả năm lớp 10 (môn 2)', 'Điểm TB cả năm lớp 11 (môn 2)', 'Điểm TB HK1 lớp 12 (môn 2)',
        'Điểm TB cả năm lớp 10 (môn 3)', 'Điểm TB cả năm lớp 11 (môn 3)', 'Điểm TB HK1 lớp 12 (môn 3)'
    ]
    for col in diem_cols:
        if col in dfc.columns:
            dfc[col] = pd.to_numeric(dfc[col], errors='coerce')

    available = [c for c in diem_cols if c in dfc.columns]
    dfc = dfc.dropna(subset=available)

    # Compute 3 subject averages (per HUIT formula, then sum for HB score)
    dfc['Diem_Mon1'] = (dfc['Điểm TB cả năm lớp 10 (môn 1)'] + dfc['Điểm TB cả năm lớp 11 (môn 1)'] + dfc['Điểm TB HK1 lớp 12 (môn 1)']) / 3
    dfc['Diem_Mon2'] = (dfc['Điểm TB cả năm lớp 10 (môn 2)'] + dfc['Điểm TB cả năm lớp 11 (môn 2)'] + dfc['Điểm TB HK1 lớp 12 (môn 2)']) / 3
    dfc['Diem_Mon3'] = (dfc['Điểm TB cả năm lớp 10 (môn 3)'] + dfc['Điểm TB cả năm lớp 11 (môn 3)'] + dfc['Điểm TB HK1 lớp 12 (môn 3)']) / 3
    dfc['Diem_HB_Tinh'] = dfc['Diem_Mon1'] + dfc['Diem_Mon2'] + dfc['Diem_Mon3']

    ma_nganh_col = find_ma_nganh_col(dfc)
    if not ma_nganh_col:
        raise RuntimeError("Không tìm thấy cột mã ngành trong dữ liệu HB")
    dfc['Ma_Nganh'] = pd.to_numeric(dfc[ma_nganh_col], errors='coerce')
    dfc = dfc.dropna(subset=['Ma_Nganh'])
    dfc['Ma_Nganh'] = dfc['Ma_Nganh'].astype(int).astype(str)

    return dfc


def train_and_save(excel_path: str, out_path: str):
    print(f"🔄 Loading HB data from {excel_path} ...")
    df = load_hb_data(excel_path)
    print(f"✅ Loaded {len(df):,} rows from 3 years")

    dfp = preprocess(df)
    print(f"✅ Preprocessed -> {len(dfp):,} valid rows")

    feature_cols = ['Diem_Mon1', 'Diem_Mon2', 'Diem_Mon3', 'Diem_HB_Tinh', 'Nam']
    X = dfp[feature_cols].fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(dfp['Ma_Nganh'])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
    rf.fit(X_train, y_train)
    nb = GaussianNB()
    nb.fit(X_train, y_train)

    rf_acc = float(rf.score(X_test, y_test))
    nb_acc = float(nb.score(X_test, y_test))
    print(f"📊 RF acc: {rf_acc:.2%} | NB acc: {nb_acc:.2%}")

    # Optional name map if present
    name_map = {}
    for col in dfp.columns:
        lc = col.replace('\n', ' ').strip().lower()
        if 'tên' in lc and 'ngành' in lc:
            try:
                # build code->name map from original df rows (dropna)
                tmp = pd.DataFrame({'code': dfp['Ma_Nganh'], 'name': dfp[col].astype(str)})
                tmp = tmp.dropna().drop_duplicates(subset=['code'])
                name_map = dict(zip(tmp['code'], tmp['name']))
            except Exception:
                name_map = {}
            break

    payload = {
        'rf_model': rf,
        'nb_model': nb,
        'le_nganh': le,
        'feature_names': feature_cols,
        'name_map': name_map,
        'metadata': {
            'rf_acc': rf_acc,
            'nb_acc': nb_acc,
            'rows': int(len(dfp)),
            'created_at': datetime.now().isoformat(timespec='seconds')
        }
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    joblib.dump(payload, out_path)
    print(f"💾 Saved HB models to {out_path}")


if __name__ == "__main__":
    excel = "DXDuong.xlsx"
    out = os.path.join("models", "hocba_models.pkl")
    if not os.path.exists(excel):
        raise SystemExit(f"❌ Không tìm thấy {excel} trong thư mục làm việc hiện tại.")
    train_and_save(excel, out)
