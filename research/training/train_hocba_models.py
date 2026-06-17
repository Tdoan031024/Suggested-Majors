# -*- coding: utf-8 -*-
"""
Training script for Hoc ba (HB) method.
Reads HB-2023/HB-2022/HB-2021 from DXDuong.xlsx.
Chi lay ban ghi TRUNG TUYEN (KQ=Dau/TT) de dam bao model hoc dung pattern.
  - HB-2023: col 'KQ', gia tri 'Dau'
  - HB-2022: col 'Ket qua', gia tri 'TT'
  - HB-2021: col 'KQ', gia tri 'TT'
"""

import os
import sys
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from research.paths import DATASET_PATH, MODEL_DIR

sys.stdout.reconfigure(encoding='utf-8')


# Map (ten_sheet -> (cot_kq, [gia_tri_trung_tuyen]))
KQ_MAP = {
    "HB-2023": ("KQ", ["Đậu"]),
    "HB-2022": ("Kết quả", ["TT"]),
    "HB-2021": ("KQ", ["TT"]),
}


def load_hb_data(excel_path: str) -> pd.DataFrame:
    sheets = ["HB-2023", "HB-2022", "HB-2021"]
    frames = []
    for sh in sheets:
        df = pd.read_excel(excel_path, sheet_name=sh)
        # Chuan hoa ten cot: bo xuong dong + gop dau cach thua
        df.columns = [' '.join(str(c).replace("\n", " ").split()) for c in df.columns]
        df["Nam"] = int(sh.split("-")[1])
        n_before = len(df)

        # === Loc chi lay ban ghi Trung Tuyen ===
        kq_col_raw, tt_vals_raw = KQ_MAP.get(sh, (None, []))
        # Tim cot kq thuc te (fuzzy)
        kq_col = None
        if kq_col_raw:
            for col in df.columns:
                if col.lower().strip() == kq_col_raw.lower().strip():
                    kq_col = col
                    break
            if not kq_col:
                # fallback: partial match
                for col in df.columns:
                    if kq_col_raw.lower() in col.lower():
                        kq_col = col
                        break

        if kq_col:
            # Normalize ca gia tri TT: bo dau tieng Viet de match an toan hon
            col_vals = df[kq_col].astype(str).str.strip()
            # Build mask: khop chinh xac hoac khop unicode normalized
            import unicodedata
            def norm(s):
                return unicodedata.normalize('NFC', s).strip()
            tt_vals_norm = [norm(v) for v in tt_vals_raw]
            mask = col_vals.apply(lambda v: norm(v) in tt_vals_norm)
            df = df[mask].copy()
            print(f"  [{sh}] Loc KQ Trung Tuyen: {n_before:,} -> {len(df):,} ban ghi")
        else:
            print(f"  [{sh}] Khong tim thay col KQ '{kq_col_raw}', giu nguyen {n_before:,}")

        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def find_col(df: pd.DataFrame, keywords: list) -> str | None:
    """Tim cot chua tat ca keyword (case-insensitive, normalize spaces)."""
    for col in df.columns:
        col_norm = ' '.join(col.lower().split())
        if all(kw.lower() in col_norm for kw in keywords):
            return col
    return None


def find_ma_nganh_col(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        col_clean = ' '.join(col.lower().split())
        if ("ma" in col_clean or "m\u00e3" in col_clean) and ("nganh" in col_clean or "ng\u00e0nh" in col_clean):
            return col
    return None


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    dfc = df.copy()

    # Tim cot diem linh hoat theo keyword — ho tro ten cot khac nhau giua cac nam
    col_map = {
        'mon1_l10': find_col(dfc, ['l\u1edbp 10', 'm\u00f4n 1']),
        'mon1_l11': find_col(dfc, ['l\u1edbp 11', 'm\u00f4n 1']),
        'mon1_l12': find_col(dfc, ['l\u1edbp 12', 'm\u00f4n 1']),
        'mon2_l10': find_col(dfc, ['l\u1edbp 10', 'm\u00f4n 2']),
        'mon2_l11': find_col(dfc, ['l\u1edbp 11', 'm\u00f4n 2']),
        'mon2_l12': find_col(dfc, ['l\u1edbp 12', 'm\u00f4n 2']),
        'mon3_l10': find_col(dfc, ['l\u1edbp 10', 'm\u00f4n 3']),
        'mon3_l11': find_col(dfc, ['l\u1edbp 11', 'm\u00f4n 3']),
        'mon3_l12': find_col(dfc, ['l\u1edbp 12', 'm\u00f4n 3']),
    }

    available = [v for v in col_map.values() if v is not None]
    if not available:
        print("  Khong tim thay cot diem, bo qua batch nay")
        return pd.DataFrame()

    for col in available:
        dfc[col] = pd.to_numeric(dfc[col], errors='coerce')
    dfc = dfc.dropna(subset=available)

    def avg_cols(row, cols):
        vals = [row[c] for c in cols if c is not None and c in row.index]
        vals = [v for v in vals if pd.notna(v)]
        return sum(vals) / len(vals) if vals else None

    dfc['Diem_Mon1'] = dfc.apply(
        lambda r: avg_cols(r, [col_map['mon1_l10'], col_map['mon1_l11'], col_map['mon1_l12']]), axis=1)
    dfc['Diem_Mon2'] = dfc.apply(
        lambda r: avg_cols(r, [col_map['mon2_l10'], col_map['mon2_l11'], col_map['mon2_l12']]), axis=1)
    dfc['Diem_Mon3'] = dfc.apply(
        lambda r: avg_cols(r, [col_map['mon3_l10'], col_map['mon3_l11'], col_map['mon3_l12']]), axis=1)
    dfc['Diem_HB_Tinh'] = dfc['Diem_Mon1'] + dfc['Diem_Mon2'] + dfc['Diem_Mon3']

    ma_nganh_col = find_ma_nganh_col(dfc)
    if not ma_nganh_col:
        raise RuntimeError("Khong tim thay cot ma nganh trong du lieu HB")
    dfc['Ma_Nganh'] = pd.to_numeric(dfc[ma_nganh_col], errors='coerce')
    dfc = dfc.dropna(subset=['Ma_Nganh', 'Diem_Mon1', 'Diem_Mon2', 'Diem_Mon3'])
    dfc['Ma_Nganh'] = dfc['Ma_Nganh'].astype(int).astype(str)

    return dfc


def train_and_save(excel_path: str, out_path: str):
    print(f"Loading HB data (chi lay Trung Tuyen) from {excel_path} ...")
    df = load_hb_data(excel_path)
    print(f"Loaded {len(df):,} rows TT from 3 years")

    dfp = preprocess(df)
    print(f"Preprocessed -> {len(dfp):,} valid rows")

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
    print(f"RF acc: {rf_acc:.2%} | NB acc: {nb_acc:.2%} | N={len(dfp):,}")

    name_map = {}
    for col in dfp.columns:
        lc = ' '.join(col.lower().split())
        if 't\u00ean' in lc and 'ng\u00e0nh' in lc:
            try:
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
    print(f"Saved HB models to {out_path}")


if __name__ == "__main__":
    excel = str(DATASET_PATH)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    out = str(MODEL_DIR / "hocba_models.pkl")
    if not DATASET_PATH.exists():
        raise SystemExit(f"Khong tim thay {excel}")
    train_and_save(excel, out)
