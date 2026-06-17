# -*- coding: utf-8 -*-
"""
Đánh giá lại với Top-K Accuracy – metric phù hợp cho hệ thống gợi ý
Chạy: python topk_accuracy_evaluation.py
"""

import os, sys, time, warnings
warnings.filterwarnings('ignore')

# Cấu hình thư mục gốc
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from research.paths import DATASET_PATH
from research.training.train_hocba_models import load_hb_data, preprocess as prep_hb
from research.training.train_dgnl_models import load_dgnl_data, preprocess_dgnl as prep_dgnl
from research.training.train_thpt_models import _load_all_sheets as prep_thpt
from research.training.train_tuyenthang_models import _load_tt_sheets as prep_tt

from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Thư mục evaluation/
XLSX_PATH = str(DATASET_PATH)
OUTPUT_FILE = os.path.join(BASE_DIR, "topk_accuracy_output.txt")

_lines = []
def out(msg=""):
    print(msg)
    _lines.append(str(msg))

def topk_accuracy(model, X_test, y_test, k_list=[1,3,5,10]):
    """Tính Top-K accuracy: dự đoán đúng nếu nhãn thật nằm trong top-K dự đoán."""
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(X_test)
    else:
        return {k: float(np.mean(model.predict(X_test) == y_test)) for k in k_list}

    results = {}
    for k in k_list:
        k_eff = min(k, proba.shape[1])
        top_k_preds = np.argsort(proba, axis=1)[:, -k_eff:]
        correct = sum(y in preds for y, preds in zip(y_test, top_k_preds))
        results[k] = correct / len(y_test)
    return results

def evaluate_topk(name, model, X_tr, X_te, y_tr, y_te, dataset, split, train_time):
    topk = topk_accuracy(model, X_te, y_te, k_list=[1,3,5,10])
    topk_train = topk_accuracy(model, X_tr, y_tr, k_list=[1])

    out(f"  {'─'*60}")
    out(f"  [{dataset} | {split} | {name}]")
    out(f"  Thời gian train : {train_time:.4f}s")
    out(f"  Top-1  Accuracy : {topk[1]:.4f}  ({topk[1]*100:.2f}%)")
    out(f"  Top-3  Accuracy : {topk[3]:.4f}  ({topk[3]*100:.2f}%)  ← hệ thống gợi ý 3 ngành")
    out(f"  Top-5  Accuracy : {topk[5]:.4f}  ({topk[5]*100:.2f}%)  ← hệ thống gợi ý 5 ngành")
    out(f"  Top-10 Accuracy : {topk[10]:.4f}  ({topk[10]*100:.2f}%)  ← hệ thống gợi ý 10 ngành")
    out(f"  Train Top-1     : {topk_train[1]:.4f}")
    return {
        "dataset": dataset, "split": split, "algorithm": name,
        "train_time": round(train_time,4),
        "top1": round(topk[1],4), "top3": round(topk[3],4),
        "top5": round(topk[5],4), "top10": round(topk[10],4),
        "train_top1": round(topk_train[1],4)
    }


# ── Data loaders (Tái sử dụng logic từ các training script) ─────────────────

def prepare_hocba():
    out("Loading Học bạ from DXDuong.xlsx...")
    df = load_hb_data(XLSX_PATH)
    df = prep_hb(df)
    feature_cols = ['Diem_Mon1', 'Diem_Mon2', 'Diem_Mon3', 'Diem_HB_Tinh', 'Nam']
    X = df[feature_cols].fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(df['Ma_Nganh'].astype(str))
    return X, y, le, len(df), len(le.classes_)

def prepare_thpt():
    out("Loading THPT (PT1) from DXDuong.xlsx...")
    df = prep_thpt(XLSX_PATH)
    if df.empty: raise RuntimeError("Không load được THPT")
    le_tohop = LabelEncoder()
    df['ToHop_Enc'] = le_tohop.fit_transform(df['ToHop'].astype(str))
    features = ['Mon1', 'Mon2', 'Mon3', 'Diem_UT', 'ThuTuNV', 'ToHop_Enc', 'Year', 'Diem_Tong']
    X = df[features].astype(float).fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(df['Ma_Nganh'].astype(str))
    return X, y, le, len(df), len(le.classes_)

def prepare_dgnl():
    out("Loading DGNL from DXDuong.xlsx...")
    df = load_dgnl_data(XLSX_PATH)
    df = prep_dgnl(df)
    feature_cols = ['Diem_DGNL_Norm', 'Thu_Tu_NV', 'Diem_KV', 'Diem_DT', 'Ty_Le_Chung', 'Year']
    X = df[feature_cols].fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(df['Ma_Nganh'].astype(str))
    X = X.copy()
    X['Ma_Nganh_Encoded'] = y
    return X, y, le, len(df), len(le.classes_)

def prepare_tuyenthang():
    out("Loading Tuyển thẳng from DXDuong.xlsx...")
    df = prep_tt(XLSX_PATH)
    if df.empty: raise RuntimeError("Không load được Tuyển thẳng")
    le = LabelEncoder()
    y = le.fit_transform(df['Ma_Nganh'].astype(str))
    df['Ma_Nganh_Enc'] = y
    features = ['TB10', 'TB11', 'TBHK1_12', 'TB_total', 'UT_DT', 'UT_KV', 'EngAvg', 'Ma_Nganh_Enc', 'Year']
    X = df[features].astype(float).fillna(0)
    return X, y, le, len(df), len(le.classes_)

# -- Main --
def run_dataset(name, X, y, le, n, nc, rf_params, splits):
    results = []
    out(f"\n{'='*65}")
    out(f"  {name}  |  N={n:,}  |  Số ngành={nc}")
    out(f"{'='*65}")
    for test_sz, label in splits:
        X_tr,X_te,y_tr,y_te = train_test_split(X,y,test_size=test_sz,random_state=42)
        out(f"\n  >> Tỷ lệ {label} | Train={len(X_tr)} | Test={len(X_te)}")

        rf=RandomForestClassifier(**rf_params)
        t0=time.time(); rf.fit(X_tr,y_tr); tt=time.time()-t0
        results.append(evaluate_topk("Random Forest",rf,X_tr,X_te,y_tr,y_te,name,label,tt))

        nb=GaussianNB()
        t0=time.time(); nb.fit(X_tr,y_tr); tt=time.time()-t0
        results.append(evaluate_topk("Naive Bayes",nb,X_tr,X_te,y_tr,y_te,name,label,tt))
    return results

def main():
    out("="*65)
    out("  ĐÁNH GIÁ TOP-K ACCURACY – METRIC PHÙ HỢP CHO HỆ THỐNG GỢI Ý")
    out("  Ngày: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    out("="*65)

    splits = [(0.20,"80/20"), (0.10,"90/10")]
    all_r = []

    try:
        X,y,le,n,nc = prepare_hocba()
        all_r += run_dataset("Học bạ (HB)", X,y,le,n,nc,
                             {"n_estimators":200,"max_depth":10,"random_state":42}, splits)
    except Exception as e: out(f"❌ HB: {e}")

    try:
        X,y,le,n,nc = prepare_thpt()
        all_r += run_dataset("THPT (PT1)", X,y,le,n,nc,
                             {"n_estimators":80,"max_depth":6,"random_state":42}, splits)
    except Exception as e: out(f"❌ THPT: {e}")

    try:
        X,y,le,n,nc = prepare_dgnl()
        all_r += run_dataset("ĐGNL", X,y,le,n,nc,
                             {"n_estimators":150,"max_depth":8,"random_state":42}, splits)
    except Exception as e: out(f"❌ ĐGNL: {e}")

    try:
        X,y,le,n,nc = prepare_tuyenthang()
        all_r += run_dataset("Tuyển thẳng (TT)", X,y,le,n,nc,
                             {"n_estimators":80,"max_depth":6,"random_state":42}, splits)
    except Exception as e: out(f"❌ TT: {e}")


    # Bảng tổng hợp
    out("\n" + "="*65)
    out("  BẢNG TỔNG HỢP TOP-K ACCURACY")
    out("="*65)
    hdr = f"{'Bộ dữ liệu':<20}{'Tỷ lệ':<8}{'Thuật toán':<16}{'Top-1':>8}{'Top-3':>8}{'Top-5':>8}{'Top-10':>8}"
    out(hdr); out("-"*len(hdr))
    for r in all_r:
        out(f"{r['dataset']:<20}{r['split']:<8}{r['algorithm']:<16}"
            f"{r['top1']:>8.2%}{r['top3']:>8.2%}{r['top5']:>8.2%}{r['top10']:>8.2%}")

    out("\n" + "="*65)
    out("  HOÀN THÀNH")
    out("="*65)

    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
        f.write("\n".join(_lines))
    out(f"\n✅ Đã lưu: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
