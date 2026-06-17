"""Model-only inference services."""

from .academic_record import HocBaAnalyzer
from .dgnl import goi_y_nganh_simple
from .direct_admission import goi_y_nganh_tuyen_thang_simple
from .thpt import goi_y_nganh_thpt

__all__ = [
    "HocBaAnalyzer",
    "goi_y_nganh_simple",
    "goi_y_nganh_thpt",
    "goi_y_nganh_tuyen_thang_simple",
]
