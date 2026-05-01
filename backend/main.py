# -*- coding: utf-8 -*-
"""
FastAPI Backend - Hệ thống Gợi ý Hướng nghiệp HUIT
Cổng: http://localhost:8000
Docs: http://localhost:8000/docs
"""
import sys
import os
import warnings
warnings.filterwarnings('ignore')

# Thêm thư mục gốc vào path để import các module inference
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- Import các module inference ---
from Goi_y_nganh_nghe import goi_y_nganh_simple
from Goi_y_nganh_tuyen_thang import goi_y_nganh_tuyen_thang_simple
from Goi_y_nganh_thpt import goi_y_nganh_thpt, allowed_tohops_for_group, get_group_mapping_codes
from hoc_ba_analyzer import HocBaAnalyzer, NGANH_TO_HOP, TO_HOP_MON

# Singleton HocBaAnalyzer
_hocba_analyzer = HocBaAnalyzer()

app = FastAPI(
    title="HUIT Career Advisor API",
    description="API gợi ý ngành nghề HUIT sử dụng Machine Learning (RF + Naive Bayes)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - cho phép React frontend kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== Schemas =====================

class DGNLRequest(BaseModel):
    diem_dgnl: float = Field(..., ge=600, le=1200, description="Tổng điểm DGNL (600-1200)")
    diem_dt: float = Field(0, ge=0, le=2, description="Điểm ưu tiên đối tượng")
    diem_kv: float = Field(0, ge=0, le=0.75, description="Điểm ưu tiên khu vực")
    thu_tu_nv: int = Field(1, ge=1, le=5, description="Thứ tự nguyện vọng")
    nguyen_vong: Optional[str] = Field(None, description="Nhóm ngành ưa thích")
    top_n: int = Field(10, ge=1, le=37)

class HocBaRequest(BaseModel):
    to_hop: str = Field(..., description="Tổ hợp môn (VD: D01)")
    mon1_scores: List[float] = Field(..., min_items=5, max_items=5, description="Điểm môn 1 qua 5 HK (10L→12L)")
    mon2_scores: List[float] = Field(..., min_items=5, max_items=5, description="Điểm môn 2 qua 5 HK")
    mon3_scores: List[float] = Field(..., min_items=5, max_items=5, description="Điểm môn 3 qua 5 HK")
    diem_uu_tien: float = Field(0, ge=0, le=3.5, description="Điểm ưu tiên KV+ĐT")
    nguyen_vong: Optional[str] = Field(None, description="Nhóm ngành ưa thích")
    top_n: int = Field(10, ge=1, le=37)

class TuyenThangRequest(BaseModel):
    tb_tong: float = Field(..., ge=18, le=30, description="Tổng TB 3 năm (thang 30)")
    diem_anh: float = Field(0, ge=0, le=10, description="Điểm Tiếng Anh")
    nguyen_vong: Optional[str] = Field(None, description="Nhóm ngành ưa thích (bắt buộc chọn)")
    top_n: int = Field(10, ge=1, le=37)

class THPTRequest(BaseModel):
    mon1: float = Field(..., ge=0, le=10, description="Điểm môn 1")
    mon2: float = Field(..., ge=0, le=10, description="Điểm môn 2")
    mon3: float = Field(..., ge=0, le=10, description="Điểm môn 3")
    diem_ut: float = Field(0, ge=0, le=3.5, description="Điểm ưu tiên KV+ĐT")
    thu_tu_nv: int = Field(1, ge=1, le=5)
    tohop: Optional[str] = Field(None, description="Tổ hợp xét tuyển (VD: A00, D01)")
    nguyen_vong: Optional[str] = Field(None, description="Nhóm ngành ưa thích")
    top_n: int = Field(10, ge=1, le=37)

# ===================== Endpoints =====================

@app.get("/", tags=["Root"])
def root():
    return {"message": "HUIT Career Advisor API đang hoạt động!", "docs": "/docs"}


@app.get("/api/groups", tags=["Meta"])
def get_groups():
    """Trả về 9 nhóm ngành chính thức (tên đầy đủ) với danh sách ngành"""
    groups = get_group_mapping_codes()
    result = []
    for group_name, codes in groups.items():
        # Chỉ lấy 9 tên nhóm chính thức (chứa dấu '–' em-dash)
        if '–' not in group_name:
            continue
        majors = [NGANH_TO_HOP[c]['ten_nganh'] for c in codes if c in NGANH_TO_HOP]
        result.append({
            "ten_nhom": group_name,
            "so_nganh": len(majors),
            "nganh": majors
        })
    return {"groups": result}


@app.get("/api/tohop", tags=["Meta"])
def get_tohop():
    """Trả về danh sách tất cả tổ hợp môn xét tuyển"""
    return {
        "to_hop": [
            {"ma": ma, "mon": mon}
            for ma, mon in TO_HOP_MON.items()
        ]
    }


@app.get("/api/tohop/by-group/{group_name}", tags=["Meta"])
def get_tohop_by_group(group_name: str):
    """Trả về tổ hợp môn phù hợp cho nhóm ngành đã chọn"""
    allowed = allowed_tohops_for_group(group_name)
    return {
        "group": group_name,
        "to_hop": [
            {"ma": ma, "mon": TO_HOP_MON.get(ma, [])}
            for ma in sorted(allowed)
        ]
    }


@app.post("/api/dgnl", tags=["Predict"])
def predict_dgnl(req: DGNLRequest):
    """Gợi ý ngành theo điểm DGNL (Đánh giá năng lực)"""
    try:
        results = goi_y_nganh_simple(
            diem_dgnl=req.diem_dgnl,
            diem_dt=req.diem_dt,
            diem_kv=req.diem_kv,
            thu_tu_nv=req.thu_tu_nv,
            nguyen_vong=req.nguyen_vong,
            top_n=req.top_n
        )
        return {"success": True, "phuong_thuc": "DGNL", "ket_qua": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hocba", tags=["Predict"])
def predict_hocba(req: HocBaRequest):
    """Gợi ý ngành theo điểm Học bạ THPT (5 học kỳ)"""
    if req.to_hop not in TO_HOP_MON:
        raise HTTPException(status_code=400, detail=f"Tổ hợp '{req.to_hop}' không hợp lệ.")

    try:
        diem_5_hk = {
            'mon1': req.mon1_scores,
            'mon2': req.mon2_scores,
            'mon3': req.mon3_scores,
        }

        if not _hocba_analyzer._models_loaded:
            _hocba_analyzer.load_models()

        diem_hb_info = _hocba_analyzer.tinh_diem_hoc_ba(req.to_hop, diem_5_hk)
        if diem_hb_info is None:
            raise HTTPException(status_code=400, detail="Không thể tính điểm học bạ từ dữ liệu đầu vào.")

        # Cộng điểm ưu tiên
        diem_hb_info['diem_xet_tuyen'] = diem_hb_info['diem_hb'] + req.diem_uu_tien

        results = _hocba_analyzer.predict_nganh(
            diem_hb_info, top_k=req.top_n, nguyen_vong=req.nguyen_vong or ''
        )

        return {
            "success": True,
            "phuong_thuc": "Học bạ",
            "diem_hb": diem_hb_info['diem_hb'],
            "diem_xet_tuyen": diem_hb_info['diem_xet_tuyen'],
            "diem_tb_mon": {
                "mon1": diem_hb_info['diem_tb_mon1'],
                "mon2": diem_hb_info['diem_tb_mon2'],
                "mon3": diem_hb_info['diem_tb_mon3'],
            },
            "ket_qua": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tuyenthang", tags=["Predict"])
def predict_tuyenthang(req: TuyenThangRequest):
    """Gợi ý ngành theo phương thức Tuyển thẳng (học sinh xuất sắc)"""
    try:
        results = goi_y_nganh_tuyen_thang_simple(
            tb_tong=req.tb_tong,
            diem_anh=req.diem_anh,
            nguyen_vong=req.nguyen_vong,
            top_n=req.top_n
        )
        return {"success": True, "phuong_thuc": "Tuyển thẳng", "ket_qua": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/thpt", tags=["Predict"])
def predict_thpt(req: THPTRequest):
    """Gợi ý ngành theo điểm thi THPT 2025 (Phương thức 1)"""
    try:
        results = goi_y_nganh_thpt(
            mon1=req.mon1,
            mon2=req.mon2,
            mon3=req.mon3,
            diem_ut=req.diem_ut,
            thu_tu_nv=req.thu_tu_nv,
            tohop=req.tohop,
            nguyen_vong=req.nguyen_vong,
            top_n=req.top_n
        )
        return {
            "success": True,
            "phuong_thuc": "PT1 - THPT",
            "tong_diem": req.mon1 + req.mon2 + req.mon3 + req.diem_ut,
            "ket_qua": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("🚀 Khởi động HUIT API Server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
