"""Rule-based advisory layer that complements the trained admission models.

The trained models remain responsible for academic predictions. This module
adds transparent, low-weight profile signals and compares admission methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional

from huit_career_advisor.domain.catalog import OFFICIAL_GROUP_MAPPING


NONE_OPTION = "Không có / Chưa xác định"

GEOGRAPHY_OPTIONS = [
    "Đô thị lớn",
    "Thị xã / ven đô",
    "Nông thôn",
    "Vùng xa / khó khăn",
]

ECONOMY_OPTIONS = [
    "Đa dạng",
    "Công nghiệp - sản xuất",
    "Dịch vụ - du lịch",
    "Nông nghiệp - thực phẩm",
    "Công nghệ số - thương mại",
]

PERSONALITY_OPTIONS = [
    "Phân tích - công nghệ",
    "Sáng tạo - giao tiếp",
    "Tổ chức - kinh doanh",
    "Xã hội - phục vụ cộng đồng",
    "Thực hành - kỹ thuật",
]

MOBILITY_OPTIONS = [
    "Sẵn sàng học xa nhà",
    "Ưu tiên trường trong khu vực",
    "Cần học gần nhà",
]


@dataclass(frozen=True)
class AdvisoryProfile:
    interest_group: str = ""
    family_group: str = ""
    geography: str = ""
    local_economy: str = ""
    personality: str = ""
    mobility: str = ""


def _valid_group(value: str) -> str:
    return value if value in OFFICIAL_GROUP_MAPPING else ""


def _group_for_major(major_code: str) -> str:
    code = str(major_code or "")
    for group, codes in OFFICIAL_GROUP_MAPPING.items():
        if code in codes:
            return group
    return ""


def _economy_groups(value: str) -> set[str]:
    mapping = {
        "Công nghiệp - sản xuất": {
            "Kỹ thuật – Cơ khí – Tự động hóa",
            "Hóa học – Sinh học – Môi trường – Vật liệu",
        },
        "Dịch vụ - du lịch": {
            "Du lịch – Nhà hàng – Khách sạn – Dịch vụ",
            "Luật – Xã hội – Ngôn ngữ",
        },
        "Nông nghiệp - thực phẩm": {
            "Công nghệ – Chế biến – Thực phẩm",
            "Hóa học – Sinh học – Môi trường – Vật liệu",
        },
        "Công nghệ số - thương mại": {
            "Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu",
            "Kinh doanh – Quản trị – Marketing",
            "Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt",
        },
    }
    return mapping.get(value, set())


def _personality_groups(value: str) -> set[str]:
    mapping = {
        "Phân tích - công nghệ": {
            "Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu",
            "Kế toán – Tài chính – Ngân hàng",
        },
        "Sáng tạo - giao tiếp": {
            "Kinh doanh – Quản trị – Marketing",
            "Luật – Xã hội – Ngôn ngữ",
            "Du lịch – Nhà hàng – Khách sạn – Dịch vụ",
        },
        "Tổ chức - kinh doanh": {
            "Kinh doanh – Quản trị – Marketing",
            "Kế toán – Tài chính – Ngân hàng",
            "Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt",
        },
        "Xã hội - phục vụ cộng đồng": {
            "Luật – Xã hội – Ngôn ngữ",
            "Du lịch – Nhà hàng – Khách sạn – Dịch vụ",
            "Hóa học – Sinh học – Môi trường – Vật liệu",
        },
        "Thực hành - kỹ thuật": {
            "Kỹ thuật – Cơ khí – Tự động hóa",
            "Công nghệ – Chế biến – Thực phẩm",
            "Hóa học – Sinh học – Môi trường – Vật liệu",
        },
    }
    return mapping.get(value, set())


def profile_adjustment(major_code: str, profile: AdvisoryProfile):
    """Return a small transparent adjustment and its human-readable reasons."""
    group = _group_for_major(major_code)
    if not group:
        return 0.0, []

    score = 0.0
    reasons = []
    interest = _valid_group(profile.interest_group)
    family = _valid_group(profile.family_group)

    if interest:
        if group == interest:
            score += 6.0
            reasons.append("phù hợp sở thích")
        else:
            score -= 1.5

    if family and group == family:
        score += 2.0
        reasons.append("có nền tảng nghề nghiệp gia đình")

    if group in _economy_groups(profile.local_economy):
        score += 2.0
        reasons.append("phù hợp môi trường kinh tế địa phương")

    if group in _personality_groups(profile.personality):
        score += 3.0
        reasons.append("phù hợp đặc điểm cá nhân")

    if profile.geography == "Vùng xa / khó khăn":
        if group in {
            "Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu",
            "Kế toán – Tài chính – Ngân hàng",
        }:
            score += 1.0
            reasons.append("có khả năng học tập/làm việc linh hoạt")

    return max(-4.0, min(12.0, score)), reasons


def enrich_major_results(results: Iterable[Mapping], profile: AdvisoryProfile):
    """Apply profile support scores while preserving each model's raw score."""
    enriched = []
    for result in results:
        item = dict(result)
        try:
            raw_score = float(item.get("xac_suat", 0.0))
        except (TypeError, ValueError):
            raw_score = 0.0
        adjustment, reasons = profile_adjustment(item.get("ma_nganh", ""), profile)
        item["xac_suat_goc"] = raw_score
        item["diem_ho_tro"] = adjustment
        item["xac_suat"] = round(max(0.0, min(99.0, raw_score + adjustment)), 2)
        item["ly_do_ho_tro"] = reasons
        enriched.append(item)
    enriched.sort(key=lambda item: float(item.get("xac_suat", 0.0)), reverse=True)
    return enriched


def _score_ratio(value: Optional[float], minimum: float, maximum: float):
    if value is None:
        return None
    return max(0.0, min(1.0, (value - minimum) / (maximum - minimum)))


def rank_admission_methods(scores: Mapping[str, object]):
    """Compare admission methods using normalized academic readiness."""
    methods = []

    dgnl = _as_float(scores.get("dgnl"))
    if dgnl is not None:
        ratio = _score_ratio(dgnl, 600.0, 1200.0)
        methods.append(_method_item(
            "ĐGNL",
            ratio,
            f"Điểm ĐGNL {dgnl:.0f}/1200",
            "Phù hợp khi điểm ĐGNL phản ánh tốt năng lực tổng hợp.",
        ))

    hb_scores = _float_list(scores.get("hoc_ba"), expected=3)
    if hb_scores:
        total = sum(hb_scores)
        methods.append(_method_item(
            "Học bạ",
            total / 30.0,
            f"Tổng ba môn học bạ {total:.2f}/30",
            "Có lợi thế khi kết quả học tập ổn định trong quá trình THPT.",
        ))

    thpt_scores = _float_list(scores.get("thpt"), expected=3)
    if thpt_scores:
        total = sum(thpt_scores)
        methods.append(_method_item(
            "THPT QG",
            total / 30.0,
            f"Tổng ba môn thi {total:.2f}/30",
            "Phù hợp nếu bạn có khả năng ôn tập và đạt điểm thi tập trung tốt.",
        ))

    direct_scores = _float_list(scores.get("tuyen_thang"), expected=3)
    if direct_scores:
        average = sum(direct_scores) / 3.0
        direct_ratio = average / 10.0
        reason = f"Điểm trung bình ba năm {average:.2f}/10"
        note = "Nên kiểm tra thêm thành tích/chứng chỉ theo đề án tuyển sinh."
        if average >= 8.0:
            direct_ratio = min(1.0, direct_ratio + 0.05)
            note = "Học lực ba năm tốt; cần đối chiếu thêm điều kiện thành tích/chứng chỉ."
        methods.append(_method_item("Tuyển thẳng", direct_ratio, reason, note))

    methods.sort(key=lambda item: item["score"], reverse=True)
    for index, item in enumerate(methods, 1):
        item["rank"] = index
        item["recommended"] = index == 1
    return methods


def _method_item(name: str, ratio: float, evidence: str, note: str):
    score = round(max(0.0, min(1.0, ratio)) * 100, 1)
    if score >= 80:
        level = "Rất phù hợp"
    elif score >= 65:
        level = "Phù hợp"
    elif score >= 50:
        level = "Có thể cân nhắc"
    else:
        level = "Cần cải thiện"
    return {
        "method": name,
        "score": score,
        "level": level,
        "evidence": evidence,
        "note": note,
    }


def _as_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _float_list(values, expected):
    if not isinstance(values, (list, tuple)) or len(values) != expected:
        return []
    parsed = [_as_float(value) for value in values]
    if any(value is None for value in parsed):
        return []
    return parsed


def profile_summary(profile: AdvisoryProfile):
    parts = []
    if _valid_group(profile.interest_group):
        parts.append(f"sở thích: {profile.interest_group}")
    if _valid_group(profile.family_group):
        parts.append(f"nghề gia đình: {profile.family_group}")
    if profile.geography:
        parts.append(f"khu vực sống: {profile.geography}")
    if profile.local_economy:
        parts.append(f"kinh tế địa phương: {profile.local_economy}")
    if profile.personality:
        parts.append(f"đặc điểm: {profile.personality}")
    return "; ".join(parts) if parts else "chưa có yếu tố bổ sung"
