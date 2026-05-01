# -*- coding: utf-8 -*-
"""
Script thu thập toàn bộ metrics cho Chương 4 Luận văn.
Chạy: python thu_thap_metrics_luan_van.py
Output: in ra terminal VÀ lưu file metrics_luan_van_output.txt
"""


import pandas as pd
from sklearn.preprocessing import LabelEncoder
from training.train_hocba_models import load_hb_data, preprocess as prep_hb
from training.train_dgnl_models import load_dgnl_data, preprocess_dgnl as prep_dgnl
from training.train_thpt_models import _load_all_sheets as prep_thpt
from training.train_tuyenthang_models import _load_tt_sheets as prep_tt

import os
import sys

# Cấu hình thư mục gốc (lùi 1 cấp từ evaluation/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import time
import platform
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import joblib
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_score, recall_score, f1_score
)

# ===========================================================================
# Cấu hình đường dẫn
# ===========================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # Thư mục evaluation/
XLSX_PATH = os.path.join(ROOT_DIR, "DXDuong.xlsx")
OUTPUT_FILE = os.path.join(BASE_DIR, "metrics_luan_van_output.txt")

# ===========================================================================
# Tiện ích
# ===========================================================================
_output_lines = []

def out(msg=""):
    """In ra màn hình VÀ lưu vào buffer."""
    print(msg)
    _output_lines.append(str(msg))

def save_output():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(_output_lines))
    print(f"\n✅ Đã lưu kết quả vào: {OUTPUT_FILE}")

def sep(char="=", n=70):
    out(char * n)

# ===========================================================================
# PHẦN 1: THÔNG TIN MÔI TRƯỜNG
# ===========================================================================
def print_environment_info():
    sep()
    out("PHẦN 1: THÔNG TIN MÔI TRƯỜNG HỆ THỐNG")
    sep()

    out(f"Python version     : {sys.version}")
    out(f"Platform           : {platform.platform()}")
    out(f"Processor          : {platform.processor()}")
    out(f"Machine            : {platform.machine()}")
    out(f"OS                 : {platform.system()} {platform.release()}")

    # RAM
    try:
        import psutil
        ram = psutil.virtual_memory()
        out(f"RAM total          : {ram.total / (1024**3):.2f} GB")
        out(f"RAM available      : {ram.available / (1024**3):.2f} GB")
        cpu_count = psutil.cpu_count(logical=True)
        cpu_count_phys = psutil.cpu_count(logical=False)
        out(f"CPU logical cores  : {cpu_count}")
        out(f"CPU physical cores : {cpu_count_phys}")
    except ImportError:
        out("(psutil chưa cài – RAM/CPU info không khả dụng)")

    out(f"\nThư viện chính:")
    out(f"  scikit-learn : {sklearn.__version__}")
    out(f"  pandas       : {pd.__version__}")
    out(f"  numpy        : {np.__version__}")
    out(f"  joblib       : {joblib.__version__}")

    try:
        import scipy
        out(f"  scipy        : {scipy.__version__}")
    except Exception:
        pass
    out()

# ===========================================================================
# PHẦN 2: HÀM ĐÁNH GIÁ CHUNG
# ===========================================================================
def evaluate_model(name, model, X_train, X_test, y_train, y_test,
                   dataset_name, split_label, train_time, le=None):
    """In đầy đủ metrics cho một model."""
    y_pred = model.predict(X_test)
    y_pred_train = model.predict(X_train)

    acc_test  = accuracy_score(y_test, y_pred)
    acc_train = accuracy_score(y_train, y_pred_train)
    train_err = 1 - acc_train
    test_err  = 1 - acc_test

    # Macro averages
    prec  = precision_score(y_test, y_pred, average='macro', zero_division=0)
    rec   = recall_score(y_test, y_pred, average='macro', zero_division=0)
    f1    = f1_score(y_test, y_pred, average='macro', zero_division=0)

    sep("-", 70)
    out(f"=== {dataset_name} | {split_label} | {name} ===")
    out(f"Thời gian huấn luyện : {train_time:.4f} giây")
    out(f"Accuracy (Test)      : {acc_test:.4f}  ({acc_test*100:.2f}%)")
    out(f"Accuracy (Train)     : {acc_train:.4f}  ({acc_train*100:.2f}%)")
    out(f"Train Error          : {train_err:.4f}")
    out(f"Test Error           : {test_err:.4f}")
    out(f"Precision (macro)    : {prec:.4f}")
    out(f"Recall (macro)       : {rec:.4f}")
    out(f"F1-score (macro)     : {f1:.4f}")
    out()
    out(f"Classification Report:")
    # Chỉ dùng labels có trong y_test để tránh lỗi target_names mismatch
    present_labels = sorted(np.unique(np.concatenate([y_test, y_pred])))
    if le is not None and len(present_labels) <= 60:
        target_names = [str(le.classes_[i]) for i in present_labels]
    else:
        target_names = None
    out(classification_report(y_test, y_pred, labels=present_labels,
                              target_names=target_names, digits=4, zero_division=0))
    out(f"Confusion Matrix (shape {confusion_matrix(y_test, y_pred).shape}):")
    cm = confusion_matrix(y_test, y_pred)
    out(str(cm))
    sep("-", 70)
    out()

    return {
        "dataset": dataset_name,
        "split": split_label,
        "algorithm": name,
        "train_time_s": round(train_time, 4),
        "accuracy_test": round(acc_test, 4),
        "accuracy_train": round(acc_train, 4),
        "train_error": round(train_err, 4),
        "test_error": round(test_err, 4),
        "precision_macro": round(prec, 4),
        "recall_macro": round(rec, 4),
        "f1_macro": round(f1, 4),
    }


def train_and_eval_all(dataset_name, X, y, le, model_params, splits):
    """Train RF, NB, SVM với nhiều tỷ lệ chia; trả về list dict kết quả."""
    results = []
    for test_size, label in splits:
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=None
        )
        out(f"\n>>> Tỷ lệ chia: {label} | Train: {len(X_tr)} | Test: {len(X_te)}")

        # ---- Random Forest ----
        try:
            rf_params = model_params.get("RandomForest", {})
            rf = RandomForestClassifier(**rf_params)
            t0 = time.time()
            rf.fit(X_tr, y_tr)
            rf_time = time.time() - t0
            out(f"RandomForest params: {rf_params}")
            r = evaluate_model("Random Forest", rf, X_tr, X_te, y_tr, y_te,
                                dataset_name, label, rf_time, le)
            results.append(r)
        except Exception as e:
            out(f"❌ RF error: {e}")

        # ---- Naive Bayes ----
        try:
            nb_params = model_params.get("NaiveBayes", {})
            nb = GaussianNB(**nb_params)
            t0 = time.time()
            nb.fit(X_tr, y_tr)
            nb_time = time.time() - t0
            out(f"Naive Bayes params: GaussianNB() (no hyperparams)")
            r = evaluate_model("Naive Bayes", nb, X_tr, X_te, y_tr, y_te,
                                dataset_name, label, nb_time, le)
            results.append(r)
        except Exception as e:
            out(f"❌ NB error: {e}")

        # ---- SVM ----
        try:
            svm_params = model_params.get("SVM", {"kernel": "rbf", "C": 1.0,
                                                   "gamma": "scale", "random_state": 42,
                                                   "max_iter": 2000})
            # SVM cần scale dữ liệu
            scaler = StandardScaler()
            X_tr_s = scaler.fit_transform(X_tr)
            X_te_s = scaler.transform(X_te)
            svm = SVC(**svm_params)
            t0 = time.time()
            svm.fit(X_tr_s, y_tr)
            svm_time = time.time() - t0
            out(f"SVM params: {svm_params}")
            r = evaluate_model("SVM", svm, X_tr_s, X_te_s, y_tr, y_te,
                                dataset_name, label, svm_time, le)
            results.append(r)
        except Exception as e:
            out(f"❌ SVM error: {e}")

    return results



# ===========================================================================
# PHẦN 3: DATA LOADERS (Tái sử dụng logic từ các training script)
# ===========================================================================

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


# PHẦN 4: MAIN RUNNER

def main():
    out("=" * 70)
    out("  SCRIPT THU THẬP METRICS LUẬN VĂN – HỆ THỐNG GỢI Ý NGÀNH HỌC")
    out("  Trường ĐHCN TP.HCM (HUIT) – Ngày: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    out("=" * 70)
    out()

    # ── Môi trường ──────────────────────────────────────────────────────────
    print_environment_info()

    # ── Cấu hình chia dữ liệu và model params ───────────────────────────────
    splits = [
        (0.20, "80/20"),
        (0.10, "90/10"),
    ]

    all_results = []

    # ── Tập 1: Học bạ ───────────────────────────────────────────────────────
    sep()
    out("PHẦN 2: BỘ DỮ LIỆU HỌC BẠ (HB)")
    sep()
    try:
        X_hb, y_hb, le_hb, n_hb, nc_hb = prepare_hocba()
        out(f"Tổng bản ghi    : {n_hb:,}")
        out(f"Số ngành học    : {nc_hb}")
        out(f"Features        : Diem_Mon1, Diem_Mon2, Diem_Mon3, Diem_HB_Tinh, Nam")
        out()
        model_params_hb = {
            "RandomForest": {"n_estimators": 200, "max_depth": 10, "random_state": 42},
            "NaiveBayes":   {},
            "SVM":          {"kernel": "rbf", "C": 1.0, "gamma": "scale",
                             "random_state": 42, "max_iter": 3000},
        }
        r = train_and_eval_all("Học bạ (HB)", X_hb, y_hb, le_hb, model_params_hb, splits)
        all_results.extend(r)
    except Exception as e:
        out(f"❌ Lỗi HB: {e}")
        import traceback; traceback.print_exc()

    # ── Tập 2: THPT ─────────────────────────────────────────────────────────
    sep()
    out("PHẦN 3: BỘ DỮ LIỆU THI TN THPT (PT1)")
    sep()
    try:
        X_pt, y_pt, le_pt, n_pt, nc_pt = prepare_thpt()
        out(f"Tổng bản ghi    : {n_pt:,}")
        out(f"Số ngành học    : {nc_pt}")
        out(f"Features        : Mon1, Mon2, Mon3, Diem_UT, ThuTuNV, ToHop_Enc, Year, Diem_Tong")
        out()
        model_params_pt = {
            "RandomForest": {"n_estimators": 80, "max_depth": 6, "random_state": 42},
            "NaiveBayes":   {},
            "SVM":          {"kernel": "rbf", "C": 1.0, "gamma": "scale",
                             "random_state": 42, "max_iter": 3000},
        }
        r = train_and_eval_all("THPT (PT1)", X_pt, y_pt, le_pt, model_params_pt, splits)
        all_results.extend(r)
    except Exception as e:
        out(f"❌ Lỗi THPT: {e}")
        import traceback; traceback.print_exc()

    # ── Tập 3: ĐGNL ─────────────────────────────────────────────────────────
    sep()
    out("PHẦN 4: BỘ DỮ LIỆU ĐÁNH GIÁ NĂNG LỰC (ĐGNL)")
    sep()
    try:
        X_dg, y_dg, le_dg, n_dg, nc_dg = prepare_dgnl()
        out(f"Tổng bản ghi    : {n_dg:,}")
        out(f"Số ngành học    : {nc_dg}")
        out(f"Features        : Diem_DGNL_Norm, Thu_Tu_NV, Diem_KV, Diem_DT, Ty_Le_Chung, Year, Ma_Nganh_Encoded")
        out()
        model_params_dg = {
            "RandomForest": {"n_estimators": 150, "max_depth": 8, "random_state": 42},
            "NaiveBayes":   {},
            "SVM":          {"kernel": "rbf", "C": 1.0, "gamma": "scale",
                             "random_state": 42, "max_iter": 3000},
        }
        r = train_and_eval_all("ĐGNL", X_dg, y_dg, le_dg, model_params_dg, splits)
        all_results.extend(r)
    except Exception as e:
        out(f"❌ Lỗi ĐGNL: {e}")
        import traceback; traceback.print_exc()

    # ── Tập 4: Tuyển thẳng ──────────────────────────────────────────────────
    sep()
    out("PHẦN 5: BỘ DỮ LIỆU TUYỂN THẲNG (TT)")
    sep()
    try:
        X_tt, y_tt, le_tt, n_tt, nc_tt = prepare_tuyenthang()
        out(f"Tổng bản ghi    : {n_tt:,}")
        out(f"Số ngành học    : {nc_tt}")
        out(f"Features        : TB10, TB11, TBHK1_12, TB_total, EngAvg, UT_DT, UT_KV, Year")
        out()
        model_params_tt = {
            "RandomForest": {"n_estimators": 80, "max_depth": 6, "random_state": 42},
            "NaiveBayes":   {},
            "SVM":          {"kernel": "rbf", "C": 1.0, "gamma": "scale",
                             "random_state": 42, "max_iter": 3000},
        }
        r = train_and_eval_all("Tuyển thẳng (TT)", X_tt, y_tt, le_tt, model_params_tt, splits)
        all_results.extend(r)
    except Exception as e:
        out(f"❌ Lỗi TT: {e}")
        import traceback; traceback.print_exc()

    # ── Bảng tổng hợp ────────────────────────────────────────────────────────
    sep()
    print_summary_table(all_results)

    out("=" * 70)
    out("  HOÀN THÀNH THU THẬP METRICS")
    out("=" * 70)

    save_output()


if __name__ == "__main__":
    main()
