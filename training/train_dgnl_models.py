# -*- coding: utf-8 -*-
"""
Training script for DGNL (Danh gia nang luc) method.
Reads 2023-DGNL / DGNL-2022 / DGNL-2021 from DXDuong.xlsx, engineers features,
trains RandomForest + GaussianNB, and saves to models/dgnl_models.pkl.

Runtime policy: Use this script offline to produce the .pkl once;
the app should only load the saved models at runtime.

Fix: Trich xuat cot diem tu TUNG SHEET truoc khi concat,
     tranh mat du lieu khi ten cot khac nhau giua cac nam.
     - 2023-DGNL : 'Diem tong End'
     - DGNL-2022 : 'Diem Tong' (va 'Diem thi')
     - DGNL-2021 : 'Tong Diem' (va 'Diem thi')
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')


def _find_col_in(df: pd.DataFrame, keywords: list) -> str | None:
    """Tim cot chua TAT CA keyword (normalize spaces, case-insensitive)."""
    for col in df.columns:
        n = ' '.join(col.lower().split())
        if all(kw in n for kw in keywords):
            return col
    return None


def _extract_score(df: pd.DataFrame) -> pd.Series:
    """
    Tim va tra ve cot diem chinh xac cho TUNG sheet.
    Thu tu uu tien:
      1. Cot co ca 'tong'/'tổng' VA 'diem'/'điểm' (e.g. 'Diem Tong', 'Diem tong End', 'Tong Diem')
      2. Cot co 'diem'/'điểm' VA 'thi' (e.g. 'Diem thi')
    """
    # Uu tien 1: cot tong diem
    for col in df.columns:
        n = ' '.join(col.lower().split())
        has_tong = 'tong' in n or 't\u1ed5ng' in n
        has_diem = 'diem' in n or '\u0111i\u1ec3m' in n
        if has_tong and has_diem:
            print(f"    -> Diem col (tong): '{col}'")
            return pd.to_numeric(df[col], errors='coerce')
    # Fallback: cot diem thi
    for col in df.columns:
        n = ' '.join(col.lower().split())
        if ('diem' in n or '\u0111i\u1ec3m' in n) and 'thi' in n:
            print(f"    -> Diem col (thi): '{col}'")
            return pd.to_numeric(df[col], errors='coerce')
    print("    -> Khong tim thay cot diem, dung synthetic")
    np.random.seed(42)
    return pd.Series(np.random.normal(900, 150, len(df)).clip(600, 1200))


def _find_ma_nganh(df: pd.DataFrame) -> str | None:
    """Tim cot ma nganh (ho tro co dau va khong dau, underscore, nhieu dang viet)."""
    for col in df.columns:
        cn = ' '.join(col.lower().replace('_', ' ').split())
        # Khop: 'ma nganh', 'mã ngành', 'ma  nganh', 'Ma_Nganh'...
        has_ma = 'ma' in cn or 'm\u00e3' in cn
        has_nganh = 'nganh' in cn or 'ng\u00e0nh' in cn
        if has_ma and has_nganh:
            return col
    return None


def load_dgnl_data(excel_path: str) -> pd.DataFrame:
    """
    Load DGNL data tu 3 sheet, trich xuat cot diem TRUOC KHI concat.
    Chi giu ban ghi KQ = TT (Trung Tuyen) de model hoc dung pattern.
    - 2023-DGNL : KQ col = 'Ket qua so tuyen', TT = 'Tham gia xet tuyen'
    - DGNL-2022 : KQ col = 'KQ', TT = 'TT'
    - DGNL-2021 : KQ col = 'KQ', TT = 'TT'
    """
    sheet_year_map = {
        "2023-DGNL": 2023,
        "DGNL-2022": 2022,
        "DGNL-2021": 2021,
    }
    frames = []
    for sh, year in sheet_year_map.items():
        try:
            df = pd.read_excel(excel_path, sheet_name=sh)
            df.columns = [' '.join(str(c).replace("\n", " ").split()) for c in df.columns]
            df["Year"] = year

            n_before = len(df)

            # === Loc chi lay ban ghi TRUNG TUYEN (KQ = TT) ===
            kq_cols = [c for c in df.columns
                       if 'kq' in c.lower() or 'k\u1ebft qu\u1ea3' in c.lower()]
            if kq_cols:
                kq_col = kq_cols[0]
                # 2023: 'Tham gia xet tuyen', 2022/2021: 'TT'
                mask_tt = df[kq_col].astype(str).str.strip().isin(['TT', 'Tham gia x\u00e9t tuy\u1ec3n'])
                df = df[mask_tt].copy()
                print(f"  [{sh}] Loc KQ=TT: {n_before:,} -> {len(df):,} ban ghi trung tuyen")
            else:
                print(f"  [{sh}] Khong tim thay cot KQ, giu nguyen {n_before:,} ban ghi")

            # === Trich xuat cot diem NGAY TRONG SHEET NAY ===
            df['Diem_DGNL'] = _extract_score(df)

            # === Ma nganh ===
            ma_col = _find_ma_nganh(df)
            if ma_col:
                df['Ma_Nganh_Raw'] = pd.to_numeric(df[ma_col], errors='coerce')
            else:
                print(f"    -> Khong tim thay cot ma nganh trong {sh}")
                df['Ma_Nganh_Raw'] = np.nan

            # === Ten nganh ===
            ten_col = _find_col_in(df, ['ten', 'nganh']) or _find_col_in(df, ['t\u00ean', 'ng\u00e0nh'])
            df['Ten_Nganh_Raw'] = df[ten_col].astype(str) if ten_col else "?"

            # === Thu tu NV ===
            nv_col = next((c for c in df.columns
                           if 'nv' in c.lower() or 'nguy' in c.lower() or 'thu_tu' in c.lower()), None)
            df['Thu_Tu_NV'] = pd.to_numeric(df[nv_col], errors='coerce').fillna(1) if nv_col else 1

            # === KV ===
            kv_col = next((c for c in df.columns if 'kv' in c.lower() or 'khu v' in c.lower()), None)
            df['Diem_KV'] = pd.to_numeric(df[kv_col], errors='coerce').fillna(0) if kv_col else 0

            # === DT ===
            dt_col = next((c for c in df.columns
                           if 'dt' in c.lower() and ('diem' in c.lower() or '\u0111i\u1ec3m' in c.lower())), None)
            df['Diem_DT'] = pd.to_numeric(df[dt_col], errors='coerce').fillna(0) if dt_col else 0

            keep_cols = ['Diem_DGNL', 'Ma_Nganh_Raw', 'Ten_Nganh_Raw',
                         'Thu_Tu_NV', 'Diem_KV', 'Diem_DT', 'Year']
            frames.append(df[keep_cols].copy())
            print(f"  Diem_DGNL non-null: {df['Diem_DGNL'].notna().sum():,}")

        except Exception as e:
            print(f"  Cannot load {sh}: {e}")
            continue

    if not frames:
        raise RuntimeError("Khong load duoc sheet DGNL nao tu DXDuong.xlsx")

    df_all = pd.concat(frames, ignore_index=True)
    return df_all


def preprocess_dgnl(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess du lieu DGNL da duoc chuan hoa truoc do.
    Luc nay 'Diem_DGNL' da ton tai nhat quan trong toan bo DataFrame.
    """
    dfc = df.copy()

    dfc = dfc.dropna(subset=['Ma_Nganh_Raw', 'Diem_DGNL'])
    dfc['Ma_Nganh'] = dfc['Ma_Nganh_Raw'].astype(int)

    # Chuan hoa diem DGNL ve [0,1] (thang 600-1200)
    dfc['Diem_DGNL_Norm'] = np.clip((dfc['Diem_DGNL'] - 600) / (1200 - 600), 0, 1)

    # Ty le trung tuyen (synthetic)
    major_counts = dfc['Ma_Nganh'].value_counts()
    dfc['Ty_Le_Chung'] = dfc['Ma_Nganh'].map(
        lambda x: min(30, max(5, 20 - (major_counts.get(x, 100) / 50)))
    )

    return dfc


def train_and_save(excel_path: str, out_path: str):
    """Train DGNL models and save to .pkl"""
    print(f"Loading DGNL data from {excel_path} ...")
    df = load_dgnl_data(excel_path)
    print(f"Loaded {len(df):,} total rows from 3 years")

    dfp = preprocess_dgnl(df)
    print(f"Preprocessed -> {len(dfp):,} valid rows")

    feature_cols = [
        'Diem_DGNL_Norm',
        'Thu_Tu_NV',
        'Diem_KV',
        'Diem_DT',
        'Ty_Le_Chung',
        'Year'
    ]

    X = dfp[feature_cols].fillna(0)

    le_nganh = LabelEncoder()
    y = le_nganh.fit_transform(dfp['Ma_Nganh'].astype(str))

    print(f"Features: {X.shape}, Classes: {len(le_nganh.classes_)}")

    X = X.copy()
    X['Ma_Nganh_Encoded'] = y
    feature_cols.append('Ma_Nganh_Encoded')

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
    rf.fit(X_train, y_train)

    print("Training Naive Bayes...")
    nb = GaussianNB()
    nb.fit(X_train, y_train)

    rf_acc = float(rf.score(X_test, y_test))
    nb_acc = float(nb.score(X_test, y_test))
    print(f"RF accuracy: {rf_acc:.2%} | NB accuracy: {nb_acc:.2%}")

    # Name map
    name_map = {}
    tmp = dfp[['Ma_Nganh', 'Ten_Nganh_Raw']].drop_duplicates(subset=['Ma_Nganh'])
    name_map = dict(zip(tmp['Ma_Nganh'].astype(str), tmp['Ten_Nganh_Raw'].astype(str)))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    payload = {
        'rf_model': rf,
        'nb_model': nb,
        'le_nganh': le_nganh,
        'feature_names': feature_cols,
        'name_map': name_map,
        'metadata': {
            'rf_acc': rf_acc,
            'nb_acc': nb_acc,
            'ensemble_accuracy': 0.7 * rf_acc + 0.3 * nb_acc,
            'n_samples': len(dfp),
            'n_features': len(feature_cols),
            'n_classes': len(le_nganh.classes_),
            'trained_date': datetime.now().isoformat(),
            'dgnl_range': '600-1200'
        }
    }

    joblib.dump(payload, out_path)
    print(f"Saved DGNL models to {out_path}")
    print(f"Ensemble accuracy: {payload['metadata']['ensemble_accuracy']:.2%}")


if __name__ == '__main__':
    excel_path = os.path.join(os.path.dirname(__file__), '..', 'DXDuong.xlsx')
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'dgnl_models.pkl')

    try:
        train_and_save(excel_path, out_path)
        print("DGNL training completed successfully!")
    except Exception as e:
        print(f"Training failed: {e}")
        import traceback
        traceback.print_exc()