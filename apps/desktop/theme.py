"""Shared visual tokens and navigation data for the desktop application."""

LIGHT_COLORS = {
    "header_bg": "#FFFFFF",
    "sidebar_bg": "#FFFFFF",
    "sidebar_hover": "#EFF6FF",
    "sidebar_active": "#DBEAFE",
    "content_bg": "#FFFFFF",
    "card_bg": "#FFFFFF",
    "card_border": "#E5E7EB",
    "card_shadow": "#D5DCE8",
    "surface_alt": "#FFFFFF",
    "surface_hover": "#E0EAFF",
    "surface_pressed": "#CBD5E1",
    "text_dark": "#000000",
    "text_muted": "#000000",
    "text_subtle": "#000000",
    "text_light": "#000000",
    "text_header": "#000000",
    "accent": "#2563EB",
    "accent_dark": "#1D4ED8",
    "accent_hover": "#1D4ED8",
    "accent_pressed": "#1E40AF",
    "accent_soft": "#DBEAFE",
    "accent_ring": "#93C5FD",
    "ai_accent": "#7C3AED",
    "ai_soft": "#EDE9FE",
    "success": "#10B981",
    "success_light": "#D1FAE5",
    "warning": "#F59E0B",
    "warning_light": "#FEF3C7",
    "danger": "#EF4444",
    "row_even": "#FFFFFF",
    "row_odd": "#FFFFFF",
    "row_hover": "#EFF6FF",
    "row_top": "#D1FAE5",
    "row_mid": "#FEF3C7",
    "input_bg": "#FFFFFF",
    "input_focus": "#F5FAFF",
    "sep": "#E5E7EB",
    "status_bg": "#FFFFFF",
    "secondary": "#F1F5F9",
    "secondary_hover": "#E2E8F0",
    "secondary_pressed": "#CBD5E1",
    "ghost": "#00000000",
    "danger_soft": "#FFECEA",
}

DARK_COLORS = {
    "header_bg": "#0F172A",
    "sidebar_bg": "#0F172A",
    "sidebar_hover": "#1E293B",
    "sidebar_active": "#172554",
    "content_bg": "#0F172A",
    "card_bg": "#1E293B",
    "card_border": "#334155",
    "card_shadow": "#020617",
    "surface_alt": "#1E293B",
    "surface_hover": "#24324A",
    "surface_pressed": "#334155",
    "text_dark": "#F8FAFC",
    "text_muted": "#CBD5E1",
    "text_subtle": "#94A3B8",
    "text_light": "#CBD5E1",
    "text_header": "#F8FAFC",
    "accent": "#60A5FA",
    "accent_dark": "#2563EB",
    "accent_hover": "#3B82F6",
    "accent_pressed": "#2563EB",
    "accent_soft": "#1E3A8A",
    "accent_ring": "#60A5FA",
    "ai_accent": "#A78BFA",
    "ai_soft": "#312E81",
    "success": "#34D399",
    "success_light": "#064E3B",
    "warning": "#FBBF24",
    "warning_light": "#78350F",
    "danger": "#F87171",
    "row_even": "#0F172A",
    "row_odd": "#1E293B",
    "row_hover": "#1E3A8A",
    "row_top": "#064E3B",
    "row_mid": "#78350F",
    "input_bg": "#0F172A",
    "input_focus": "#172554",
    "sep": "#334155",
    "status_bg": "#0F172A",
    "secondary": "#1E293B",
    "secondary_hover": "#334155",
    "secondary_pressed": "#475569",
    "ghost": "#00000000",
    "danger_soft": "#3A1717",
}

# Mutable palette used by existing widgets. App updates it in place at runtime.
COLORS = LIGHT_COLORS.copy()


def get_theme_colors(theme_name):
    """Return a copy of the requested color palette."""
    return (DARK_COLORS if theme_name == "dark" else LIGHT_COLORS).copy()

# ── Đăng ký Font Roboto (Google Font) trên Windows ───────────────────────
import sys
from pathlib import Path

def _register_custom_fonts():
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(sys.executable).resolve().parent
        fonts_dir = base_dir / "apps" / "desktop" / "assets" / "fonts"
    else:
        fonts_dir = Path(__file__).resolve().parent / "assets" / "fonts"

    loaded = False
    if sys.platform == 'win32' and fonts_dir.exists():
        import ctypes
        try:
            for font_file in fonts_dir.glob("*.ttf"):
                path = str(font_file.resolve())
                res = ctypes.windll.gdi32.AddFontResourceW(path)
                if res > 0:
                    loaded = True
            if loaded:
                try:
                    result = ctypes.c_long()
                    ctypes.windll.user32.SendMessageTimeoutW(0xffff, 0x001d, 0, 0, 2, 100, ctypes.byref(result))
                except Exception:
                    try:
                        ctypes.windll.user32.PostMessageW(0xffff, 0x001d, 0, 0)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error loading custom fonts: {e}")
    return loaded

HAS_ROBOTO = _register_custom_fonts()
FONT_FAMILY = "Roboto" if HAS_ROBOTO else "Segoe UI"

FONTS = {
    "app_title": (FONT_FAMILY, 18, "bold"),
    "app_sub": (FONT_FAMILY, 10),
    "nav": (FONT_FAMILY, 10, "bold"),
    "section": (FONT_FAMILY, 13, "bold"),
    "label": (FONT_FAMILY, 10),
    "label_b": (FONT_FAMILY, 10, "bold"),
    "entry": (FONT_FAMILY, 10),
    "button": (FONT_FAMILY, 10, "bold"),
    "result_h": (FONT_FAMILY, 10, "bold"),
    "result": (FONT_FAMILY, 10),
    "status": (FONT_FAMILY, 9),
    "small": (FONT_FAMILY, 9),
    "small_medium": (FONT_FAMILY, 9, "bold"),
    "page_title": (FONT_FAMILY, 28, "bold"),
    "hero_title": (FONT_FAMILY, 18, "bold"),
    "metric": (FONT_FAMILY, 22, "bold"),
}

RADIUS = {
    "sm": 8,
    "md": 12,
    "lg": 18,
    "xl": 24,
}

SPACING = {
    "xs": 6,
    "sm": 10,
    "md": 16,
    "lg": 24,
    "xl": 32,
}

GROUP_OPTIONS = [
    "Công nghệ – Chế biến – Thực phẩm",
    "Kỹ thuật – Cơ khí – Tự động hóa",
    "Hóa học – Sinh học – Môi trường – Vật liệu",
    "Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu",
    "Kinh doanh – Quản trị – Marketing",
    "Kế toán – Tài chính – Ngân hàng",
    "Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt",
    "Luật – Xã hội – Ngôn ngữ",
    "Du lịch – Nhà hàng – Khách sạn – Dịch vụ",
]

NAV_ITEMS = [
    ("🏠", "Tổng quan", "Chọn phương thức phù hợp"),
    ("📊", "ĐGNL", "Đánh giá năng lực"),
    ("📚", "Học bạ", "Xét học bạ THPT"),
    ("🎯", "Tuyển thẳng", "Xét tuyển thẳng"),
    ("📝", "THPT QG", "Điểm thi THPT"),
    ("🤖", "Trợ lý AI", "Tư vấn hướng nghiệp"),
    ("⚙️", "Cài đặt", "Cấu hình hệ thống"),
]
