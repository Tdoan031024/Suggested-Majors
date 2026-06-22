"""Canonical HUIT major and admission-combination catalog."""


def normalize_group_name(value: str) -> str:
    """Normalize display variants of a major-group name for matching."""
    text = str(value or "")
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    return " ".join(text.split()).casefold()


def resolve_group_key(value: str, mapping: dict) -> str | None:
    """Resolve aliases and dash variants to a canonical mapping key."""
    normalized = normalize_group_name(value)
    if not normalized:
        return None

    for key in mapping:
        if normalize_group_name(key) == normalized:
            return key

    matches = [
        key for key in mapping
        if normalized in normalize_group_name(key)
        or normalize_group_name(key) in normalized
    ]
    return max(matches, key=lambda key: len(normalize_group_name(key))) if matches else None

MAJOR_ADMISSION_COMBINATIONS = {
    "7810103": {"ten_nganh": "Quản trị dịch vụ du lịch và lữ hành", "to_hop": ["D01", "C03", "D15", "C00"]},
    "7810201": {"ten_nganh": "Quản trị khách sạn", "to_hop": ["D01", "C03", "D15", "C00"]},
    "7810202": {"ten_nganh": "Quản trị nhà hàng và dịch vụ ăn uống", "to_hop": ["D01", "C03", "D15", "C00"]},
    "7380107": {"ten_nganh": "Luật kinh tế", "to_hop": ["D01", "C03", "C14", "C00"]},
    "7220201": {"ten_nganh": "Ngôn ngữ Anh", "to_hop": ["D01", "A01", "D09", "D14"]},
    "7220204": {"ten_nganh": "Ngôn ngữ Trung Quốc", "to_hop": ["D01", "A01", "D09", "D14"]},
    "7480201": {"ten_nganh": "Công nghệ thông tin", "to_hop": ["D01", "A00", "C01", "X26"]},
    "7480202": {"ten_nganh": "An toàn thông tin", "to_hop": ["D01", "A00", "C01", "X26"]},
    "7460108": {"ten_nganh": "Khoa học dữ liệu", "to_hop": ["D01", "A00", "C01", "X26"]},
    "7340301": {"ten_nganh": "Kế toán", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7340201": {"ten_nganh": "Tài chính ngân hàng", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7340205": {"ten_nganh": "Công nghệ tài chính", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7340115": {"ten_nganh": "Marketing", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7340101": {"ten_nganh": "Quản trị kinh doanh", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7340120": {"ten_nganh": "Kinh doanh quốc tế", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7340122": {"ten_nganh": "Thương mại điện tử", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7510605": {"ten_nganh": "Logistics và quản lý chuỗi cung ứng", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7340123": {"ten_nganh": "Kinh doanh thời trang và dệt may", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7540204": {"ten_nganh": "Công nghệ dệt, may", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7510202": {"ten_nganh": "Công nghệ chế tạo máy", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7510203": {"ten_nganh": "Công nghệ kỹ thuật cơ điện tử", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7510301": {"ten_nganh": "Công nghệ kỹ thuật điện - điện tử", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7510303": {"ten_nganh": "Công nghệ kỹ thuật điều khiển và tự động hóa", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7520115": {"ten_nganh": "Kỹ thuật nhiệt", "to_hop": ["D01", "A01", "C01", "A00"]},
    "7510406": {"ten_nganh": "Công nghệ kỹ thuật môi trường", "to_hop": ["B00", "A01", "A00", "D07"]},
    "7850101": {"ten_nganh": "Quản lý tài nguyên và môi trường", "to_hop": ["B00", "A01", "A00", "D07"]},
    "7510401": {"ten_nganh": "Công nghệ kỹ thuật hóa học", "to_hop": ["B00", "B08", "A00", "D07"]},
    "7510402": {"ten_nganh": "Công nghệ vật liệu", "to_hop": ["B00", "B08", "A00", "D07"]},
    "7420201": {"ten_nganh": "Công nghệ sinh học", "to_hop": ["B00", "B08", "A00", "D07"]},
    "7540105": {"ten_nganh": "Công nghệ chế biến thủy sản", "to_hop": ["B00", "B08", "A00", "D07"]},
    "7540101": {"ten_nganh": "Công nghệ thực phẩm", "to_hop": ["B00", "B08", "A00", "D07"]},
    "7540106": {"ten_nganh": "Đảm bảo chất lượng và an toàn thực phẩm", "to_hop": ["B00", "B08", "A00", "D07"]},
    "7340129": {"ten_nganh": "Quản trị kinh doanh thực phẩm", "to_hop": ["B00", "D01", "C02", "D07"]},
    "7819009": {"ten_nganh": "Khoa học dinh dưỡng và ẩm thực", "to_hop": ["B00", "A01", "C02", "D07"]},
    "7819010": {"ten_nganh": "Khoa học chế biến món ăn", "to_hop": ["B00", "A01", "C02", "D07"]},
    "7810101": {"ten_nganh": "Du lịch", "to_hop": ["D01", "C03", "D15", "C00"]},
    "7380101": {"ten_nganh": "Luật", "to_hop": ["D01", "C03", "C14", "C00"]},
}

ADMISSION_COMBINATIONS = {
    "A00": ["Toán", "Lý", "Hóa"],
    "A01": ["Toán", "Lý", "Anh"],
    "B00": ["Toán", "Hóa", "Sinh"],
    "B08": ["Toán", "Sinh", "Anh"],
    "C00": ["Văn", "Sử", "Địa"],
    "C01": ["Văn", "Toán", "Lý"],
    "C02": ["Văn", "Toán", "Hóa"],
    "C03": ["Văn", "Toán", "Sử"],
    "C14": ["Toán", "Văn", "GDKTPL"],
    "D01": ["Toán", "Văn", "Anh"],
    "D07": ["Toán", "Hóa", "Anh"],
    "D09": ["Toán", "Sử", "Anh"],
    "D14": ["Văn", "Anh", "Sử"],
    "D15": ["Văn", "Anh", "Địa"],
    "X26": ["Toán", "Tin", "Anh"],
}

# Vietnamese aliases remain available for compatibility with existing callers.
NGANH_TO_HOP = MAJOR_ADMISSION_COMBINATIONS
TO_HOP_MON = ADMISSION_COMBINATIONS

FOOD_CODES = ["7540101", "7540106", "7540105", "7819009", "7819010", "7340129"]
ENGINEERING_CODES = ["7510202", "7510203", "7520115", "7510301", "7510303"]
CHEMISTRY_CODES = ["7510401", "7510406", "7850101", "7420201", "7510402"]
IT_CODES = ["7480201", "7480202", "7460108"]
BUSINESS_CODES = ["7340101", "7340115", "7340120", "7340122", "7340129"]
FINANCE_CODES = ["7340301", "7340201", "7340205"]
LOGISTICS_CODES = ["7510605", "7340123", "7540204"]
LAW_LANGUAGE_CODES = ["7380101", "7380107", "7220201", "7220204"]
TOURISM_CODES = ["7810101", "7810103", "7810201", "7810202"]

OFFICIAL_GROUP_MAPPING = {
    "Công nghệ – Chế biến – Thực phẩm": FOOD_CODES,
    "Kỹ thuật – Cơ khí – Tự động hóa": ENGINEERING_CODES,
    "Hóa học – Sinh học – Môi trường – Vật liệu": CHEMISTRY_CODES,
    "Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu": IT_CODES,
    "Kinh doanh – Quản trị – Marketing": BUSINESS_CODES,
    "Kế toán – Tài chính – Ngân hàng": FINANCE_CODES,
    "Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt": LOGISTICS_CODES,
    "Luật – Xã hội – Ngôn ngữ": LAW_LANGUAGE_CODES,
    "Du lịch – Nhà hàng – Khách sạn – Dịch vụ": TOURISM_CODES,
}

THPT_GROUP_MAPPING = {
    "CNTT": IT_CODES,
    "Kinh doanh": BUSINESS_CODES,
    "Kỹ thuật": ENGINEERING_CODES,
    "Thực phẩm - Môi trường": FOOD_CODES,
    "Tài chính": FINANCE_CODES,
    "Hóa sinh": CHEMISTRY_CODES,
    "Luật - Ngôn ngữ": LAW_LANGUAGE_CODES,
    "Logistics": LOGISTICS_CODES,
    "Du lịch": TOURISM_CODES,
    **OFFICIAL_GROUP_MAPPING,
}

DIRECT_ADMISSION_GROUP_MAPPING = {
    "CNTT": IT_CODES,
    "Kinh doanh": BUSINESS_CODES,
    "Kỹ thuật": ENGINEERING_CODES,
    "Thực phẩm": FOOD_CODES,
    "Tài chính": FINANCE_CODES,
    "Hóa sinh": CHEMISTRY_CODES,
    "Luật ngôn ngữ": LAW_LANGUAGE_CODES,
    "Logistics": LOGISTICS_CODES,
    "Du lịch": TOURISM_CODES,
    **OFFICIAL_GROUP_MAPPING,
}

DGNL_GROUP_MAPPING = {
    "CNTT": IT_CODES,
    "Kinh tế": BUSINESS_CODES,
    "Kỹ thuật": ENGINEERING_CODES,
    "Thực phẩm": FOOD_CODES,
    "Ngôn ngữ": ["7220201", "7220204"],
    "Luật": ["7380101", "7380107"],
    "Du lịch": TOURISM_CODES,
    "Logistics": LOGISTICS_CODES,
    "Tài chính": FINANCE_CODES,
    **OFFICIAL_GROUP_MAPPING,
}

ACADEMIC_RECORD_GROUP_MAPPING = {
    **THPT_GROUP_MAPPING,
    "CNTT": [*IT_CODES, "7340205"],
    "Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu": [*IT_CODES, "7340205"],
}
