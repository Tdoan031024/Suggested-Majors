# -*- coding: utf-8 -*-
"""Regression/UAT smoke tests for HUIT Career Advisor AI.

This runner intentionally focuses on previously fixed production risks:
- admission score validation at inference layer
- priority-point formula and boundary behavior
- recommendation flow stability for the main user scenarios
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PASS = "[PASS]"
FAIL = "[FAIL]"

results = []


def check(tc_id, desc, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((tc_id, status, desc, detail))
    print(f"{status} [{tc_id}] {desc}" + (f" | {detail}" if detail else ""))


def is_invalid_result(result):
    if not result:
        return True
    first = result[0]
    name = str(first.get("ten_nganh", "")).lower()
    return first.get("ma_nganh") in (None, "Error") or "không hợp lệ" in name


print("\n=== 1. MODULE LOAD ===")
try:
    from huit_career_advisor.inference.dgnl import goi_y_nganh_simple, DGNL_MODELS

    check("ML-01", "DGNL module loads", True)
    check("ML-02", "DGNL model payload exists", DGNL_MODELS is not None)
except Exception as exc:
    check("ML-01", "DGNL module loads", False, str(exc))

try:
    from huit_career_advisor.inference.thpt import (
        allowed_tohops_for_group,
        calculate_priority_pt1,
        goi_y_nganh_thpt,
    )

    check("ML-03", "THPT module loads", True)
except Exception as exc:
    check("ML-03", "THPT module loads", False, str(exc))

try:
    from huit_career_advisor.inference.academic_record import HocBaAnalyzer

    hb = HocBaAnalyzer()
    check("ML-04", "HocBa module loads", True)
    check("ML-05", "HocBa model loads", hb.load_models())
except Exception as exc:
    check("ML-04", "HocBa module loads", False, str(exc))
    hb = None

try:
    from huit_career_advisor.inference.direct_admission import goi_y_nganh_tuyen_thang_simple

    check("ML-06", "TuyenThang module loads", True)
except Exception as exc:
    check("ML-06", "TuyenThang module loads", False, str(exc))

try:
    from huit_career_advisor.domain.advisory import (
        AdvisoryProfile,
        enrich_major_results,
        rank_admission_methods,
    )

    check("ML-07", "Advisory domain loads", True)
except Exception as exc:
    check("ML-07", "Advisory domain loads", False, str(exc))


print("\n=== 2. REGRESSION BUGS ===")
NHOM_1 = "Nhóm 1 (01-04)"
NHOM_2 = "Nhóm 2 (05-07)"
NO_PRIORITY = "Không ưu tiên"
CNTT_GROUP = "Công nghệ thông tin - Trí tuệ nhân tạo - Dữ liệu"

check("DG-01", "DGNL 599 is rejected", is_invalid_result(goi_y_nganh_simple(599)))
check("DG-02", "DGNL 600 is accepted as floor score", len(goi_y_nganh_simple(600)) > 0)
check("DG-03", "DGNL 1201 is rejected", is_invalid_result(goi_y_nganh_simple(1201)))
check("DG-04", "DGNL output is deterministic", [x["ma_nganh"] for x in goi_y_nganh_simple(850, top_n=5)] == [x["ma_nganh"] for x in goi_y_nganh_simple(850, top_n=5)])

check("PT-01", "Priority score below 22.5 keeps full value", calculate_priority_pt1(20, "KV1", NHOM_1) == 2.75)
check("PT-02", "Priority boundary 22.5 keeps full value", calculate_priority_pt1(22.5, "KV1", NHOM_1) == 2.75)
check("PT-03", "Priority formula above 22.5 uses divisor 7.5", calculate_priority_pt1(25, "KV1", NHOM_1) == 1.83, f"got {calculate_priority_pt1(25, 'KV1', NHOM_1)}")
check("PT-04", "Priority at max score is zero", calculate_priority_pt1(30, "KV1", NHOM_1) == 0.0)
check("PT-05", "Priority negative score is guarded", calculate_priority_pt1(-5, "KV1", NHOM_1) == 0.0)
check("PT-06", "Priority over max score is guarded", calculate_priority_pt1(31, "KV1", NHOM_1) == 0.0)
ui_groups = [
    "Công nghệ - Chế biến - Thực phẩm",
    "Kỹ thuật - Cơ khí - Tự động hóa",
    "Hóa học - Sinh học - Môi trường - Vật liệu",
    "Công nghệ thông tin - Trí tuệ nhân tạo - Dữ liệu",
    "Kinh doanh - Quản trị - Marketing",
    "Kế toán - Tài chính - Ngân hàng",
    "Logistics - Quản lý chuỗi cung ứng - Kinh doanh chuyên biệt",
    "Luật - Xã hội - Ngôn ngữ",
    "Du lịch - Nhà hàng - Khách sạn - Dịch vụ",
]
check(
    "PT-07",
    "Every UI major group resolves to admission combinations",
    all(allowed_tohops_for_group(group) for group in ui_groups),
)

check("TH-01", "THPT valid input returns recommendations", len(goi_y_nganh_thpt(8, 8, 8, tohop="A00")) > 0)
check("TH-02", "THPT subject >10 is rejected", is_invalid_result(goi_y_nganh_thpt(11, 8, 8, tohop="A00")))
check("TH-03", "THPT null score is rejected", is_invalid_result(goi_y_nganh_thpt(None, 8, 8, tohop="A00")))

check("TT-01", "TuyenThang valid score returns recommendations", len(goi_y_nganh_tuyen_thang_simple(27, 8.5)) > 0)
check("TT-02", "TuyenThang zero score is rejected", is_invalid_result(goi_y_nganh_tuyen_thang_simple(0)))
check("TT-03", "TuyenThang negative score is rejected", is_invalid_result(goi_y_nganh_tuyen_thang_simple(-5)))
check("TT-04", "TuyenThang English >10 is rejected", is_invalid_result(goi_y_nganh_tuyen_thang_simple(27, 11)))
tt_food = goi_y_nganh_tuyen_thang_simple(
    27,
    8.5,
    "Công nghệ - Chế biến - Thực phẩm",
    top_n=5,
)
check(
    "TT-05",
    "TuyenThang accepts UI dash variants for preferred group",
    bool(tt_food) and all(item.get("thuoc_nhom_mong_muon") for item in tt_food),
)

if hb:
    valid_hb = {
        "to_hop": "A00",
        "mon_hoc": ["Toán", "Lý", "Hóa"],
        "diem_tb_mon1": 8,
        "diem_tb_mon2": 8,
        "diem_tb_mon3": 8,
        "diem_hb": 24,
        "diem_xet_tuyen": 24,
    }
    check("HB-01", "HocBa priority includes bonus and caps at 3.0", hb.get_priority_points("KV1", NHOM_1, 2.0) == 3.0)
    check("HB-02", "HocBa semester score >10 is rejected", hb.tinh_diem_hoc_ba("D01", {"mon1": [11] * 5, "mon2": [8] * 5, "mon3": [8] * 5}) is None)
    check("HB-03", "HocBa valid prediction returns recommendations", len(hb.predict_nganh(valid_hb, top_k=5)) > 0)
    check("HB-04", "HocBa model-layer score >10 is rejected", is_invalid_result(hb.predict_nganh({**valid_hb, "diem_tb_mon1": 11, "diem_hb": 27, "diem_xet_tuyen": 27}, top_k=5)))
    no_group = hb.predict_nganh(valid_hb, top_k=3, nguyen_vong="")
    check("HB-05", "HocBa empty interest group is neutral enough", bool(no_group and no_group[0]["xac_suat"] >= 10), str(no_group[0] if no_group else []))


print("\n=== 3. UAT FLOWS ===")
check("UAT-01", "Only DGNL score produces major recommendations", len(goi_y_nganh_simple(850, top_n=5)) >= 3)
check("UAT-02", "Only HocBa score produces major recommendations", bool(hb and len(hb.predict_nganh(valid_hb, top_k=5)) >= 3))
check("UAT-03", "Only THPT score produces major recommendations", len(goi_y_nganh_thpt(8, 8, 8, tohop="A00", top_n=5)) >= 3)
methods = rank_admission_methods({"dgnl": 850, "hoc_ba": [8, 8, 8], "thpt": [8, 8, 8], "tuyen_thang": [8.7, 8.6, 8.8]})
check("UAT-04", "Full profile ranks admission methods", len(methods) >= 4 and sum(1 for item in methods if item.get("recommended")) == 1)
profile = AdvisoryProfile(interest_group=CNTT_GROUP)
enriched = enrich_major_results([{"ma_nganh": "7480201", "xac_suat": 80}], profile)
check("UAT-05", "AI enrichment keeps probability bounded", enriched and 0 <= enriched[0]["xac_suat"] <= 100, str(enriched[0] if enriched else []))
check("UAT-06", "Empty score profile returns no methods", rank_admission_methods({}) == [])


print("\n" + "=" * 60)
print("QA TEST SUMMARY")
print("=" * 60)
passed = sum(1 for _, status, _, _ in results if status == PASS)
failed = sum(1 for _, status, _, _ in results if status == FAIL)
print(f"Total: {len(results)} | PASS: {passed} | FAIL: {failed}")
if failed:
    print("\nFAILED CASES:")
    for tc_id, status, desc, detail in results:
        if status == FAIL:
            print(f"  - [{tc_id}] {desc}" + (f" | {detail}" if detail else ""))
    raise SystemExit(1)
