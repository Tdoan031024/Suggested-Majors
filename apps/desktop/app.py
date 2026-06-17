#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HUIT – Hệ thống Gợi ý Ngành học
Modern Desktop GUI v2.0  (Tkinter)
"""

import sys
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.desktop.theme import (
    COLORS as C,
    FONTS as F,
    GROUP_OPTIONS,
    NAV_ITEMS,
    RADIUS,
    SPACING,
    get_theme_colors,
)

# ── Unicode fix trên Windows ───────────────────────────────────────────────
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── Import các mô-đun inference ───────────────────────────────────────────
try:
    from huit_career_advisor.inference.dgnl import goi_y_nganh_simple as dgnl_predict
except Exception:
    dgnl_predict = None

try:
    from huit_career_advisor.inference.thpt import (
        goi_y_nganh_thpt,
        allowed_tohops_for_group,
        calculate_priority_pt1,
    )
except Exception:
    goi_y_nganh_thpt = None
    allowed_tohops_for_group = lambda g: set()
    calculate_priority_pt1 = lambda total, area, subject: 0.0

try:
    from huit_career_advisor.inference.direct_admission import goi_y_nganh_tuyen_thang_simple as tt_predict
except Exception:
    tt_predict = None

try:
    from huit_career_advisor.inference.academic_record import HocBaAnalyzer, TO_HOP_MON
except Exception:
    HocBaAnalyzer = None
    TO_HOP_MON = {}

from huit_career_advisor.domain.advisory import (
    AdvisoryProfile,
    ECONOMY_OPTIONS,
    GEOGRAPHY_OPTIONS,
    MOBILITY_OPTIONS,
    NONE_OPTION,
    PERSONALITY_OPTIONS,
    enrich_major_results,
    profile_summary,
    rank_admission_methods,
)

# ══════════════════════════════════════════════════════════════════════════
#  THEME CONSTANTS
# ══════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════
#  HELPER WIDGETS
# ══════════════════════════════════════════════════════════════════════════

def rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedCard(tk.Frame):
    """Reusable rounded card with a soft depth effect."""

    def __init__(self, parent, title=None, padx=20, pady=18, radius=None, fill_key='card_bg'):
        super().__init__(parent, bg=parent.cget('bg'), highlightthickness=0, bd=0)
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._radius = radius or RADIUS['lg']
        self._fill_key = fill_key
        self._canvas = tk.Canvas(
            self,
            width=1,
            height=1,
            bg=parent.cget('bg'),
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._inner = tk.Frame(self._canvas, bg=C[self._fill_key], padx=padx, pady=pady)
        self._window = self._canvas.create_window(
            8,
            6,
            window=self._inner,
            anchor='nw',
        )
        self._canvas.bind('<Configure>', self._redraw)
        self._inner.bind('<Configure>', self._sync_height)
        if title:
            tk.Label(
                self._inner,
                text=title,
                font=F['section'],
                bg=C[self._fill_key],
                fg=C['text_dark'],
            ).pack(anchor=tk.W, pady=(0, 14))
        self.content = tk.Frame(self._inner, bg=C[self._fill_key])
        self.content.pack(fill=tk.BOTH, expand=True)
        self.content.bind('<Configure>', self._sync_height)
        self.content.grid_columnconfigure(1, weight=1)
        self.content.grid_columnconfigure(3, weight=1)
        self.after_idle(self._sync_height)

    def _sync_height(self, _event=None):
        requested = max(80, self._inner.winfo_reqheight() + 18)
        current_req = self._canvas.winfo_reqheight()
        if abs(current_req - requested) > 2:
            self.configure(height=requested)
            self._canvas.configure(height=requested)
        self._redraw()

    def _redraw(self, event=None):
        width = event.width if event else self.winfo_width()
        height = event.height if event else max(self._inner.winfo_reqheight() + 14, 80)
        self._canvas.delete('card')
        self._canvas.configure(bg=self.master.cget('bg'))
        rounded_rect(
            self._canvas,
            8,
            8,
            max(8, width - 2),
            max(8, height - 2),
            self._radius,
            fill=C['card_shadow'],
            outline='',
            tags='card',
        )
        rounded_rect(
            self._canvas,
            2,
            2,
            max(2, width - 8),
            max(2, height - 8),
            self._radius,
            fill=C[self._fill_key],
            outline='',
            tags='card',
        )
        self._canvas.tag_lower('card')
        self._canvas.itemconfigure(
            self._window,
            width=max(10, width - 20),
            height=max(10, height - 18),
        )

    def apply_theme(self):
        parent_bg = self.master.cget('bg')
        self.configure(bg=parent_bg)
        self._canvas.configure(bg=parent_bg)
        self._inner.configure(bg=C[self._fill_key])
        self.content.configure(bg=C[self._fill_key])
        self._sync_descendant_backgrounds(self._inner)
        self._redraw()

    def _sync_descendant_backgrounds(self, widget):
        fill = C[self._fill_key]
        semantic_backgrounds = {
            C['header_bg'],
            C['content_bg'],
            C['card_bg'],
            C['surface_alt'],
            C['input_bg'],
            '#ffffff',
            '#f8fafc',
            '#0f172a',
            '#1e293b',
        }
        preserve_backgrounds = {
            C['accent'],
            C['accent_soft'],
            C['ai_soft'],
            C['success_light'],
            C['warning_light'],
            C['danger_soft'],
            C['sep'],
        }
        for child in widget.winfo_children():
            if isinstance(child, (ttk.Widget, IconButton, ResultTable, MethodTable, RoundedCard)):
                continue
            if isinstance(child, tk.Canvas):
                continue
            try:
                current = str(child.cget('background')).lower()
                if current in semantic_backgrounds and current not in preserve_backgrounds:
                    child.configure(background=fill)
            except (tk.TclError, TypeError):
                pass
            self._sync_descendant_backgrounds(child)


def make_card(parent, title=None, padx=16, pady=12):
    """Return a softly elevated card and its content frame."""
    card = RoundedCard(parent, title=title, padx=padx, pady=pady + 2)
    return card, card.content


def styled_entry(parent, textvariable, width=18, **kw):
    return ttk.Entry(parent, textvariable=textvariable,
                     width=width, font=F['entry'], style='Modern.TEntry', **kw)


def styled_combo(parent, textvariable, values, width=22, state='readonly'):
    return ttk.Combobox(parent, textvariable=textvariable, values=values,
                        width=width, state=state, font=F['entry'],
                        style='Modern.TCombobox')


def label_row(parent, text, row, col=0, **kw):
    lbl = tk.Label(parent, text=text, font=F['label'],
                   bg=C['card_bg'], fg=C['text_dark'], anchor='w', **kw)
    lbl.grid(row=row, column=col, sticky='w', padx=(0, 14), pady=9)
    return lbl


def section_sep(parent, row, colspan=4):
    f = tk.Frame(parent, bg=C['sep'], height=1)
    f.grid(row=row, column=0, columnspan=colspan, sticky='ew', pady=14)
    return f


# ── Modern button with hover ──────────────────────────────────────────────
class IconButton(tk.Canvas):
    def __init__(self, parent, text, command, icon='',
                 bg=None, fg='#ffffff', hover=None, width=150,
                 variant=None, disabled=False, **kw):
        self._variant = variant or ('secondary' if bg is not None else 'primary')
        self._bg = bg or C['accent']
        self._hover = hover or C['accent_hover']
        self._pressed = C.get('accent_pressed', self._hover)
        self._fg = fg
        self._command = command
        self._width = width
        self._height = 42
        self._text = f'{icon}  {text}' if icon else text
        self._disabled = disabled
        self._has_focus = False
        super().__init__(
            parent,
            width=self._width,
            height=self._height,
            bg=parent.cget('bg'),
            highlightthickness=0,
            bd=0,
            cursor='arrow' if disabled else 'hand2',
            **kw,
        )
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<FocusIn>', self._on_focus)
        self.bind('<FocusOut>', self._on_blur)
        self.configure(takefocus=True)
        self._draw(self._bg)

    def _rounded_rect(self, color, outline=''):
        x1, y1, x2, y2, radius = 2, 2, self._width - 2, self._height - 2, RADIUS['md']
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        self.create_polygon(points, smooth=True, fill=color, outline=outline, width=2)

    def _draw(self, color):
        self.delete('all')
        outline = C['accent_ring'] if self._has_focus else ''
        self._rounded_rect(color, outline=outline)
        self.create_text(
            self._width / 2,
            self._height / 2,
            text=self._text,
            fill=C['text_subtle'] if self._disabled else self._fg,
            font=F['button'],
        )

    def _on_enter(self, _):
        if self._disabled:
            return
        self._draw(self._hover)

    def _on_leave(self, _):
        if self._disabled:
            return
        self._draw(self._bg)

    def _on_press(self, _):
        if self._disabled:
            return
        self.focus_set()
        self._draw(self._pressed)

    def _on_release(self, event):
        if self._disabled:
            return
        inside = 0 <= event.x <= self._width and 0 <= event.y <= self._height
        self._draw(self._hover if inside else self._bg)
        if inside:
            self._command()

    def _on_focus(self, _):
        self._has_focus = True
        self._draw(self._bg)

    def _on_blur(self, _):
        self._has_focus = False
        self._draw(self._bg)

    def apply_theme(self):
        if self._variant == 'secondary':
            self._bg = C['secondary']
            self._hover = C['secondary_hover']
            self._pressed = C['secondary_pressed']
            self._fg = C['text_dark']
        elif self._variant == 'danger':
            self._bg = C['danger']
            self._hover = C['danger']
            self._pressed = C['danger']
            self._fg = '#FFFFFF'
        elif self._variant == 'ghost':
            self._bg = self.master.cget('bg')
            self._hover = C['surface_hover']
            self._pressed = C['surface_pressed']
            self._fg = C['text_dark']
        else:
            self._bg = C['accent']
            self._hover = C['accent_hover']
            self._pressed = C['accent_pressed']
            self._fg = '#FFFFFF'
        self.configure(bg=self.master.cget('bg'))
        self._draw(self._bg)


# ── Results Treeview with coloured rows ───────────────────────────────────
class ResultTable(tk.Frame):
    COLS = [
        ('rank',  '#',          42,   tk.CENTER),
        ('ma',    'Mã ngành',   100,  tk.CENTER),
        ('ten',   'Tên ngành',  420,  tk.W),
        ('prob',  'Phù hợp',    90,   tk.CENTER),
        ('flags', 'Ghi chú',    210,  tk.CENTER),
    ]

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C['card_bg'], **kw)
        self._style_name = f'T{id(self)}'
        self._configure_theme()

        cols = [c[0] for c in self.COLS]
        self._tree = ttk.Treeview(
            self,
            columns=cols,
            show='headings',
            height=4,
            style=f'{self._style_name}.Treeview',
        )
        for cid, hd, w, anc in self.COLS:
            self._tree.heading(cid, text=hd)
            stretch = cid in ('ten', 'flags')
            self._tree.column(cid, width=w, minwidth=60, anchor=anc, stretch=stretch)

        vsb = ttk.Scrollbar(self, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscroll=vsb.set)
        self._tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._configure_tags()
        self.show_empty()

    def _configure_theme(self):
        s = ttk.Style()
        uid = self._style_name
        s.configure(f'{uid}.Treeview',
                    font=F['result'], rowheight=40,
                    background=C['row_odd'], fieldbackground=C['row_odd'],
                    foreground=C['text_dark'], borderwidth=0)
        s.configure(f'{uid}.Treeview.Heading',
                    font=F['result_h'],
                    background=C['surface_alt'], foreground=C['text_muted'],
                    relief='flat', padding=(10, 9))
        s.map(f'{uid}.Treeview.Heading',
              background=[('active', C['surface_alt'])])
        s.map(f'{uid}.Treeview',
              background=[('selected', C['accent_soft'])],
              foreground=[('selected', C['text_dark'])])

    def _configure_tags(self):
        self._tree.tag_configure('preferred', background=C['success_light'])
        self._tree.tag_configure('even', background=C['row_even'])
        self._tree.tag_configure('odd', background=C['row_odd'])
        self._tree.tag_configure('hover', background=C['row_hover'])
        self._tree.tag_configure('empty', foreground=C['text_muted'])

    def apply_theme(self):
        self.configure(bg=C['card_bg'])
        self._configure_theme()
        self._configure_tags()

    def populate(self, results):
        self.clear()
        if not results:
            self.show_empty('Không tìm thấy ngành phù hợp với thông tin đã nhập.')
            return
        for idx, item in enumerate(results, 1):
            ma   = item.get('ma_nganh', '')
            ten  = item.get('ten_nganh', '')
            flag_parts = []
            if item.get('to_hop_phu_hop') is True:
                flag_parts.append('✅ tổ hợp phù hợp')
            if item.get('to_hop_phu_hop') is False:
                flag_parts.append('⚠️ không mở tổ hợp')
            if item.get('thuoc_nhom_mong_muon') is True:
                flag_parts.append('🎯 thuộc nhóm')
            if item.get('thuoc_nhom_mong_muon') is False:
                flag_parts.append('📊 ngoài nhóm')
            if item.get('ghi_chu'):
                flag_parts.append(str(item['ghi_chu']))
            if item.get('thuoc_nhom_mong_muon') is True:
                tag = 'preferred'
            else:
                tag = 'even' if idx % 2 == 0 else 'odd'
            probability = item.get('xac_suat')
            probability_text = ''
            if probability is not None:
                try:
                    probability_text = f'{float(probability):.1f}%'
                except (TypeError, ValueError):
                    probability_text = str(probability)
            self._tree.insert('', tk.END,
                              values=(idx, ma, ten, probability_text,
                                      ', '.join(flag_parts)),
                              tags=(tag,))

    def clear(self):
        for iid in self._tree.get_children():
            self._tree.delete(iid)

    def show_empty(self, message='Nhập thông tin và chọn “Phân tích” để xem kết quả.'):
        self.clear()
        self._tree.insert(
            '',
            tk.END,
            values=('', '', f'  {message}', '', ''),
            tags=('empty',),
        )

    def show_loading(self):
        self.show_empty('Đang phân tích hồ sơ...')


class MethodTable(tk.Frame):
    """Compact ranking table for admission methods."""

    COLS = [
        ('rank', '#', 45, tk.CENTER),
        ('method', 'Phương thức', 130, tk.W),
        ('score', 'Mức phù hợp', 105, tk.CENTER),
        ('level', 'Đánh giá', 125, tk.CENTER),
        ('evidence', 'Căn cứ', 260, tk.W),
        ('note', 'Khuyến nghị', 330, tk.W),
    ]

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C['card_bg'], **kw)
        self._style_name = f'M{id(self)}'
        self._configure_theme()
        columns = [item[0] for item in self.COLS]
        self._tree = ttk.Treeview(
            self,
            columns=columns,
            show='headings',
            height=4,
            style=f'{self._style_name}.Treeview',
        )
        for column, heading, width, anchor in self.COLS:
            self._tree.heading(column, text=heading)
            self._tree.column(
                column,
                width=width,
                minwidth=60,
                anchor=anchor,
                stretch=column in ('evidence', 'note'),
            )
        self._tree.pack(fill=tk.BOTH, expand=True)
        self._configure_tags()

    def _configure_theme(self):
        style = ttk.Style()
        uid = self._style_name
        style.configure(
            f'{uid}.Treeview',
            font=F['result'],
            rowheight=42,
            background=C['row_odd'],
            fieldbackground=C['row_odd'],
            foreground=C['text_dark'],
            borderwidth=0,
        )
        style.configure(
            f'{uid}.Treeview.Heading',
            font=F['result_h'],
            background=C['surface_alt'],
            foreground=C['text_muted'],
            relief='flat',
            padding=(10, 9),
        )
        style.map(
            f'{uid}.Treeview',
            background=[('selected', C['accent_soft'])],
            foreground=[('selected', C['text_dark'])],
        )

    def _configure_tags(self):
        self._tree.tag_configure('recommended', background=C['success_light'])
        self._tree.tag_configure('even', background=C['row_even'])
        self._tree.tag_configure('odd', background=C['row_odd'])
        self._tree.tag_configure('hover', background=C['row_hover'])
        self._tree.tag_configure('empty', foreground=C['text_muted'])

    def populate(self, methods):
        self.clear()
        if not methods:
            self._tree.insert(
                '',
                tk.END,
                values=('', 'Chưa đủ dữ liệu', '', '', '', ''),
                tags=('empty',),
            )
            return
        for item in methods:
            tag = 'recommended' if item.get('recommended') else (
                'even' if item['rank'] % 2 == 0 else 'odd'
            )
            self._tree.insert(
                '',
                tk.END,
                values=(
                    item['rank'],
                    item['method'],
                    f"{item['score']:.1f}%",
                    item['level'],
                    item['evidence'],
                    item['note'],
                ),
                tags=(tag,),
            )

    def clear(self):
        for iid in self._tree.get_children():
            self._tree.delete(iid)

    def apply_theme(self):
        self.configure(bg=C['card_bg'])
        self._configure_theme()
        self._configure_tags()


class ScrollablePage(tk.Frame):
    """Vertically scrollable page that keeps content responsive."""

    def __init__(self, parent):
        super().__init__(parent, bg=C['content_bg'])
        self.canvas = tk.Canvas(
            self,
            bg=C['content_bg'],
            highlightthickness=0,
            bd=0,
        )
        scrollbar = ttk.Scrollbar(
            self,
            orient='vertical',
            command=self.canvas.yview,
            style='Modern.Vertical.TScrollbar',
        )
        self.content = tk.Frame(self.canvas, bg=C['content_bg'])
        self._window = self.canvas.create_window(
            (0, 0),
            window=self.content,
            anchor='nw',
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.content.bind(
            '<Configure>',
            lambda _event: self.canvas.configure(
                scrollregion=self.canvas.bbox('all')
            ),
        )
        self.canvas.bind(
            '<Configure>',
            lambda event: self.canvas.itemconfigure(
                self._window,
                width=event.width,
            ),
        )
        for widget in (self, self.canvas, self.content):
            widget.bind('<Enter>', self._bind_wheel)
            widget.bind('<Leave>', self._unbind_wheel)

    def _bind_wheel(self, _event=None):
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)

    def _unbind_wheel(self, _event=None):
        self.canvas.unbind_all('<MouseWheel>')

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), 'units')

    def apply_theme(self):
        self.configure(bg=C['content_bg'])
        self.canvas.configure(bg=C['content_bg'])
        self.content.configure(bg=C['content_bg'])


# ══════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════

class App(tk.Tk):

    def __init__(self):
        if sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    'HUIT.CareerAdvisor.Desktop.v2'
                )
            except (AttributeError, OSError):
                pass
        super().__init__()
        self._theme_name = self._load_theme_preference()
        C.clear()
        C.update(get_theme_colors(self._theme_name))
        self._palette_snapshot = C.copy()
        self.title('HUIT – Hệ thống Gợi ý Ngành học')
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        icon_path = os.path.join(assets_dir, 'app_icon.ico')
        logo_path = os.path.join(assets_dir, 'app_logo.png')
        self._window_icon = None
        if os.path.exists(logo_path):
            try:
                self._window_icon = tk.PhotoImage(file=logo_path)
                self.iconphoto(True, self._window_icon)
            except tk.TclError:
                pass
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except tk.TclError:
                pass
        self.geometry('1360x880')
        self.minsize(1040, 740)
        self.configure(bg=C['content_bg'])
        self._apply_global_style()
        self._sidebar_collapsed = False
        self._sidebar_width_expanded = 260
        self._sidebar_width_collapsed = 78
        self._current_page = tk.StringVar(value='Tổng quan')
        self._status_var   = tk.StringVar(value='Sẵn sàng')
        self._init_advisory_profile()
        self._clock_job = None
        self._startup_job = None
        self._build_layout()
        self.bind('<Control-Shift-T>', lambda _event: self._toggle_theme())
        self.update_idletasks()
        self._apply_windows_titlebar()
        self._center_window()
        self._startup_job = self.after(
            150,
            lambda: self._show_page('Tổng quan'),
        )

    def _init_advisory_profile(self):
        self.profile_interest = tk.StringVar(value=NONE_OPTION)
        self.profile_family = tk.StringVar(value=NONE_OPTION)
        self.profile_geography = tk.StringVar(value=GEOGRAPHY_OPTIONS[0])
        self.profile_economy = tk.StringVar(value=ECONOMY_OPTIONS[0])
        self.profile_personality = tk.StringVar(value=PERSONALITY_OPTIONS[0])
        self.profile_mobility = tk.StringVar(value=MOBILITY_OPTIONS[0])
        self._profile_summary_var = tk.StringVar()
        for variable in (
            self.profile_interest,
            self.profile_family,
            self.profile_geography,
            self.profile_economy,
            self.profile_personality,
            self.profile_mobility,
        ):
            variable.trace_add('write', self._update_profile_summary)
        self._update_profile_summary()

    def _current_profile(self):
        return AdvisoryProfile(
            interest_group=self.profile_interest.get(),
            family_group=self.profile_family.get(),
            geography=self.profile_geography.get(),
            local_economy=self.profile_economy.get(),
            personality=self.profile_personality.get(),
            mobility=self.profile_mobility.get(),
        )

    def _update_profile_summary(self, *_):
        self._profile_summary_var.set(
            'Hồ sơ hỗ trợ: ' + profile_summary(self._current_profile())
        )

    @staticmethod
    def _settings_path():
        base = os.environ.get('APPDATA')
        settings_dir = Path(base) / 'HUITCareerAdvisor' if base else (
            Path.home() / '.huit-career-advisor'
        )
        return settings_dir / 'settings.json'

    def _load_theme_preference(self):
        try:
            data = json.loads(self._settings_path().read_text(encoding='utf-8'))
            if data.get('theme') in ('light', 'dark'):
                return data['theme']
        except (OSError, ValueError, TypeError):
            pass
        return 'light'

    def _save_theme_preference(self):
        try:
            path = self._settings_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({'theme': self._theme_name}, ensure_ascii=False),
                encoding='utf-8',
            )
        except OSError:
            pass

    def _center_window(self):
        width = self.winfo_width()
        height = self.winfo_height()
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    # ── Global ttk style ──────────────────────────────────────────────────
    def _apply_global_style(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('TFrame',    background=C['content_bg'])
        s.configure('TLabel',    background=C['content_bg'],
                                 foreground=C['text_dark'], font=F['label'])
        s.configure('Modern.TEntry', fieldbackground=C['input_bg'],
                    foreground=C['text_dark'], bordercolor=C['card_border'],
                    lightcolor=C['card_border'], darkcolor=C['card_border'],
                    borderwidth=1, relief='flat', padding=(12, 10))
        s.map('Modern.TEntry',
              fieldbackground=[('focus', C['input_focus'])],
              bordercolor=[('focus', C['accent'])],
              lightcolor=[('focus', C['accent'])],
              darkcolor=[('focus', C['accent'])])
        s.configure('Invalid.TEntry', fieldbackground=C['input_bg'],
                    foreground=C['text_dark'], bordercolor=C['danger'],
                    lightcolor=C['danger'], darkcolor=C['danger'],
                    borderwidth=1, relief='flat', padding=(12, 10))
        s.configure('Success.TEntry', fieldbackground=C['input_bg'],
                    foreground=C['text_dark'], bordercolor=C['success'],
                    lightcolor=C['success'], darkcolor=C['success'],
                    borderwidth=1, relief='flat', padding=(12, 10))
        s.configure('Modern.TCombobox', fieldbackground=C['input_bg'],
                    background=C['input_bg'], foreground=C['text_dark'],
                    bordercolor=C['card_border'], lightcolor=C['card_border'],
                    darkcolor=C['card_border'], arrowcolor=C['accent'],
                    borderwidth=1, relief='flat', padding=(10, 9))
        s.map('Modern.TCombobox',
              fieldbackground=[('readonly', C['input_bg']),
                               ('focus', C['input_focus'])],
              bordercolor=[('focus', C['accent'])])
        s.configure('Invalid.TCombobox', fieldbackground=C['input_bg'],
                    background=C['input_bg'], foreground=C['text_dark'],
                    bordercolor=C['danger'], lightcolor=C['danger'],
                    darkcolor=C['danger'], arrowcolor=C['danger'],
                    borderwidth=1, relief='flat', padding=(10, 9))
        s.configure('TRadiobutton', background=C['card_bg'],
                                    foreground=C['text_dark'], font=F['label'])
        s.map('TRadiobutton', background=[('active', C['card_bg'])],
              foreground=[('active', C['text_dark'])])
        s.configure('TScrollbar', background=C['surface_alt'],
                                  troughcolor=C['content_bg'],
                                  arrowcolor=C['text_muted'],
                                  bordercolor=C['content_bg'],
                                  lightcolor=C['content_bg'],
                                  darkcolor=C['content_bg'])
        s.configure('Modern.Vertical.TScrollbar',
                    gripcount=0,
                    background=C['surface_hover'],
                    troughcolor=C['content_bg'],
                    arrowcolor=C['text_subtle'],
                    bordercolor=C['content_bg'],
                    lightcolor=C['content_bg'],
                    darkcolor=C['content_bg'],
                    width=10)
        self.option_add('*TCombobox*Listbox.background', C['input_bg'])
        self.option_add('*TCombobox*Listbox.foreground', C['text_dark'])
        self.option_add('*TCombobox*Listbox.selectBackground', C['accent'])
        self.option_add('*TCombobox*Listbox.selectForeground', '#FFFFFF')

    # ── Layout skeleton ───────────────────────────────────────────────────
    def _build_layout(self):
        self._build_header()
        self._build_statusbar()
        body = tk.Frame(self, bg=C['content_bg'])
        body.pack(fill=tk.BOTH, expand=True)
        self._build_sidebar(body)
        self._content_host = tk.Frame(body, bg=C['content_bg'])
        self._content_host.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                                padx=(30, 34), pady=(26, 30))
        self._pages = {}
        self._build_page_overview()
        self._build_page_dgnl()
        self._build_page_hocba()
        self._build_page_tuyenthang()
        self._build_page_pt1()
        self._build_page_chat()

    # ── Header ────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=C['header_bg'], height=86)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        brand = tk.Frame(hdr, bg=C['header_bg'], width=52, height=52)
        brand.pack(side=tk.LEFT, padx=(26, 16), pady=17)
        brand.pack_propagate(False)
        header_logo_path = os.path.join(
            os.path.dirname(__file__), 'assets', 'app_logo_header.png'
        )
        self._header_logo = None
        if os.path.exists(header_logo_path):
            try:
                self._header_logo = tk.PhotoImage(file=header_logo_path)
            except tk.TclError:
                pass
        if self._header_logo is not None:
            tk.Label(
                brand,
                image=self._header_logo,
                bg=C['header_bg'],
                bd=0,
            ).pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(brand, text='H', font=('Segoe UI', 16, 'bold'),
                     bg=C['accent'], fg='#FFFFFF').pack(fill=tk.BOTH, expand=True)

        info = tk.Frame(hdr, bg=C['header_bg'])
        info.pack(side=tk.LEFT)
        tk.Label(info, text='HUIT Career Advisor AI', font=F['app_title'],
                 bg=C['header_bg'], fg=C['text_header']).pack(anchor=tk.W, pady=(18, 0))
        tk.Label(info,
                 text='Trợ lý hướng nghiệp thông minh cho học sinh THPT',
                 font=F['app_sub'], bg=C['header_bg'], fg=C['text_muted']).pack(anchor=tk.W)

        self._clock_var = tk.StringVar()
        avatar = tk.Frame(hdr, bg=C['accent_soft'], width=38, height=38)
        avatar.pack(side=tk.RIGHT, padx=(10, 24))
        avatar.pack_propagate(False)
        tk.Label(
            avatar,
            text='HS',
            bg=C['accent_soft'],
            fg=C['accent'],
            font=F['small_medium'],
        ).pack(fill=tk.BOTH, expand=True)

        clock = tk.Frame(hdr, bg=C['surface_alt'], padx=14, pady=8)
        clock.pack(side=tk.RIGHT, padx=(10, 24))
        tk.Label(clock, textvariable=self._clock_var,
                 font=F['small'], bg=C['surface_alt'], fg=C['text_muted']).pack()
        self._build_theme_toggle(hdr)
        self._tick()

    def _build_theme_toggle(self, parent):
        self._theme_toggle = tk.Frame(
            parent,
            bg=C['surface_alt'],
            padx=14,
            pady=8,
            cursor='hand2',
        )
        self._theme_toggle.pack(side=tk.RIGHT, padx=(0, 4))
        self._theme_toggle_label = tk.Label(
            self._theme_toggle,
            bg=C['surface_alt'],
            fg=C['text_dark'],
            font=F['small_medium'],
            cursor='hand2',
        )
        self._theme_toggle_label.pack()
        self._update_theme_toggle_text()

        def enter(_event=None):
            for widget in (self._theme_toggle, self._theme_toggle_label):
                widget.configure(bg=C['sidebar_hover'])

        def leave(_event=None):
            for widget in (self._theme_toggle, self._theme_toggle_label):
                widget.configure(bg=C['surface_alt'])

        for widget in (self._theme_toggle, self._theme_toggle_label):
            widget.bind('<Button-1>', lambda _event: self._toggle_theme())
            widget.bind('<Enter>', enter)
            widget.bind('<Leave>', leave)

    def _update_theme_toggle_text(self):
        if hasattr(self, '_theme_toggle_label'):
            text = '☀  Sáng' if self._theme_name == 'dark' else (
                '🌙  Tối'
            )
            self._theme_toggle_label.configure(text=text)

    def _toggle_theme(self):
        self._theme_name = 'dark' if self._theme_name == 'light' else 'light'
        self._apply_theme()
        self._save_theme_preference()

    def _apply_theme(self):
        old_palette = self._palette_snapshot
        new_palette = get_theme_colors(self._theme_name)
        color_map = {}
        for key, old_color in old_palette.items():
            color_map.setdefault(old_color.lower(), new_palette[key])

        C.clear()
        C.update(new_palette)
        self._palette_snapshot = new_palette.copy()
        self.configure(bg=C['content_bg'])
        self._apply_global_style()
        self._recolor_widget_tree(self, color_map)

        for widget in self.winfo_children():
            self._apply_component_theme(widget)

        self._style_chat_widgets()
        self._update_theme_toggle_text()
        if hasattr(self, '_nav_btns'):
            if hasattr(self, '_sidebar'):
                self._sidebar.configure(bg=C['sidebar_bg'])
            for attr in ('_sidebar_menu_label', '_sidebar_footer_label'):
                label = getattr(self, attr, None)
                if label is not None:
                    label.configure(bg=C['sidebar_bg'], fg=C['text_muted'])
            sep = getattr(self, '_sidebar_footer_sep', None)
            if sep is not None:
                sep.configure(bg=C['card_border'])
            self._draw_sidebar_toggle()
            for title, item in self._nav_btns.items():
                self._draw_nav_item(item, title == self._current_page.get())
        self._show_page(self._current_page.get())
        self.update_idletasks()
        self._apply_windows_titlebar()

    def _recolor_widget_tree(self, widget, color_map):
        if not isinstance(widget, ttk.Widget):
            for option in (
                'background',
                'foreground',
                'activebackground',
                'activeforeground',
                'highlightbackground',
                'highlightcolor',
            ):
                try:
                    current = str(widget.cget(option)).lower()
                    if current in color_map:
                        widget.configure(**{option: color_map[current]})
                except (tk.TclError, TypeError):
                    pass
        for child in widget.winfo_children():
            self._recolor_widget_tree(child, color_map)

    def _apply_component_theme(self, widget):
        if isinstance(widget, IconButton):
            widget.apply_theme()
        elif isinstance(widget, ResultTable):
            widget.apply_theme()
        elif isinstance(widget, MethodTable):
            widget.apply_theme()
        elif isinstance(widget, ScrollablePage):
            widget.apply_theme()
        elif isinstance(widget, RoundedCard):
            widget.apply_theme()
        for child in widget.winfo_children():
            self._apply_component_theme(child)

    def _style_chat_widgets(self):
        if not hasattr(self, 'chat_log'):
            return
        try:
            self.chat_log.configure(
                bg=C['input_bg'],
                fg=C['text_dark'],
                insertbackground=C['accent'],
                selectbackground=C['accent_soft'],
                selectforeground=C['text_dark'],
            )
            self.chat_log.tag_configure(
                'student_tag', font=F['label_b'], foreground=C['accent'])
            self.chat_log.tag_configure(
                'student_msg', font=F['label'], foreground=C['text_dark'],
                lmargin1=110, rmargin=12, spacing1=3, spacing3=8)
            self.chat_log.tag_configure(
                'ai_tag', font=F['label_b'], foreground=C['success'])
            self.chat_log.tag_configure(
                'ai_msg', font=F['label'], foreground=C['text_dark'],
                lmargin1=12, rmargin=110, spacing1=3, spacing3=8)
            self.chat_log.tag_configure(
                'system_card', font=F['result'], foreground=C['text_muted'],
                background=C['surface_alt'], lmargin1=24, rmargin=24,
                spacing1=6, spacing3=6)
        except tk.TclError:
            pass

    def _apply_windows_titlebar(self):
        if sys.platform != 'win32':
            return
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            enabled = ctypes.c_int(1 if self._theme_name == 'dark' else 0)
            for attribute in (20, 19):
                result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    attribute,
                    ctypes.byref(enabled),
                    ctypes.sizeof(enabled),
                )
                if result == 0:
                    break
        except (AttributeError, OSError):
            pass

    def _tick(self):
        self._clock_var.set(datetime.now().strftime('%H:%M:%S  |  %d/%m/%Y'))
        self._clock_job = self.after(1000, self._tick)

    def destroy(self):
        for job_name in ('_clock_job', '_startup_job'):
            job = getattr(self, job_name, None)
            if job is None:
                continue
            try:
                self.after_cancel(job)
            except tk.TclError:
                pass
            setattr(self, job_name, None)
        super().destroy()

    # ── Sidebar ───────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C['sidebar_bg'], width=self._sidebar_width_expanded)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)
        self._sidebar = sb

        top = tk.Frame(sb, bg=C['sidebar_bg'])
        top.pack(fill=tk.X, padx=14, pady=(22, 12))
        self._sidebar_menu_label = tk.Label(
            top,
            text='MENU CHÍNH',
            font=('Segoe UI', 8, 'bold'),
            bg=C['sidebar_bg'],
            fg=C['text_muted'],
        )
        self._sidebar_menu_label.pack(side=tk.LEFT, padx=(10, 0))
        self._sidebar_toggle = self._make_sidebar_toggle(top)
        self._sidebar_toggle.pack(side=tk.RIGHT)

        self._nav_btns = {}
        for icon, title, sub in NAV_ITEMS:
            self._nav_btns[title] = self._make_nav_btn(sb, icon, title, sub)

        self._sidebar_footer_sep = tk.Frame(sb, bg=C['card_border'], height=1)
        self._sidebar_footer_sep.pack(fill=tk.X, padx=22, pady=18)
        self._sidebar_footer_label = tk.Label(
            sb,
            text='HUIT Career Advisor  ·  v2.0',
            font=('Segoe UI', 8),
            bg=C['sidebar_bg'],
            fg=C['text_muted'],
        )
        self._sidebar_footer_label.pack(anchor=tk.W, padx=24)

    def _make_sidebar_toggle(self, parent):
        canvas = tk.Canvas(
            parent,
            width=36,
            height=34,
            bg=C['sidebar_bg'],
            highlightthickness=0,
            bd=0,
            cursor='hand2',
        )
        data = {'canvas': canvas, 'hover': False}

        def enter(_=None):
            data['hover'] = True
            self._draw_sidebar_toggle(data)

        def leave(_=None):
            data['hover'] = False
            self._draw_sidebar_toggle(data)

        canvas.bind('<Button-1>', lambda _event: self._toggle_sidebar())
        canvas.bind('<Enter>', enter)
        canvas.bind('<Leave>', leave)
        canvas.bind('<Configure>', lambda _event: self._draw_sidebar_toggle(data))
        self._sidebar_toggle_data = data
        self._draw_sidebar_toggle(data)
        return canvas

    def _draw_sidebar_toggle(self, data=None):
        data = data or getattr(self, '_sidebar_toggle_data', None)
        if not data:
            return
        canvas = data['canvas']
        canvas.delete('all')
        canvas.configure(bg=C['sidebar_bg'])
        fill = C['sidebar_hover'] if data.get('hover') else C['surface_alt']
        rounded_rect(canvas, 1, 1, 35, 33, RADIUS['md'], fill=fill, outline='')
        arrow = '›' if self._sidebar_collapsed else '‹'
        canvas.create_text(
            18,
            16,
            text=arrow,
            fill=C['accent'],
            font=('Segoe UI', 18, 'bold'),
        )

    def _toggle_sidebar(self):
        self._sidebar_collapsed = not self._sidebar_collapsed
        self._apply_sidebar_state()

    def _apply_sidebar_state(self):
        width = (
            self._sidebar_width_collapsed
            if self._sidebar_collapsed
            else self._sidebar_width_expanded
        )
        self._sidebar.configure(width=width)

        if self._sidebar_collapsed:
            self._sidebar_menu_label.pack_forget()
            self._sidebar_footer_sep.pack_forget()
            self._sidebar_footer_label.pack_forget()
            self._sidebar_toggle.pack_configure(side=tk.TOP, pady=(0, 8))
        else:
            if not self._sidebar_menu_label.winfo_ismapped():
                self._sidebar_menu_label.pack(side=tk.LEFT, padx=(10, 0))
            if not self._sidebar_footer_sep.winfo_ismapped():
                self._sidebar_footer_sep.pack(fill=tk.X, padx=22, pady=18)
            if not self._sidebar_footer_label.winfo_ismapped():
                self._sidebar_footer_label.pack(anchor=tk.W, padx=24)
            self._sidebar_toggle.pack_configure(side=tk.RIGHT, pady=0)

        for title, item in self._nav_btns.items():
            padx = 10 if self._sidebar_collapsed else 12
            item['canvas'].pack_configure(padx=padx, pady=5)
            self._draw_nav_item(item, title == self._current_page.get())
        self._draw_sidebar_toggle()

    def _make_nav_btn(self, parent, icon, title, subtitle):
        canvas = tk.Canvas(
            parent,
            height=66,
            bg=C['sidebar_bg'],
            highlightthickness=0,
            bd=0,
            cursor='hand2',
        )
        canvas.pack(fill=tk.X, padx=12, pady=4)
        data = {
            'canvas': canvas,
            'icon': icon,
            'title': title,
            'subtitle': subtitle,
            'hover': False,
        }

        def _click(_=None):
            self._show_page(title)

        def _enter(_=None):
            data['hover'] = True
            self._draw_nav_item(data, self._current_page.get() == title)

        def _leave(_=None):
            data['hover'] = False
            self._draw_nav_item(data, self._current_page.get() == title)

        canvas.bind('<Button-1>', _click)
        canvas.bind('<Enter>', _enter)
        canvas.bind('<Leave>', _leave)
        canvas.bind('<Configure>', lambda _event: self._draw_nav_item(
            data, self._current_page.get() == title))
        self._draw_nav_item(data, False)
        return data

    def _draw_nav_item(self, item, active=False):
        canvas = item['canvas']
        collapsed = self._sidebar_collapsed
        width = max(canvas.winfo_width(), 54 if collapsed else 220)
        height = 66
        canvas.delete('all')
        canvas.configure(bg=C['sidebar_bg'])
        fill = C['sidebar_active'] if active else (
            C['sidebar_hover'] if item.get('hover') else C['sidebar_bg']
        )
        x1 = 2 if collapsed else 0
        x2 = width - 2 if collapsed else width - 1
        rounded_rect(
            canvas,
            x1,
            2,
            x2,
            height - 2,
            RADIUS['md'],
            fill=fill,
            outline=C['accent_ring'] if item.get('hover') and not active else '',
        )
        if active:
            rounded_rect(
                canvas,
                0 if not collapsed else 3,
                12,
                5 if not collapsed else 8,
                height - 12,
                3,
                fill=C['accent'],
                outline='',
            )

        if collapsed:
            icon_fill = C['accent_soft'] if active or item.get('hover') else C['surface_alt']
            rounded_rect(
                canvas,
                14,
                13,
                width - 14,
                height - 13,
                RADIUS['sm'],
                fill=icon_fill,
                outline='',
            )
            canvas.create_text(
                width // 2,
                height // 2,
                text=item['icon'],
                fill=C['accent'],
                font=('Segoe UI Emoji', 18),
            )
            if active:
                canvas.create_oval(
                    width // 2 - 3,
                    height - 9,
                    width // 2 + 3,
                    height - 3,
                    fill=C['accent'],
                    outline='',
                )
            return

        if not active and not item.get('hover'):
            canvas.create_line(
                22,
                height - 1,
                width - 22,
                height - 1,
                fill=C['sep'],
            )

        rounded_rect(
            canvas,
            18,
            17,
            48,
            49,
            RADIUS['sm'],
            fill=C['accent_soft'] if active or item.get('hover') else C['surface_alt'],
            outline='',
        )
        canvas.create_text(
            33,
            33,
            text=item['icon'],
            fill=C['accent'],
            font=('Segoe UI Emoji', 17),
        )
        canvas.create_text(
            66,
            24,
            text=item['title'],
            fill=C['accent'] if active else C['text_dark'],
            font=F['nav'],
            anchor='w',
        )
        canvas.create_text(
            66,
            44,
            text=item['subtitle'],
            fill=C['text_muted'],
            font=('Segoe UI', 8),
            anchor='w',
        )
        if active:
            canvas.create_text(
                width - 22,
                33,
                text='•',
                fill=C['accent'],
                font=('Segoe UI', 18, 'bold'),
            )

    def _show_page(self, name):
        prev = self._current_page.get()
        # Deactivate previous
        if prev in self._nav_btns:
            b = self._nav_btns[prev]
            self._draw_nav_item(b, False)
        # Activate new
        self._current_page.set(name)
        if name in self._nav_btns:
            b = self._nav_btns[name]
            self._draw_nav_item(b, True)
        # Swap page frames
        for pname, pframe in self._pages.items():
            if pname == name:
                pframe.pack(fill=tk.BOTH, expand=True)
            else:
                pframe.pack_forget()
        self._set_status(f'Đang sử dụng phương thức: {name}')

    # ── Status bar ────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=C['status_bg'], height=30)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)
        tk.Label(bar, text='●', font=('Segoe UI', 8),
                 bg=C['status_bg'], fg=C['success']).pack(side=tk.LEFT, padx=(18, 5))
        tk.Label(bar, textvariable=self._status_var,
                 font=F['status'], bg=C['status_bg'], fg=C['text_muted'],
                 anchor='w').pack(side=tk.LEFT)
        tk.Label(bar, text='HUIT AI Advisory System',
                 font=F['status'], bg=C['status_bg'], fg=C['text_muted']).pack(
            side=tk.RIGHT, padx=18)

    def _set_status(self, msg):
        self._status_var.set(f'  {msg}')

    # ── Page title helper ─────────────────────────────────────────────────
    @staticmethod
    def _page_title(parent, title, sub=''):
        hdr = tk.Frame(parent, bg=C['content_bg'])
        hdr.pack(fill=tk.X, pady=(0, 20))
        tk.Label(hdr, text=title, font=F['page_title'],
                 bg=C['content_bg'], fg=C['text_dark']).pack(anchor=tk.W)
        if sub:
            tk.Label(hdr, text=sub, font=F['small'],
                     bg=C['content_bg'], fg=C['text_muted']).pack(anchor=tk.W, pady=(5, 0))

    def _build_profile_fields(self, parent, start_row=0):
        group_values = [NONE_OPTION] + GROUP_OPTIONS
        fields = [
            ('Sở thích cá nhân:', self.profile_interest, group_values, 0, 0, 34),
            ('Nghề nghiệp gia đình:', self.profile_family, group_values, 0, 2, 34),
            ('Nơi sinh sống:', self.profile_geography, GEOGRAPHY_OPTIONS, 1, 0, 24),
            ('Kinh tế địa phương:', self.profile_economy, ECONOMY_OPTIONS, 1, 2, 27),
            ('Đặc điểm cá nhân:', self.profile_personality, PERSONALITY_OPTIONS, 2, 0, 24),
            ('Điều kiện học xa:', self.profile_mobility, MOBILITY_OPTIONS, 2, 2, 27),
        ]
        for label, variable, values, row, column, width in fields:
            label_row(parent, label, start_row + row, col=column)
            styled_combo(
                parent,
                variable,
                values,
                width=width,
            ).grid(
                row=start_row + row,
                column=column + 1,
                sticky='ew',
                padx=(0, 14) if column == 0 else 0,
                pady=4,
            )
        return start_row + 3

    def _build_profile_strip(self, parent):
        strip = tk.Frame(parent, bg=C['accent_soft'], padx=12, pady=9)
        strip.pack(fill=tk.X, pady=(0, 10))
        tk.Label(
            strip,
            textvariable=self._profile_summary_var,
            bg=C['accent_soft'],
            fg=C['text_dark'],
            font=F['small'],
            anchor='w',
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        edit = tk.Label(
            strip,
            text='Chỉnh sửa hồ sơ',
            bg=C['accent_soft'],
            fg=C['accent'],
            font=F['small_medium'] if 'small_medium' in F else F['small'],
            cursor='hand2',
        )
        edit.pack(side=tk.RIGHT)
        edit.bind('<Button-1>', lambda _event: self._open_profile_dialog())

    def _build_method_page_hero(self, parent, icon, title, subtitle, chips, action_text, command):
        hero, content = make_card(parent, padx=24, pady=22)
        hero.pack(fill=tk.X, pady=(0, 18))
        content.grid_columnconfigure(0, weight=1)
        left = tk.Frame(content, bg=C['card_bg'])
        left.grid(row=0, column=0, sticky='nsew')
        title_row = tk.Frame(left, bg=C['card_bg'])
        title_row.pack(fill=tk.X)
        tk.Label(
            title_row,
            text=icon,
            bg=C['card_bg'],
            fg=C['accent'],
            font=('Segoe UI Emoji', 28),
        ).pack(side=tk.LEFT, padx=(0, 14))
        tk.Label(
            title_row,
            text=title,
            bg=C['card_bg'],
            fg=C['text_dark'],
            font=F['page_title'],
        ).pack(side=tk.LEFT)
        tk.Label(
            left,
            text=subtitle,
            bg=C['card_bg'],
            fg=C['text_muted'],
            font=F['label'],
            wraplength=720,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(10, 14))
        chip_row = tk.Frame(left, bg=C['card_bg'])
        chip_row.pack(anchor=tk.W)
        for chip in chips:
            tk.Label(
                chip_row,
                text=chip,
                bg=C['accent_soft'],
                fg=C['accent'],
                font=F['small_medium'],
                padx=10,
                pady=5,
            ).pack(side=tk.LEFT, padx=(0, 8), pady=(0, 4))

    def _refresh_subject_labels(self, tohop_var, label_widgets):
        for label, subject in zip(label_widgets, self._subject_names(tohop_var.get())):
            label.configure(text=f'{subject} (0-10):')

    def _build_dashboard_hero(self, parent):
        hero, content = make_card(parent, padx=24, pady=22)
        hero.pack(fill=tk.X, pady=(0, 18))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)
        intro = tk.Frame(content, bg=C['card_bg'])
        intro.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=(0, 22))
        tk.Label(
            intro,
            text='🤖 HUIT Career Advisor AI',
            bg=C['card_bg'],
            fg=C['text_dark'],
            font=F['page_title'],
        ).pack(anchor=tk.W)
        tk.Label(
            intro,
            text='AI sẽ phân tích hồ sơ và đề xuất ngành học phù hợp nhất với bạn.',
            bg=C['card_bg'],
            fg=C['text_muted'],
            font=F['label'],
            wraplength=720,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(8, 14))
        chips = tk.Frame(intro, bg=C['card_bg'])
        chips.pack(anchor=tk.W)
        for chip in (
            '✓ Ngành phù hợp',
            '✓ Tỷ lệ trúng tuyển',
            '✓ Trường nên đăng ký',
            '✓ Phương thức tối ưu',
        ):
            tk.Label(
                chips,
                text=chip,
                bg=C['accent_soft'],
                fg=C['accent'],
                font=F['small_medium'],
                padx=10,
                pady=5,
            ).pack(side=tk.LEFT, padx=(0, 8), pady=(0, 4))
        cta_box = tk.Frame(content, bg=C['card_bg'])
        cta_box.grid(row=0, column=2, sticky='e', pady=(0, 22))
        IconButton(
            cta_box,
            '🚀 Bắt đầu phân tích',
            self._run_overview,
            width=210,
        ).pack(anchor=tk.E)
        tk.Label(
            cta_box,
            text='Nhập điểm trước khi phân tích',
            bg=C['card_bg'],
            fg=C['text_subtle'],
            font=F['small'],
        ).pack(anchor=tk.E, pady=(8, 0))
        items = [
            ('1', 'Nhập điểm', 'Điền các kết quả hiện có theo từng phương thức.'),
            ('2', 'Bổ sung hồ sơ', 'Thêm sở thích, gia đình, địa lý và cá tính.'),
            ('3', 'Nhận tư vấn', 'So sánh phương thức và xem ngành học phù hợp.'),
        ]
        for index, (step, title, subtitle) in enumerate(items):
            tile = RoundedCard(content, padx=14, pady=12, radius=RADIUS['md'], fill_key='surface_alt')
            tile.configure(height=112)
            tile._canvas.configure(height=112)
            tile.grid(row=1, column=index, sticky='ew', padx=(0, 14 if index < 2 else 0))
            tile_content = tile.content
            badge = tk.Label(
                tile_content,
                text=step,
                bg=C['accent'],
                fg='#FFFFFF',
                font=F['small_medium'],
                width=3,
            )
            badge.pack(side=tk.LEFT, padx=(0, 12), ipady=4)
            text_box = tk.Frame(tile_content, bg=C['surface_alt'])
            text_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(
                text_box,
                text=title,
                bg=C['surface_alt'],
                fg=C['text_dark'],
                font=F['label_b'],
                anchor='w',
            ).pack(anchor=tk.W)
            tk.Label(
                text_box,
                text=subtitle,
                bg=C['surface_alt'],
                fg=C['text_muted'],
                font=F['small'],
                anchor='w',
                wraplength=250,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=(3, 0))

    def _build_metric_card(self, parent, title, value_var, subtitle, color_key, col):
        card = RoundedCard(parent, padx=18, pady=16, radius=RADIUS['lg'])
        card.grid(row=0, column=col, sticky='nsew', padx=(0, 12 if col < 3 else 0))
        content = card.content
        icon_map = {
            'Điểm ĐGNL': '📊',
            'Điểm Học bạ': '📚',
            'Điểm THPT': '📝',
            'Mức phù hợp': '✨',
        }
        tk.Label(
            content,
            text=icon_map.get(title, '•'),
            bg=C['accent_soft'] if color_key == 'accent' else C['surface_alt'],
            fg=C[color_key],
            font=('Segoe UI', 15),
            width=3,
        ).pack(anchor=tk.W, pady=(0, 10), ipady=5)
        tk.Label(
            content,
            text=title,
            bg=C['card_bg'],
            fg=C['text_muted'],
            font=F['small_medium'],
            anchor='w',
        ).pack(anchor=tk.W)
        tk.Label(
            content,
            textvariable=value_var,
            bg=C['card_bg'],
            fg=C[color_key],
            font=F['metric'],
            anchor='w',
        ).pack(anchor=tk.W, pady=(7, 2))
        tk.Label(
            content,
            text=subtitle,
            bg=C['card_bg'],
            fg=C['text_subtle'],
            font=F['small'],
            anchor='w',
        ).pack(anchor=tk.W)
        return card

    def _build_overview_metrics(self, parent):
        self.ov_metric_dgnl = tk.StringVar(value='—')
        self.ov_metric_hb = tk.StringVar(value='—')
        self.ov_metric_thpt = tk.StringVar(value='—')
        self.ov_metric_fit = tk.StringVar(value='Chưa có')
        row = tk.Frame(parent, bg=C['content_bg'])
        row.pack(fill=tk.X, pady=(0, 42))
        for index in range(4):
            row.grid_columnconfigure(index, weight=1)
        self._build_metric_card(row, 'Điểm ĐGNL', self.ov_metric_dgnl, 'Thang 600–1200', 'accent', 0)
        self._build_metric_card(row, 'Điểm Học bạ', self.ov_metric_hb, 'Tổng 3 môn', 'success', 1)
        self._build_metric_card(row, 'Điểm THPT', self.ov_metric_thpt, 'Tổng 3 môn thi', 'warning', 2)
        self._build_metric_card(row, 'Mức phù hợp', self.ov_metric_fit, 'Theo phương thức tốt nhất', 'ai_accent', 3)

    def _build_ai_insight_dashboard(self, parent):
        insight = RoundedCard(parent, padx=24, pady=22, radius=RADIUS['xl'], fill_key='ai_soft')
        content = insight.content
        insight.pack(fill=tk.X, pady=(0, 42))
        content.configure(bg=C['ai_soft'])
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=1)
        left = tk.Frame(content, bg=C['ai_soft'])
        left.grid(row=0, column=0, sticky='nsew')
        tk.Label(
            left,
            text='🤖 AI Nhận Định',
            bg=C['ai_soft'],
            fg=C['ai_accent'],
            font=F['hero_title'],
        ).pack(anchor=tk.W)
        self.ov_ai_summary = tk.StringVar(
            value=('Dựa trên dữ liệu hiện tại, AI sẽ:\n'
                   '• So sánh các phương thức xét tuyển\n'
                   '• Dự đoán khả năng trúng tuyển\n'
                   '• Gợi ý ngành phù hợp\n'
                   '• Đề xuất trường phù hợp')
        )
        tk.Label(
            left,
            textvariable=self.ov_ai_summary,
            bg=C['ai_soft'],
            fg=C['text_dark'],
            font=F['label'],
            wraplength=690,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(8, 0))
        IconButton(
            left,
            'Phân tích ngay',
            self._run_overview,
            width=180,
        ).pack(anchor=tk.W, pady=(18, 0))
        right = tk.Frame(content, bg=C['ai_soft'])
        right.grid(row=0, column=1, sticky='nsew', padx=(18, 0))
        self.ov_best_major = tk.StringVar(value='Chưa xác định')
        tk.Label(
            right,
            text='Ngành phù hợp nhất',
            bg=C['ai_soft'],
            fg=C['text_muted'],
            font=F['small_medium'],
        ).pack(anchor=tk.W)
        tk.Label(
            right,
            textvariable=self.ov_best_major,
            bg=C['ai_soft'],
            fg=C['ai_accent'],
            font=F['section'],
            wraplength=260,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(8, 0))

    def _build_top_major_dashboard(self, parent):
        top, content = make_card(parent, 'Top ngành phù hợp', padx=20, pady=14)
        top.pack(fill=tk.X, pady=(0, 42))
        self._top_major_rows = []
        for index in range(5):
            row = tk.Frame(content, bg=C['card_bg'])
            row.pack(fill=tk.X, pady=(0, 10 if index < 4 else 0))
            title = tk.Label(
                row,
                text=f'{index + 1}. Chưa có dữ liệu',
                bg=C['card_bg'],
                fg=C['text_dark'],
                font=F['label_b'],
                anchor='w',
            )
            title.pack(side=tk.LEFT, fill=tk.X, expand=True)
            badge = tk.Label(
                row,
                text='—',
                bg=C['accent_soft'],
                fg=C['accent'],
                font=F['small_medium'],
                padx=8,
                pady=3,
            )
            badge.pack(side=tk.RIGHT)
            bar_wrap = tk.Frame(content, bg=C['surface_alt'], height=7)
            bar_wrap.pack(fill=tk.X, pady=(0, 12 if index < 4 else 0))
            bar_wrap.pack_propagate(False)
            bar = tk.Frame(bar_wrap, bg=C['accent'], width=1)
            bar.pack(side=tk.LEFT, fill=tk.Y)
            self._top_major_rows.append((title, badge, bar, bar_wrap))

    def _update_overview_dashboard(self, scores=None, methods=None, majors=None):
        scores = scores or {}
        methods = methods or []
        majors = majors or []
        dgnl = scores.get('dgnl')
        self.ov_metric_dgnl.set(f'{dgnl:.0f}' if dgnl is not None else '—')
        hb = scores.get('hoc_ba')
        self.ov_metric_hb.set(f'{sum(hb):.1f}' if hb else '—')
        thpt = scores.get('thpt')
        self.ov_metric_thpt.set(f'{sum(thpt):.1f}' if thpt else '—')
        best = methods[0] if methods else None
        self.ov_metric_fit.set(f"{best['score']:.0f}%" if best else 'Chưa có')
        has_ai_insight = hasattr(self, 'ov_best_major') and hasattr(self, 'ov_ai_summary')
        if majors:
            top_major = majors[0]
            if has_ai_insight:
                self.ov_best_major.set(top_major.get('ten_nganh', 'Chưa xác định'))
            summary_lines = []
            for item in majors[:3]:
                summary_lines.append(
                    f"• {item.get('ten_nganh', 'Ngành phù hợp')}: {float(item.get('xac_suat', 0)):.0f}%"
                )
            if has_ai_insight:
                self.ov_ai_summary.set(
                    'Dựa trên hồ sơ hiện tại:\n'
                    + '\n'.join(summary_lines)
                    + f"\n\nPhương thức nên ưu tiên: {best['method'] if best else 'chưa xác định'}."
                )
        else:
            if has_ai_insight:
                self.ov_best_major.set('Chưa xác định')
                self.ov_ai_summary.set(
                    'Nhập điểm và hồ sơ để AI tổng hợp phương thức, ngành học và mức độ phù hợp.'
                )
        for index, (title, badge, bar, wrap) in enumerate(
            getattr(self, '_top_major_rows', [])
        ):
            if index < len(majors):
                item = majors[index]
                probability = max(0, min(100, float(item.get('xac_suat', 0))))
                title.configure(text=f"{index + 1}. {item.get('ten_nganh', '')}")
                badge.configure(text=f'{probability:.0f}%')
                wrap.update_idletasks()
                width = max(1, int(wrap.winfo_width() * probability / 100))
                bar.configure(width=width)
            else:
                title.configure(text=f'{index + 1}. Chưa có dữ liệu')
                badge.configure(text='—')
                bar.configure(width=1)

    def _open_profile_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title('Hồ sơ tư vấn bổ sung')
        dialog.geometry('840x410')
        dialog.minsize(760, 390)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg=C['content_bg'])
        try:
            dialog.attributes('-alpha', 0.0)
            self.after(10, lambda: self._fade_in(dialog))
        except tk.TclError:
            pass

        wrapper = tk.Frame(dialog, bg=C['content_bg'], padx=22, pady=20)
        wrapper.pack(fill=tk.BOTH, expand=True)
        tk.Label(
            wrapper,
            text='Hồ sơ tư vấn bổ sung',
            font=F['page_title'],
            bg=C['content_bg'],
            fg=C['text_dark'],
        ).pack(anchor=tk.W)
        tk.Label(
            wrapper,
            text=(
                "Ngoài học lực và điểm số, hệ thống còn xem xét các yếu tố như sở thích cá nhân, truyền thống nghề nghiệp\n"
                "của gia đình, điều kiện địa lý nơi sinh sống, môi trường kinh tế địa phương và một số đặc điểm cá nhân\n"
                "để đưa ra gợi ý ngành học phù hợp hơn. Các yếu tố này chỉ mang tính hỗ trợ tham khảo nhằm tăng độ chính xác."
            ),
            font=F['small'],
            bg=C['content_bg'],
            fg=C['text_muted'],
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(2, 14))
        card, content = make_card(wrapper, padx=18, pady=16)
        card.pack(fill=tk.BOTH, expand=True)
        self._build_profile_fields(content)
        actions = tk.Frame(content, bg=C['card_bg'])
        actions.grid(row=4, column=0, columnspan=4, sticky='e', pady=(16, 0))
        IconButton(
            actions,
            'Hoàn tất',
            dialog.destroy,
            width=120,
        ).pack(side=tk.RIGHT)

    def _fade_in(self, window, alpha=0.0):
        try:
            next_alpha = min(1.0, alpha + 0.12)
            window.attributes('-alpha', next_alpha)
            if next_alpha < 1.0:
                self.after(12, lambda: self._fade_in(window, next_alpha))
        except tk.TclError:
            pass

    # ══════════════════════════════════════════════════════════════════════
    #  PAGE – TỔNG QUAN
    # ══════════════════════════════════════════════════════════════════════
    def _method_card_header(self, parent, icon, title, subtitle, color_key='accent'):
        head = tk.Frame(parent, bg=C['card_bg'])
        head.pack(fill=tk.X, pady=(0, 16))
        tk.Label(
            head,
            text=icon,
            bg=C['accent_soft'] if color_key == 'accent' else C['surface_alt'],
            fg=C[color_key],
            font=('Segoe UI Emoji', 18),
            width=3,
        ).pack(side=tk.LEFT, padx=(0, 12), ipady=7)
        text_box = tk.Frame(head, bg=C['card_bg'])
        text_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(
            text_box,
            text=title,
            bg=C['card_bg'],
            fg=C['text_dark'],
            font=F['section'],
            anchor='w',
        ).pack(anchor=tk.W)
        tk.Label(
            text_box,
            text=subtitle,
            bg=C['card_bg'],
            fg=C['text_muted'],
            font=F['small'],
            anchor='w',
            justify=tk.LEFT,
            wraplength=390,
        ).pack(anchor=tk.W, pady=(3, 0))

    def _subject_names(self, tohop):
        subjects = list(TO_HOP_MON.get(tohop, []))
        while len(subjects) < 3:
            subjects.append(f'Môn {len(subjects) + 1}')
        return subjects[:3]

    def _update_total_var(self, score_vars, total_var):
        total = 0.0
        has_value = False
        for variable in score_vars:
            raw = variable.get().strip()
            if not raw:
                continue
            try:
                total += float(raw)
                has_value = True
            except ValueError:
                total_var.set('Chưa hợp lệ')
                return
        total_var.set(f'{total:.2f}' if has_value else '—')

    def _build_subject_score_card(self, parent, tohop_var, score_vars):
        controls = tk.Frame(parent, bg=C['card_bg'])
        controls.pack(fill=tk.X, pady=(0, 14))
        tk.Label(
            controls,
            text='Tổ hợp',
            bg=C['card_bg'],
            fg=C['text_muted'],
            font=F['small_medium'],
        ).pack(side=tk.LEFT, padx=(0, 10))
        styled_combo(
            controls,
            tohop_var,
            sorted(TO_HOP_MON),
            width=12,
        ).pack(side=tk.LEFT)

        grid = tk.Frame(parent, bg=C['card_bg'])
        grid.pack(fill=tk.X)
        subject_labels = []
        for index, variable in enumerate(score_vars):
            cell = tk.Frame(grid, bg=C['card_bg'])
            cell.grid(row=0, column=index, sticky='ew', padx=(0, 12 if index < 2 else 0))
            grid.grid_columnconfigure(index, weight=1)
            label = tk.Label(
                cell,
                text='',
                bg=C['card_bg'],
                fg=C['text_dark'],
                font=F['label_b'],
                anchor='w',
            )
            label.pack(anchor=tk.W, pady=(0, 6))
            subject_labels.append(label)
            styled_entry(cell, variable, 9).pack(anchor=tk.W, fill=tk.X)

        total_var = tk.StringVar(value='—')
        total = tk.Frame(parent, bg=C['surface_alt'], padx=12, pady=10)
        total.pack(fill=tk.X, pady=(16, 0))
        tk.Label(
            total,
            text='Tổng tổ hợp',
            bg=C['surface_alt'],
            fg=C['text_muted'],
            font=F['small_medium'],
        ).pack(side=tk.LEFT)
        tk.Label(
            total,
            textvariable=total_var,
            bg=C['surface_alt'],
            fg=C['accent'],
            font=F['section'],
        ).pack(side=tk.RIGHT)

        def refresh(*_):
            for label, subject in zip(subject_labels, self._subject_names(tohop_var.get())):
                label.configure(text=subject)
            self._update_total_var(score_vars, total_var)

        tohop_var.trace_add('write', refresh)
        for variable in score_vars:
            variable.trace_add('write', lambda *_: self._update_total_var(score_vars, total_var))
        refresh()

    def _build_direct_score_card(self, parent):
        grid = tk.Frame(parent, bg=C['card_bg'])
        grid.pack(fill=tk.X)
        labels = ['Lớp 10', 'Lớp 11', 'Lớp 12']
        for index, (label_text, variable) in enumerate(zip(labels, self.ov_direct_scores)):
            cell = tk.Frame(grid, bg=C['card_bg'])
            cell.grid(row=0, column=index, sticky='ew', padx=(0, 12 if index < 2 else 0))
            grid.grid_columnconfigure(index, weight=1)
            tk.Label(
                cell,
                text=label_text,
                bg=C['card_bg'],
                fg=C['text_dark'],
                font=F['label_b'],
            ).pack(anchor=tk.W, pady=(0, 6))
            styled_entry(cell, variable, 9).pack(anchor=tk.W, fill=tk.X)

        bottom = tk.Frame(parent, bg=C['card_bg'])
        bottom.pack(fill=tk.X, pady=(16, 0))
        tk.Label(
            bottom,
            text='Điểm Tiếng Anh',
            bg=C['card_bg'],
            fg=C['text_dark'],
            font=F['label_b'],
        ).pack(side=tk.LEFT, padx=(0, 10))
        styled_entry(bottom, self.ov_english, 10).pack(side=tk.LEFT)

    def _build_page_overview(self):
        page = ScrollablePage(self._content_host)
        self._pages['Tổng quan'] = page
        content = page.content
        self._build_dashboard_hero(content)

        self.ov_dgnl = tk.StringVar()
        self.ov_hb_tohop = tk.StringVar(value='D01')
        self.ov_hb_scores = [tk.StringVar() for _ in range(3)]
        self.ov_thpt_tohop = tk.StringVar(value='D01')
        self.ov_thpt_scores = [tk.StringVar() for _ in range(3)]
        self.ov_direct_scores = [tk.StringVar() for _ in range(3)]
        self.ov_english = tk.StringVar()
        self.ov_dhsp = tk.StringVar()
        self.ov_kv = tk.StringVar(value='KV3')
        self.ov_dt = tk.StringVar(value='Không ưu tiên')

        self._build_overview_metrics(content)

        method_grid = tk.Frame(content, bg=C['content_bg'])
        method_grid.pack(fill=tk.X, pady=(0, 32))
        for column in range(2):
            method_grid.grid_columnconfigure(column, weight=1, uniform='overview_methods')

        card, panel = make_card(method_grid, padx=22, pady=18)
        card.grid(row=1, column=1, sticky='nsew', padx=(12, 0), pady=(0, 24))
        self._method_card_header(
            panel,
            '🧠',
            'Đánh giá năng lực ĐHQG-HCM',
            'Nhập tổng điểm ĐGNL theo thang 600-1200.',
            'accent',
        )
        tk.Label(panel, text='Tổng điểm ĐGNL', bg=C['card_bg'], fg=C['text_dark'], font=F['label_b']).pack(anchor=tk.W, pady=(0, 6))
        styled_entry(panel, self.ov_dgnl, 14).pack(anchor=tk.W)

        card, panel = make_card(method_grid, padx=22, pady=18)
        card.grid(row=0, column=0, sticky='nsew', padx=(0, 12), pady=(0, 24))
        self._method_card_header(
            panel,
            '📚',
            'Xét học bạ THPT',
            'Chọn tổ hợp, sau đó nhập điểm theo từng môn thực tế.',
            'success',
        )
        self._build_subject_score_card(panel, self.ov_hb_tohop, self.ov_hb_scores)

        card, panel = make_card(method_grid, padx=22, pady=18)
        card.grid(row=0, column=1, sticky='nsew', padx=(12, 0), pady=(0, 24))
        self._method_card_header(
            panel,
            '📝',
            'Điểm thi THPT',
            'Nhập điểm thi theo đúng môn của tổ hợp xét tuyển.',
            'warning',
        )
        self._build_subject_score_card(panel, self.ov_thpt_tohop, self.ov_thpt_scores)

        card, panel = make_card(method_grid, padx=22, pady=18)
        card.grid(row=1, column=0, sticky='nsew', padx=(0, 12), pady=(0, 24))
        self._method_card_header(
            panel,
            '🎯',
            'Tuyển thẳng',
            'Nhập điểm trung bình lớp 10, 11, 12 và điểm tiếng Anh nếu có.',
            'ai_accent',
        )
        self._build_direct_score_card(panel)

        card, panel = make_card(method_grid, padx=22, pady=18)
        card.grid(row=2, column=0, sticky='nsew', padx=(0, 12))
        self._method_card_header(
            panel,
            '⭐',
            'Đánh giá năng lực chuyên biệt ĐHSP',
            'Ghi nhận điểm riêng để hoàn thiện hồ sơ, không ảnh hưởng mô hình hiện tại.',
            'accent',
        )
        tk.Label(panel, text='Điểm ĐGNL chuyên biệt', bg=C['card_bg'], fg=C['text_dark'], font=F['label_b']).pack(anchor=tk.W, pady=(0, 6))
        styled_entry(panel, self.ov_dhsp, 14).pack(anchor=tk.W)

        card, panel = make_card(method_grid, padx=22, pady=18)
        card.grid(row=2, column=1, sticky='nsew', padx=(12, 0))
        self._method_card_header(
            panel,
            '⚙',
            'Ưu tiên xét tuyển',
            'Thiết lập khu vực và đối tượng ưu tiên dùng chung cho các phương thức.',
            'warning',
        )
        prefs = tk.Frame(panel, bg=C['card_bg'])
        prefs.pack(fill=tk.X)
        for column in range(2):
            prefs.grid_columnconfigure(column, weight=1)
        tk.Label(prefs, text='Khu vực', bg=C['card_bg'], fg=C['text_dark'], font=F['label_b']).grid(row=0, column=0, sticky='w', pady=(0, 6))
        styled_combo(prefs, self.ov_kv, ['KV1', 'KV2-NT', 'KV2', 'KV3'], width=13).grid(row=1, column=0, sticky='w')
        tk.Label(prefs, text='Đối tượng', bg=C['card_bg'], fg=C['text_dark'], font=F['label_b']).grid(row=0, column=1, sticky='w', pady=(0, 6))
        styled_combo(
            prefs,
            self.ov_dt,
            ['Nhóm 1 (01-04)', 'Nhóm 2 (05-07)', 'Không ưu tiên'],
            width=22,
        ).grid(row=1, column=1, sticky='w')

        profile_card, profile_content = make_card(
            content,
            'Yếu tố hỗ trợ định hướng',
            padx=20,
            pady=14,
        )
        profile_card.pack(fill=tk.X, pady=(0, 10))
        next_row = self._build_profile_fields(profile_content)
        tk.Label(
            profile_content,
            text=(
                "Ngoài học lực và điểm số, hệ thống còn xem xét các yếu tố như sở thích cá nhân, truyền thống\n"
                "nghề nghiệp của gia đình, điều kiện địa lý nơi sinh sống, môi trường kinh tế địa phương và một số\n"
                "đặc điểm cá nhân để đưa ra gợi ý ngành học phù hợp hơn. Các yếu tố này chỉ mang tính hỗ trợ\n"
                "tham khảo nhằm tăng độ chính xác của việc tư vấn hướng nghiệp."
            ),
            bg=C['card_bg'],
            fg=C['text_muted'],
            font=F['small'],
            justify=tk.LEFT,
        ).grid(row=next_row, column=0, columnspan=4, sticky='w', pady=(8, 0))

        action_row = tk.Frame(content, bg=C['content_bg'])
        action_row.pack(fill=tk.X, pady=(2, 10))
        IconButton(
            action_row,
            'Đánh giá toàn bộ hồ sơ',
            self._run_overview,
            width=210,
        ).pack(side=tk.LEFT)
        IconButton(
            action_row,
            'Xóa điểm',
            self._clear_overview,
            bg=C['secondary'],
            fg=C['text_dark'],
            hover=C['secondary_hover'],
            width=110,
        ).pack(side=tk.LEFT, padx=(10, 0))

        self._build_ai_insight_dashboard(content)
        self._build_top_major_dashboard(content)

        method_card, method_content = make_card(
            content,
            'Phương thức xét tuyển đề xuất',
            padx=12,
            pady=12,
        )
        method_card.pack(fill=tk.X, pady=(0, 10))
        self._tbl_methods = MethodTable(method_content)
        self._tbl_methods.pack(fill=tk.X)
        self._tbl_methods.populate([])

        major_card, major_content = make_card(
            content,
            'Ngành học nổi bật từ toàn bộ hồ sơ',
            padx=12,
            pady=12,
        )
        major_card.pack(fill=tk.BOTH, expand=True)
        self._tbl_overview = ResultTable(major_content)
        self._tbl_overview.pack(fill=tk.BOTH, expand=True)
        self._overview_major_results = []

    def _optional_triplet(self, variables, label, show_errors=True):
        raw_values = [variable.get().strip() for variable in variables]
        if not any(raw_values):
            return None
        if not all(raw_values):
            if show_errors:
                messagebox.showwarning(
                    'Thiếu điểm',
                    f'Vui lòng nhập đủ ba điểm cho {label}.',
                )
            return False
        try:
            values = [float(value) for value in raw_values]
        except ValueError:
            if show_errors:
                messagebox.showwarning(
                    'Điểm không hợp lệ',
                    f'Điểm {label} phải là số.',
                )
            return False
        if not all(0 <= value <= 10 for value in values):
            if show_errors:
                messagebox.showwarning(
                    'Điểm không hợp lệ',
                    f'Điểm {label} phải nằm trong khoảng 0–10.',
                )
            return False
        return values

    def _overview_input(self, show_errors=True):
        dgnl = None
        if self.ov_dgnl.get().strip():
            try:
                dgnl = float(self.ov_dgnl.get())
                if not 600 <= dgnl <= 1200:
                    raise ValueError
            except ValueError:
                if show_errors:
                    messagebox.showwarning(
                        'Điểm không hợp lệ',
                        'Điểm ĐGNL phải nằm trong khoảng 600–1200.',
                    )
                return None
        hoc_ba = self._optional_triplet(
            self.ov_hb_scores, 'học bạ', show_errors)
        thpt = self._optional_triplet(
            self.ov_thpt_scores, 'thi THPT', show_errors)
        direct = self._optional_triplet(
            self.ov_direct_scores, 'điểm trung bình ba năm', show_errors)
        if False in (hoc_ba, thpt, direct):
            return None
        if dgnl is None and not any((hoc_ba, thpt, direct)):
            if show_errors:
                messagebox.showwarning(
                    'Chưa có dữ liệu',
                    'Hãy nhập điểm của ít nhất một phương thức xét tuyển.',
                )
            return None
        return {
            'dgnl': dgnl,
            'hoc_ba': hoc_ba,
            'thpt': thpt,
            'tuyen_thang': direct,
        }

    def _run_overview(self):
        scores = self._overview_input(show_errors=True)
        if not scores:
            return
        self._set_status('Đang đánh giá toàn bộ hồ sơ...')
        self._tbl_methods.populate([])
        self._tbl_overview.show_loading()
        self.update_idletasks()

        methods = rank_admission_methods(scores)
        self._tbl_methods.populate(methods)
        self._update_overview_dashboard(scores=scores, methods=methods, majors=[])
        readiness = {
            item['method']: item['score'] / 100.0 for item in methods
        }
        profile = self._current_profile()
        group = profile.interest_group
        if group == NONE_OPTION:
            group = None
        candidates = {}

        def collect(method_name, results):
            for item in enrich_major_results(results, profile):
                code = str(item.get('ma_nganh') or '')
                if not code or code == 'Error':
                    continue
                weighted = float(item.get('xac_suat', 0)) * (
                    0.65 + 0.35 * readiness.get(method_name, 0.5)
                )
                candidate = dict(item)
                candidate['xac_suat'] = round(weighted, 2)
                candidate['ghi_chu'] = f'Phù hợp nhất qua {method_name}'
                if code not in candidates or weighted > candidates[code]['xac_suat']:
                    candidates[code] = candidate

        if scores['dgnl'] is not None and dgnl_predict:
            collect('ĐGNL', dgnl_predict(
                scores['dgnl'],
                diem_dt=0,
                diem_kv=0,
                thu_tu_nv=1,
                nguyen_vong=group,
                top_n=10,
            ))
        if scores['hoc_ba'] and HocBaAnalyzer:
            analyzer = HocBaAnalyzer()
            if analyzer.load_models():
                priority = analyzer.get_priority_points(
                    self.ov_kv.get(),
                    self.ov_dt.get().replace('Không ưu tiên',
                                             'Không thuộc diện ưu tiên'),
                )
                m1, m2, m3 = scores['hoc_ba']
                collect('Học bạ', analyzer.predict_nganh({
                    'to_hop': self.ov_hb_tohop.get(),
                    'mon_hoc': TO_HOP_MON.get(self.ov_hb_tohop.get(), []),
                    'diem_tb_mon1': m1,
                    'diem_tb_mon2': m2,
                    'diem_tb_mon3': m3,
                    'diem_hb': round(m1 + m2 + m3, 2),
                    'diem_xet_tuyen': round(m1 + m2 + m3 + priority, 2),
                }, top_k=10, nguyen_vong=group or ''))
        if scores['tuyen_thang'] and tt_predict:
            english = 0.0
            try:
                english = float(self.ov_english.get() or 0)
            except ValueError:
                pass
            collect('Tuyển thẳng', tt_predict(
                sum(scores['tuyen_thang']),
                english,
                group,
                top_n=10,
            ))
        if scores['thpt'] and goi_y_nganh_thpt:
            total = sum(scores['thpt'])
            priority = calculate_priority_pt1(
                total,
                self.ov_kv.get(),
                self.ov_dt.get(),
            )
            collect('THPT QG', goi_y_nganh_thpt(
                *scores['thpt'],
                diem_ut=priority,
                thu_tu_nv=1,
                tohop=self.ov_thpt_tohop.get(),
                nguyen_vong=group,
                top_n=10,
            ))

        self._overview_major_results = sorted(
            candidates.values(),
            key=lambda item: item['xac_suat'],
            reverse=True,
        )[:12]
        self._tbl_overview.populate(self._overview_major_results)
        self._update_overview_dashboard(
            scores=scores,
            methods=methods,
            majors=self._overview_major_results,
        )
        best = methods[0]['method'] if methods else 'chưa xác định'
        self._set_status(
            f'Hoàn tất đánh giá. Phương thức ưu tiên: {best}.'
        )

    def _clear_overview(self):
        self.ov_dgnl.set('')
        for variable in (
            self.ov_hb_scores
            + self.ov_thpt_scores
            + self.ov_direct_scores
        ):
            variable.set('')
        self.ov_english.set('')
        if hasattr(self, 'ov_dhsp'):
            self.ov_dhsp.set('')
        self._tbl_methods.populate([])
        self._tbl_overview.show_empty()
        self._overview_major_results = []
        self._update_overview_dashboard()

    # ══════════════════════════════════════════════════════════════════════
    #  PAGE – ĐGNL
    # ══════════════════════════════════════════════════════════════════════
    def _build_page_dgnl(self):
        page = ScrollablePage(self._content_host)
        self._pages['ĐGNL'] = page
        content = page.content
        self._build_method_page_hero(
            content,
            '🧠',
            'Xét tuyển theo ĐGNL',
            'AI phân tích điểm đánh giá năng lực, ưu tiên khu vực và nguyện vọng ngành để gợi ý ngành học phù hợp.',
            ('Tổng điểm 600-1200', 'Điểm từng phần', 'Ưu tiên khu vực', 'Gợi ý ngành'),
            'Phân tích ĐGNL',
            self._run_dgnl,
        )
        self._build_profile_strip(content)

        c_out, c_in = make_card(content, 'Thông tin điểm ĐGNL', padx=20, pady=14)
        c_out.pack(fill=tk.X, pady=(0, 18))

        # Cách nhập điểm
        tk.Label(c_in, text='Cách nhập điểm:', font=F['label_b'],
                 bg=C['card_bg'], fg=C['text_dark']).grid(
            row=0, column=0, sticky='w', pady=(0, 6))
        self.dgnl_input_mode = tk.StringVar(value='tong')
        rb_f = tk.Frame(c_in, bg=C['card_bg'])
        rb_f.grid(row=0, column=1, columnspan=3, sticky='w', pady=(0, 6))
        for val, txt in [('tong', '  Nhập tổng điểm ĐGNL  '),
                         ('mon',  '  Nhập điểm từng môn')]:
            ttk.Radiobutton(rb_f, text=txt, variable=self.dgnl_input_mode,
                            value=val).pack(side=tk.LEFT, padx=(0, 8))

        # Tổng điểm
        self.dgnl_total = tk.StringVar()
        self._dTotalLbl = label_row(c_in, 'Tổng điểm ĐGNL (600–1200):', 1)
        self._dTotalEnt = styled_entry(c_in, self.dgnl_total, width=14)
        self._dTotalEnt.grid(row=1, column=1, sticky='w', padx=(0, 12), pady=4)

        # Điểm từng môn
        mon_names = ['Tiếng Việt', 'Tiếng Anh', 'Toán học', 'Tư duy KH']
        self.dgnl_mon_vars   = []
        self._dMonLbls       = []
        self._dMonEnts       = []
        for i, mn in enumerate(mon_names):
            v   = tk.StringVar()
            lbl = label_row(c_in, f'{mn} (0–300):', 2 + i)
            ent = styled_entry(c_in, v, width=10)
            ent.grid(row=2 + i, column=1, sticky='w', padx=(0, 12), pady=4)
            v.trace_add('write', self._dgnl_update_sum)
            self.dgnl_mon_vars.append(v)
            self._dMonLbls.append(lbl)
            self._dMonEnts.append(ent)
            lbl.grid_remove(); ent.grid_remove()

        # Tổng + XT labels
        self._dSumLbl = label_row(c_in, 'Tổng ĐGNL:', 6)
        self._dSumVal = tk.Label(c_in, text='—', font=('Segoe UI', 11, 'bold'),
                                 bg=C['card_bg'], fg=C['accent'])
        self._dSumVal.grid(row=6, column=1, sticky='w', pady=4)
        self._dSumLbl.grid_remove(); self._dSumVal.grid_remove()

        self._dXTLbl = label_row(c_in, 'Điểm xét tuyển (+ ưu tiên):', 6, col=2)
        self._dXTVal = tk.Label(c_in, text='—', font=('Segoe UI', 11, 'bold'),
                                bg=C['card_bg'], fg=C['success'])
        self._dXTVal.grid(row=6, column=3, sticky='w', pady=4)

        section_sep(c_in, 7)

        # Ưu tiên
        label_row(c_in, 'Đối tượng ưu tiên:', 8)
        self.dgnl_ut = tk.StringVar(value='none')
        styled_combo(c_in, self.dgnl_ut,
                     ['none', 'ƯT1 (01–04)', 'ƯT2 (05–07)'],
                     width=14).grid(row=8, column=1, sticky='w', padx=(0, 12), pady=4)
        label_row(c_in, 'Khu vực:', 8, col=2)
        self.dgnl_kv = tk.StringVar(value='KV3')
        styled_combo(c_in, self.dgnl_kv,
                     ['KV1', 'KV2-NT', 'KV2', 'KV3'],
                     width=10).grid(row=8, column=3, sticky='w', pady=4)

        self._dUTInfo = tk.Label(c_in, text='', font=('Segoe UI', 9, 'italic'),
                                 bg=C['card_bg'], fg=C['warning'])
        self._dUTInfo.grid(row=9, column=0, columnspan=4, sticky='w', pady=(0, 4))

        section_sep(c_in, 10)
        label_row(c_in, 'Nhóm ngành ưa thích (tùy chọn):', 11)
        self.dgnl_group = tk.StringVar(value='(Tất cả)')
        styled_combo(c_in, self.dgnl_group,
                     ['(Tất cả)'] + GROUP_OPTIONS, width=56).grid(
            row=11, column=1, columnspan=3, sticky='w', pady=4)

        # Buttons
        btn_r = tk.Frame(c_in, bg=C['card_bg'])
        btn_r.grid(row=12, column=0, columnspan=4, sticky='w', pady=(12, 0))
        IconButton(btn_r, 'Phân tích hồ sơ', self._run_dgnl, width=170).pack(side=tk.LEFT)
        IconButton(btn_r, 'Xóa dữ liệu', self._clear_dgnl,
                   bg=C['secondary'], fg=C['text_dark'],
                   hover=C['secondary_hover'], width=125).pack(side=tk.LEFT, padx=(10, 0))

        # Results
        r_out, r_in = make_card(content, 'Kết quả gợi ý ngành học', padx=12, pady=12)
        r_out.pack(fill=tk.BOTH, expand=True)
        self._tbl_dgnl = ResultTable(r_in)
        self._tbl_dgnl.pack(fill=tk.BOTH, expand=True)

        # Wire up traces
        for v in [self.dgnl_ut, self.dgnl_kv, self.dgnl_total]:
            v.trace_add('write', self._dgnl_update_sum)
        self.dgnl_input_mode.trace_add('write', self._dgnl_toggle)
        self.dgnl_input_mode.trace_add('write', self._dgnl_update_sum)
        self._dgnl_toggle()
        self._dgnl_update_sum()

    def _dgnl_toggle(self, *_):
        mode = self.dgnl_input_mode.get()
        if mode == 'tong':
            self._dTotalLbl.grid(); self._dTotalEnt.grid()
            for l, e in zip(self._dMonLbls, self._dMonEnts):
                l.grid_remove(); e.grid_remove()
            self._dSumLbl.grid_remove(); self._dSumVal.grid_remove()
        else:
            self._dTotalLbl.grid_remove(); self._dTotalEnt.grid_remove()
            for l, e in zip(self._dMonLbls, self._dMonEnts):
                l.grid(); e.grid()
            self._dSumLbl.grid(); self._dSumVal.grid()

    def _dgnl_update_sum(self, *_):
        try:
            if self.dgnl_input_mode.get() == 'mon':
                s = sum(float(v.get() or 0) for v in self.dgnl_mon_vars)
            else:
                s = float(self.dgnl_total.get() or 0)
        except Exception:
            s = 0
        ut_map = {'none': 0, 'ƯT1 (01–04)': 80, 'ƯT2 (05–07)': 40}
        kv_map = {'KV1': 30, 'KV2-NT': 20, 'KV2': 10, 'KV3': 0}
        dut = ut_map.get(self.dgnl_ut.get(), 0) + kv_map.get(self.dgnl_kv.get(), 0)
        if s >= 900 and dut > 0:
            dut = round(((1200 - s) / 300) * dut, 2)
        self._dSumVal.config(text=f'{s:.0f} / 1200')
        self._dXTVal.config(text=f'{s + dut:.1f} / 1200')
        self._dUTInfo.config(
            text=f'  + {dut} điểm ưu tiên (quy định mới)' if dut > 0 else '')

    def _clear_dgnl(self):
        self.dgnl_total.set('')
        for v in self.dgnl_mon_vars:
            v.set('')
        self.dgnl_ut.set('none'); self.dgnl_kv.set('KV3')
        self.dgnl_group.set('(Tất cả)')
        self._tbl_dgnl.show_empty()

    def _run_dgnl(self):
        if dgnl_predict is None:
            messagebox.showerror('Lỗi', "Không thể tải mô-đun ĐGNL.\nKiểm tra 'Goi_y_nganh_nghe.py'.")
            return
        mode = self.dgnl_input_mode.get()
        diem_thanh_phan = None
        if mode == 'tong':
            try:
                diem = float(self.dgnl_total.get())
                if not (600 <= diem <= 1200):
                    raise ValueError
            except Exception:
                messagebox.showwarning('Giá trị không hợp lệ',
                                       'Tổng điểm ĐGNL phải là số từ 600 đến 1200.')
                return
        else:
            try:
                mon_keys   = ['vietnamese', 'english', 'math', 'science']
                mon_labels = ['Tiếng Việt', 'Tiếng Anh', 'Toán học', 'Tư duy KH']
                diem_thanh_phan = {k: float(v.get() or 0)
                                   for k, v in zip(mon_keys, self.dgnl_mon_vars)}
                for k, lbl in zip(mon_keys, mon_labels):
                    if not (0 <= diem_thanh_phan[k] <= 300):
                        messagebox.showwarning('Sai giá trị',
                                               f'Điểm {lbl} phải từ 0 đến 300.')
                        return
                diem = sum(diem_thanh_phan.values())
                if not (600 <= diem <= 1200):
                    messagebox.showwarning('Sai tổng điểm',
                                           'Tổng điểm phải từ 600 đến 1200.')
                    return
            except Exception as ex:
                messagebox.showwarning('Lỗi nhập', str(ex)); return

        ut_map = {'none': 0, 'ƯT1 (01–04)': 80, 'ƯT2 (05–07)': 40}
        kv_map = {'KV1': 30, 'KV2-NT': 20, 'KV2': 10, 'KV3': 0}
        dut = ut_map.get(self.dgnl_ut.get(), 0) + kv_map.get(self.dgnl_kv.get(), 0)
        if diem >= 900 and dut > 0:
            dut = round(((1200 - diem) / 300) * dut, 2)
        group = self.dgnl_group.get()
        if group == '(Tất cả)':
            group = None
        self._set_status('Đang xử lý ĐGNL…')
        self._tbl_dgnl.show_loading()
        self.update_idletasks()
        results = dgnl_predict(diem, diem_dt=0, diem_kv=dut,
                               thu_tu_nv=1, nguyen_vong=group, top_n=12)
        results = enrich_major_results(results, self._current_profile())
        self._tbl_dgnl.populate(results)
        self._set_status(f'Đã gợi ý {len(results)} ngành phù hợp (ĐGNL)')

    # ══════════════════════════════════════════════════════════════════════
    #  PAGE – HỌC BẠ
    # ══════════════════════════════════════════════════════════════════════
    def _build_page_hocba(self):
        page = ScrollablePage(self._content_host)
        self._pages['Học bạ'] = page
        content = page.content
        self._build_method_page_hero(
            content,
            '📚',
            'Xét tuyển theo Học bạ',
            'Nhập điểm trung bình từng môn theo tổ hợp xét tuyển để AI đánh giá mức độ phù hợp.',
            ('Tổ hợp môn', 'Điểm học bạ', 'Ưu tiên 2026', 'Ngành phù hợp'),
            'Phân tích học bạ',
            self._run_hocba,
        )
        self._build_profile_strip(content)

        c_out, c_in = make_card(content, 'Thông tin học bạ THPT', padx=20, pady=14)
        c_out.pack(fill=tk.X, pady=(0, 18))

        label_row(c_in, 'Nhóm ngành:', 0)
        self.hb_group = tk.StringVar()
        cb = styled_combo(c_in, self.hb_group, GROUP_OPTIONS, width=56)
        cb.grid(row=0, column=1, columnspan=3, sticky='ew', pady=4)
        cb.bind('<<ComboboxSelected>>', self._on_hb_group_changed)

        label_row(c_in, 'Tổ hợp môn:', 1)
        self.hb_tohop = tk.StringVar()
        self.hb_cb_tohop = styled_combo(c_in, self.hb_tohop, [], width=16)
        self.hb_cb_tohop.grid(row=1, column=1, sticky='w', pady=4)

        section_sep(c_in, 2)

        self._hb_subject_labels = []
        fields_hb = [
            ('Môn 1 (0-10):', 'hb_m1', 3, 0),
            ('Môn 2 (0-10):', 'hb_m2', 3, 2),
            ('Môn 3 (0-10):', 'hb_m3', 4, 0),
        ]
        for lbl_t, attr, r, col in fields_hb:
            self._hb_subject_labels.append(label_row(c_in, lbl_t, r, col=col))
            v = tk.StringVar(value='')
            styled_entry(c_in, v, 10).grid(
                row=r, column=col + 1, sticky='w', pady=4)
            setattr(self, attr, v)
        self.hb_tohop.trace_add(
            'write',
            lambda *_: self._refresh_subject_labels(self.hb_tohop, self._hb_subject_labels),
        )

        # Ưu tiên mới cho 2026
        label_row(c_in, 'Khu vực:', 4, col=2)
        self.hb_kv = tk.StringVar(value='KV3')
        styled_combo(c_in, self.hb_kv, ['KV1', 'KV2-NT', 'KV2', 'KV3'],
                     width=10).grid(row=4, column=3, sticky='w', pady=4)

        label_row(c_in, 'Đối tượng ưu tiên:', 5)
        self.hb_dt = tk.StringVar(value='Không thuộc diện ưu tiên')
        styled_combo(c_in, self.hb_dt,
                     ['Nhóm 1 (01-04)', 'Nhóm 2 (05-07)',
                      'Không thuộc diện ưu tiên'],
                     width=24).grid(row=5, column=1, columnspan=3,
                                    sticky='w', pady=4)

        btn_r = tk.Frame(c_in, bg=C['card_bg'])
        btn_r.grid(row=6, column=0, columnspan=4, sticky='w', pady=(12, 0))
        IconButton(btn_r, 'Phân tích hồ sơ', self._run_hocba, width=170).pack(side=tk.LEFT)
        IconButton(btn_r, 'Xóa dữ liệu', self._clear_hocba,
                   bg=C['secondary'], fg=C['text_dark'],
                   hover=C['secondary_hover'], width=125).pack(side=tk.LEFT, padx=(10, 0))

        r_out, r_in = make_card(content, 'Kết quả gợi ý ngành học', padx=12, pady=12)
        r_out.pack(fill=tk.BOTH, expand=True)
        self._tbl_hb = ResultTable(r_in)
        self._tbl_hb.pack(fill=tk.BOTH, expand=True)

    def _on_hb_group_changed(self, *_):
        vals = sorted(allowed_tohops_for_group(self.hb_group.get())
                      if callable(allowed_tohops_for_group) else set())
        self.hb_cb_tohop['values'] = vals
        if vals:
            self.hb_cb_tohop.set(vals[0])
        if hasattr(self, '_hb_subject_labels'):
            self._refresh_subject_labels(self.hb_tohop, self._hb_subject_labels)

    def _clear_hocba(self):
        for attr in ('hb_m1', 'hb_m2', 'hb_m3'):
            getattr(self, attr).set('')
        self.hb_kv.set('KV3')
        self.hb_dt.set('Không thuộc diện ưu tiên')
        self._tbl_hb.show_empty()

    def _run_hocba(self):
        if HocBaAnalyzer is None:
            messagebox.showerror('Lỗi', "Không thể tải HocBaAnalyzer.\nKiểm tra 'hoc_ba_analyzer.py'.")
            return
        group = self.hb_group.get().strip()
        tohop = self.hb_tohop.get().strip().upper()
        if not group or not tohop:
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng chọn nhóm ngành và tổ hợp.')
            return
        try:
            m1 = float(self.hb_m1.get()); m2 = float(self.hb_m2.get())
            m3 = float(self.hb_m3.get())
        except Exception:
            messagebox.showwarning('Giá trị không hợp lệ', 'Điểm phải là số hợp lệ.')
            return
        if not all(0 <= x <= 10 for x in (m1, m2, m3)):
            messagebox.showwarning('Giá trị không hợp lệ', 'Điểm môn phải trong [0, 10].')
            return
        analyzer = HocBaAnalyzer()
        if not analyzer.load_models():
            messagebox.showerror('Thiếu mô hình',
                                 'Chưa có models/hocba_models.pkl. Hãy huấn luyện trước.')
            return
            
        # Tính điểm ưu tiên theo quy chế mới 2026
        ut = analyzer.get_priority_points(self.hb_kv.get(), self.hb_dt.get())
        
        diem_hb_info = {
            'to_hop':         tohop,
            'mon_hoc':        TO_HOP_MON.get(tohop, []),
            'diem_tb_mon1':   m1,
            'diem_tb_mon2':   m2,
            'diem_tb_mon3':   m3,
            'diem_hb':        round(m1 + m2 + m3, 2),
            'diem_xet_tuyen': round(m1 + m2 + m3 + ut, 2),
        }
        self._set_status('Đang xử lý Học bạ…')
        self._tbl_hb.show_loading()
        self.update_idletasks()
        results = analyzer.predict_nganh(diem_hb_info, top_k=12, nguyen_vong=group)
        results = enrich_major_results(results, self._current_profile())
        self._tbl_hb.populate(results)
        self._set_status(f'Đã gợi ý {len(results)} ngành phù hợp (Học bạ)')

    # ══════════════════════════════════════════════════════════════════════
    #  PAGE – TUYỂN THẲNG
    # ══════════════════════════════════════════════════════════════════════
    def _build_page_tuyenthang(self):
        page = ScrollablePage(self._content_host)
        self._pages['Tuyển thẳng'] = page
        content = page.content
        self._build_method_page_hero(
            content,
            '🎯',
            'Xét tuyển thẳng',
            'AI tổng hợp điểm trung bình ba năm THPT và điểm tiếng Anh để gợi ý ngành theo nhóm quan tâm.',
            ('ĐTB lớp 10', 'ĐTB lớp 11', 'ĐTB lớp 12', 'Tiếng Anh'),
            'Phân tích tuyển thẳng',
            self._run_tuyenthang,
        )
        self._build_profile_strip(content)

        c_out, c_in = make_card(content, 'Thông tin tuyển thẳng', padx=20, pady=14)
        c_out.pack(fill=tk.X, pady=(0, 18))

        label_row(c_in, 'Nhóm ngành:', 0)
        self.tt_group = tk.StringVar()
        cb = styled_combo(c_in, self.tt_group, GROUP_OPTIONS, width=56)
        cb.grid(row=0, column=1, columnspan=3, sticky='ew', pady=4)

        section_sep(c_in, 1)

        self.tt_l10 = tk.StringVar(); self.tt_l11 = tk.StringVar(); self.tt_l12 = tk.StringVar()
        grade_fields = [
            ('ĐTB Lớp 10 (0–10):', self.tt_l10, 2, 0),
            ('ĐTB Lớp 11 (0–11):', self.tt_l11, 2, 2),
            ('ĐTB Lớp 12 (0–12):', self.tt_l12, 3, 0),
        ]
        for lbl, var, row, col in grade_fields:
            label_row(c_in, lbl, row, col=col)
            styled_entry(c_in, var, 12).grid(
                row=row, column=col + 1, sticky='w', pady=4)
            var.trace_add('write', self._tt_update_sum)

        self._ttSumLbl = label_row(
            c_in, 'Tổng ĐTB 3 năm (thang 30):', 3, col=2)
        self._ttSumVal = tk.Label(c_in, text='0.0', font=('Segoe UI', 11, 'bold'),
                                  bg=C['card_bg'], fg=C['accent'])
        self._ttSumVal.grid(row=3, column=3, sticky='w', pady=4)

        label_row(c_in, 'Điểm Tiếng Anh (0–10, tùy chọn):', 4)
        self.tt_anh = tk.StringVar()
        styled_entry(c_in, self.tt_anh, 12).grid(
            row=4, column=1, sticky='w', pady=4)

        btn_r = tk.Frame(c_in, bg=C['card_bg'])
        btn_r.grid(row=5, column=0, columnspan=4, sticky='w', pady=(12, 0))
        IconButton(btn_r, 'Phân tích hồ sơ', self._run_tuyenthang, width=170).pack(side=tk.LEFT)
        IconButton(btn_r, 'Xóa dữ liệu', self._clear_tuyenthang,
                   bg=C['secondary'], fg=C['text_dark'],
                   hover=C['secondary_hover'], width=125).pack(side=tk.LEFT, padx=(10, 0))

        r_out, r_in = make_card(content, 'Kết quả gợi ý ngành học', padx=12, pady=12)
        r_out.pack(fill=tk.BOTH, expand=True)
        self._tbl_tt = ResultTable(r_in)
        self._tbl_tt.pack(fill=tk.BOTH, expand=True)

    def _tt_update_sum(self, *_):
        try:
            s = sum(float(v.get() or 0) for v in (self.tt_l10, self.tt_l11, self.tt_l12))
            self._ttSumVal.config(text=f'{s:.2f}')
        except:
            self._ttSumVal.config(text='0.0')

    def _clear_tuyenthang(self):
        for v in (self.tt_l10, self.tt_l11, self.tt_l12, self.tt_anh):
            v.set('')
        self._tbl_tt.show_empty()
        self._tt_update_sum()

    def _run_tuyenthang(self):
        if tt_predict is None:
            messagebox.showerror('Lỗi', 'Không thể tải mô-đun Tuyển thẳng.')
            return
        if not self.tt_group.get().strip():
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng chọn nhóm ngành.')
            return
        try:
            tb30 = float(self.tt_l10.get() or 0) + float(self.tt_l11.get() or 0) + float(self.tt_l12.get() or 0)
            if tb30 <= 0: raise ValueError
        except Exception:
            messagebox.showwarning('Giá trị không hợp lệ', 'Vui lòng nhập điểm trung bình các năm.')
            return
        try:
            diem_anh = float(self.tt_anh.get()) if self.tt_anh.get() else 0.0
        except Exception:
            diem_anh = 0.0
        self._set_status('Đang xử lý Tuyển thẳng…')
        self._tbl_tt.show_loading()
        self.update_idletasks()
        results = tt_predict(tb30, diem_anh, self.tt_group.get().strip(), top_n=12)
        results = enrich_major_results(results, self._current_profile())
        self._tbl_tt.populate(results)
        self._set_status(f'Đã gợi ý {len(results)} ngành phù hợp (Tuyển thẳng)')

    # ══════════════════════════════════════════════════════════════════════
    #  PAGE – THPT QG (PT1)
    # ══════════════════════════════════════════════════════════════════════
    def _build_page_pt1(self):
        page = ScrollablePage(self._content_host)
        self._pages['THPT QG'] = page
        content = page.content
        self._build_method_page_hero(
            content,
            '📝',
            'Xét tuyển THPT Quốc gia',
            'Nhập điểm thi theo tổ hợp môn, hệ thống tự cộng ưu tiên và phân tích ngành phù hợp.',
            ('Tổ hợp xét tuyển', 'Điểm 3 môn', 'Ưu tiên khu vực', 'Xếp hạng ngành'),
            'Phân tích THPT',
            self._run_pt1,
        )
        self._build_profile_strip(content)

        c_out, c_in = make_card(content, 'Thông tin điểm thi THPT', padx=20, pady=14)
        c_out.pack(fill=tk.X, pady=(0, 18))

        label_row(c_in, 'Nhóm ngành:', 0)
        self.pt1_group = tk.StringVar()
        cb = styled_combo(c_in, self.pt1_group, GROUP_OPTIONS, width=56)
        cb.grid(row=0, column=1, columnspan=3, sticky='ew', pady=4)
        cb.bind('<<ComboboxSelected>>', self._on_pt1_group_changed)

        label_row(c_in, 'Tổ hợp môn:', 1)
        self.pt1_tohop = tk.StringVar()
        self.pt1_cb_tohop = styled_combo(c_in, self.pt1_tohop, [], width=16)
        self.pt1_cb_tohop.grid(row=1, column=1, sticky='w', pady=4)

        section_sep(c_in, 2)

        self._pt1_subject_labels = []
        for lbl_t, attr, r, col in [
            ('Môn 1 (0-10):', 'pt1_m1', 3, 0),
            ('Môn 2 (0-10):', 'pt1_m2', 3, 2),
            ('Môn 3 (0-10):', 'pt1_m3', 4, 0),
        ]:
            self._pt1_subject_labels.append(label_row(c_in, lbl_t, r, col=col))
            v = tk.StringVar()
            styled_entry(c_in, v, 10).grid(
                row=r, column=col + 1, sticky='w', pady=4)
            setattr(self, attr, v)
        self.pt1_tohop.trace_add(
            'write',
            lambda *_: self._refresh_subject_labels(self.pt1_tohop, self._pt1_subject_labels),
        )

        # Ưu tiên mới cho 2026
        label_row(c_in, 'Khu vực:', 4, col=2)
        self.pt1_kv = tk.StringVar(value='KV3')
        styled_combo(c_in, self.pt1_kv,
                     ['KV1', 'KV2-NT', 'KV2', 'KV3'],
                     width=10).grid(row=4, column=3, sticky='w', pady=4)

        label_row(c_in, 'Đối tượng ưu tiên:', 5)
        self.pt1_dt = tk.StringVar(value='Không ưu tiên')
        styled_combo(c_in, self.pt1_dt,
                     ['Nhóm 1 (01-04)', 'Nhóm 2 (05-07)', 'Không ưu tiên'],
                     width=24).grid(row=5, column=1, columnspan=3,
                                    sticky='w', pady=4)


        btn_r = tk.Frame(c_in, bg=C['card_bg'])
        btn_r.grid(row=6, column=0, columnspan=4, sticky='w', pady=(12, 0))
        IconButton(btn_r, 'Phân tích hồ sơ', self._run_pt1, width=170).pack(side=tk.LEFT)
        IconButton(btn_r, 'Xóa dữ liệu', self._clear_pt1,
                   bg=C['secondary'], fg=C['text_dark'],
                   hover=C['secondary_hover'], width=125).pack(side=tk.LEFT, padx=(10, 0))

        r_out, r_in = make_card(content, 'Kết quả gợi ý ngành học', padx=12, pady=12)
        r_out.pack(fill=tk.BOTH, expand=True)
        self._tbl_pt1 = ResultTable(r_in)
        self._tbl_pt1.pack(fill=tk.BOTH, expand=True)

    def _on_pt1_group_changed(self, *_):
        vals = sorted(allowed_tohops_for_group(self.pt1_group.get())
                      if callable(allowed_tohops_for_group) else set())
        self.pt1_cb_tohop['values'] = vals
        if vals:
            self.pt1_cb_tohop.set(vals[0])
        if hasattr(self, '_pt1_subject_labels'):
            self._refresh_subject_labels(self.pt1_tohop, self._pt1_subject_labels)

    def _clear_pt1(self):
        for attr in ('pt1_m1', 'pt1_m2', 'pt1_m3'):
            getattr(self, attr).set('')
        self.pt1_kv.set('KV3')
        self.pt1_dt.set('Không ưu tiên')
        self._tbl_pt1.show_empty()

    def _run_pt1(self):
        if goi_y_nganh_thpt is None:
            messagebox.showerror('Lỗi', 'Không thể tải mô-đun PT1.')
            return
        group = self.pt1_group.get().strip()
        tohop = self.pt1_tohop.get().strip().upper()
        if not group or not tohop:
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng chọn nhóm ngành và tổ hợp.')
            return
        try:
            m1 = float(self.pt1_m1.get()); m2 = float(self.pt1_m2.get())
            m3 = float(self.pt1_m3.get()); nv = 1
        except Exception:
            messagebox.showwarning('Giá trị không hợp lệ', 'Điểm phải là số hợp lệ.')
            return

        # Tính điểm ưu tiên theo quy chế mới (giảm tuyến tính cho điểm cao)
        try:
            import huit_career_advisor.inference.thpt as pt1_mod
            ut = pt1_mod.calculate_priority_pt1(m1 + m2 + m3, self.pt1_kv.get(), self.pt1_dt.get())
        except Exception:
            ut = 0.0
        self._set_status('Đang xử lý THPT QG…')
        self._tbl_pt1.show_loading()
        self.update_idletasks()
        results = goi_y_nganh_thpt(m1, m2, m3, diem_ut=ut, thu_tu_nv=nv,
                                    tohop=tohop, nguyen_vong=group, top_n=12)
        results = enrich_major_results(results, self._current_profile())
        self._tbl_pt1.populate(results)
        self._set_status(f'Đã gợi ý {len(results)} ngành phù hợp (THPT QG)')


# ══════════════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════════
    #  PAGE – CHAT AI HƯỚNG NGHIỆP
    # ══════════════════════════════════════════════════════════════════════
    def _build_page_chat(self):
        page = tk.Frame(self._content_host, bg=C['content_bg'])
        self._pages['Trợ lý AI'] = page
        self._build_method_page_hero(
            page,
            '🤖',
            'Trợ lý AI Hướng nghiệp HUIT',
            'Trao đổi trực tiếp với AI để phân tích học lực, sở thích và định hướng ngành học phù hợp.',
            ('Chat tư vấn', 'Gợi ý ngành', 'So sánh phương thức', 'Hồ sơ cá nhân'),
            'Bắt đầu chat',
            lambda: self.chat_input_entry.focus_set() if hasattr(self, 'chat_input_entry') else None,
        )

        chat_card, chat_content = make_card(page, padx=14, pady=14)
        chat_card.pack(fill=tk.BOTH, expand=True)
        self._method_card_header(
            chat_content,
            '🤖',
            'Cuộc trò chuyện hướng nghiệp',
            'AI sẽ hỏi từng bước để thu thập thông tin và đưa ra tư vấn cá nhân hóa.',
            'ai_accent',
        )

        from tkinter.scrolledtext import ScrolledText
        self.chat_log = ScrolledText(
            chat_content,
            wrap=tk.WORD,
            font=F['result'],
            bg=C['input_bg'],
            fg=C['text_dark'],
            bd=0,
            highlightthickness=0,
            insertbackground=C['accent'],
            selectbackground=C['accent_soft'],
            selectforeground=C['text_dark'],
            padx=16,
            pady=16,
        )
        self.chat_log.pack(fill=tk.BOTH, expand=True, pady=(0, 16))
        self.chat_log.configure(state='disabled')

        self._style_chat_widgets()

        input_frame = tk.Frame(chat_content, bg=C['card_bg'])
        input_frame.pack(fill=tk.X)

        self.chat_input_var = tk.StringVar()
        self.chat_input_entry = styled_entry(input_frame, self.chat_input_var, width=50)
        self.chat_input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.chat_input_entry.bind('<Return>', lambda _event: self._send_chat_message())

        IconButton(input_frame, 'Gửi', self._send_chat_message, width=96).pack(side=tk.LEFT)
        IconButton(input_frame, 'Làm mới', self._reset_chat, bg=C['secondary'], fg=C['text_dark'], hover=C['secondary_hover'], width=112).pack(side=tk.LEFT, padx=(10, 0))

        quick_frame = tk.Frame(chat_content, bg=C['card_bg'])
        quick_frame.pack(fill=tk.X, pady=(10, 0))

        prompts = [
            ("Tư vấn ngành cho tôi", "Tôi muốn tư vấn ngành học phù hợp nhất"),
            ("Học phí HUIT", "Học phí của HUIT là bao nhiêu?"),
            ("Điều kiện Tuyển thẳng", "Điều kiện để xét tuyển thẳng là gì?"),
            ("9 Nhóm ngành chính", "Kể tên 9 nhóm ngành đào tạo chính thức của HUIT"),
        ]

        for text, prompt in prompts:
            btn = tk.Label(
                quick_frame,
                text=text,
                bg=C['surface_alt'],
                fg=C['accent'],
                font=F['small_medium'],
                padx=11,
                pady=7,
                cursor='hand2',
                relief='flat',
            )
            btn.pack(side=tk.LEFT, padx=(0, 10))
            btn.bind('<Button-1>', lambda _event, p=prompt: self._send_quick_prompt(p))

            def on_enter(event, b=btn):
                b.configure(bg=C['accent_soft'])
            def on_leave(event, b=btn):
                b.configure(bg=C['surface_alt'])
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)

        self._reset_chat()

    def _reset_chat(self):
        self.chat_state = 'state_init'
        self.student_name = ""
        self.student_scores = {}
        self.student_interest = ""

        self.chat_log.configure(state='normal')
        self.chat_log.delete('1.0', tk.END)
        self.chat_log.configure(state='disabled')

        self._append_to_chat_log(
            "Trợ lý AI",
            "Xin chào! Tôi là Trợ lý Hướng nghiệp AI của trường HUIT. Tôi ở đây để hỗ trợ bạn định hướng nghề nghiệp, lựa chọn phương thức xét tuyển và các ngành học phù hợp nhất.\n\nTrước tiên, tôi có thể biết tên của bạn không?",
            is_ai=True
        )

    def _append_to_chat_log(self, sender, message, is_ai=True, is_card=False):
        self.chat_log.configure(state='normal')
        if is_card:
            self.chat_log.insert(tk.END, f"\n{message}\n\n", 'system_card')
        else:
            tag_name = 'ai_tag' if is_ai else 'student_tag'
            msg_name = 'ai_msg' if is_ai else 'student_msg'
            self.chat_log.insert(tk.END, f"\n{sender}:\n", tag_name)
            self.chat_log.insert(tk.END, f"{message}\n", msg_name)
        self.chat_log.see(tk.END)
        self.chat_log.configure(state='disabled')

    def _send_chat_message(self):
        text = self.chat_input_var.get().strip()
        if not text:
            return
        self.chat_input_var.set("")
        self._process_message(text)

    def _send_quick_prompt(self, text):
        self._process_message(text)

    def _process_message(self, text):
        self._append_to_chat_log(self.student_name or "Học sinh", text, is_ai=False)

        if self.chat_state == 'state_init':
            self.student_name = text
            self.chat_state = 'state_ask_method'
            response = (
                f"Rất vui được trò chuyện với {self.student_name}!\n\n"
                f"Để tôi có thể tư vấn tốt nhất, bạn dự kiến đăng ký xét tuyển bằng phương thức nào dưới đây?\n"
                f"1. Học bạ THPT (5 học kỳ)\n"
                f"2. Điểm thi Đánh giá năng lực (ĐGNL)\n"
                f"3. Điểm thi tốt nghiệp THPT\n"
                f"4. Xét tuyển thẳng\n\n"
                f"Hãy nhập số tương ứng (1-4) hoặc gõ tên phương thức nhé!"
            )
            self._append_to_chat_log("Trợ lý AI", response, is_ai=True)

        elif self.chat_state == 'state_ask_method':
            cleaned = text.lower()
            if "1" in cleaned or "học bạ" in cleaned or "hoc ba" in cleaned:
                self.student_scores['method'] = "Học bạ"
                response = f"Bạn chọn xét tuyển bằng Học bạ THPT. {self.student_name} có thể cho tôi biết tổng điểm trung bình 3 môn trong tổ hợp xét tuyển của bạn khoảng bao nhiêu? (VD: 24.5 hoặc nhập điểm 3 môn lẻ như 8, 8.5, 9)"
            elif "2" in cleaned or "đgnl" in cleaned or "dgnl" in cleaned or "năng lực" in cleaned:
                self.student_scores['method'] = "ĐGNL"
                response = f"Bạn chọn xét tuyển bằng điểm thi ĐGNL. Điểm thi dự kiến của {self.student_name} là bao nhiêu (thang điểm 600 - 1200)? (VD: 850)"
            elif "3" in cleaned or "thpt" in cleaned or "thi tốt nghiệp" in cleaned:
                self.student_scores['method'] = "THPT QG"
                response = f"Bạn chọn xét tuyển bằng điểm thi THPT. Tổng điểm dự kiến 3 môn thi của {self.student_name} là bao nhiêu? (VD: 23.0)"
            elif "4" in cleaned or "tuyển thẳng" in cleaned or "tuyen thang" in cleaned:
                self.student_scores['method'] = "Tuyển thẳng"
                response = f"Bạn chọn xét tuyển thẳng. Điểm trung bình cả năm lớp 12 (hoặc 3 năm) của {self.student_name} là bao nhiêu? (VD: 8.7)"
            else:
                self.student_scores['method'] = "Học bạ"
                response = f"Tôi sẽ chọn phương thức Học bạ nhé. {self.student_name} cho biết tổng điểm học bạ dự kiến của bạn là bao nhiêu? (VD: 24.5)"

            self.chat_state = 'state_ask_score'
            self._append_to_chat_log("Trợ lý AI", response, is_ai=True)

        elif self.chat_state == 'state_ask_score':
            import re
            numbers = re.findall(r'\d+\.\d+|\d+', text)
            score_val = 0.0
            if numbers:
                try:
                    if len(numbers) >= 3:
                        score_val = sum(float(x) for x in numbers[:3])
                    else:
                        score_val = float(numbers[0])
                        if score_val <= 10.0 and self.student_scores['method'] in ("Học bạ", "THPT QG"):
                            score_val = score_val * 3.0
                except ValueError:
                    score_val = 24.0
            else:
                score_val = 24.0

            self.student_scores['score'] = score_val
            self.chat_state = 'state_ask_interests'

            response = (
                f"Đã ghi nhận mức điểm dự kiến của {self.student_name} là: {score_val}.\n\n"
                f"Tiếp theo, bạn quan tâm hoặc có sở thích đối với lĩnh vực nào nhất trong số các lĩnh vực sau?\n"
                f"A. Công nghệ thông tin / Dữ liệu / Trí tuệ nhân tạo\n"
                f"B. Kinh doanh / Marketing / Quản trị\n"
                f"C. Kỹ thuật / Cơ khí / Tự động hóa\n"
                f"D. Công nghệ thực phẩm / Dinh dưỡng\n"
                f"E. Hóa học / Sinh học / Môi trường\n"
                f"F. Du lịch / Nhà hàng / Khách sạn\n"
                f"G. Kế toán / Tài chính / Ngân hàng\n"
                f"H. Luật / Xã hội / Ngôn ngữ\n"
                f"I. Logistics / Chuỗi cung ứng\n\n"
                f"Hãy chọn chữ cái (A-I) tương ứng nhé!"
            )
            self._append_to_chat_log("Trợ lý AI", response, is_ai=True)

        elif self.chat_state == 'state_ask_interests':
            cleaned = text.lower()
            interest_map = {
                'a': "Công nghệ thông tin - Trí tuệ nhân tạo - Dữ liệu",
                'b': "Kinh doanh - Quản trị - Marketing",
                'c': "Kỹ thuật - Cơ khí - Tự động hóa",
                'd': "Công nghệ - Chế biến - Thực phẩm",
                'e': "Hóa học - Sinh học - Môi trường - Vật liệu",
                'f': "Du lịch - Nhà hàng - Khách sạn - Dịch vụ",
                'g': "Kế toán - Tài chính - Ngân hàng",
                'h': "Luật - Xã hội - Ngôn ngữ",
                'i': "Logistics - Quản lý chuỗi cung ứng - Kinh doanh chuyên biệt",
            }
            selected_interest = ""
            for key, val in interest_map.items():
                if key in cleaned or val.lower() in cleaned:
                    selected_interest = val
                    break
            if not selected_interest:
                selected_interest = interest_map['a']

            self.student_interest = selected_interest
            self.chat_state = 'state_qa'

            self._append_to_chat_log("Trợ lý AI", f"Tuyệt vời! Cảm ơn {self.student_name}. Dựa trên điểm số và sở thích bạn cung cấp, tôi đã chạy mô hình ML và phân tích hồ sơ hướng nghiệp cho bạn. Dưới đây là báo cáo tổng hợp dành riêng cho bạn:", is_ai=True)
            self._generate_ai_recommendations()

        else:
            self._process_free_qa(text)

    def _generate_ai_recommendations(self):
        method = self.student_scores.get('method', 'Học bạ')
        score = self.student_scores.get('score', 24.0)
        interest = self.student_interest

        results = []
        if method == "ĐGNL" and dgnl_predict:
            results = dgnl_predict(score, diem_dt=0, diem_kv=0, thu_tu_nv=1, nguyen_vong=interest, top_n=5)
        elif method == "Học bạ" and HocBaAnalyzer:
            analyzer = HocBaAnalyzer()
            if analyzer.load_models():
                m1 = m2 = m3 = round(score / 3.0, 2)
                diem_hb_info = {
                    'to_hop': 'D01',
                    'mon_hoc': ['Toán', 'Văn', 'Anh'],
                    'diem_tb_mon1': m1,
                    'diem_tb_mon2': m2,
                    'diem_tb_mon3': m3,
                    'diem_hb': score,
                    'diem_xet_tuyen': score,
                }
                results = analyzer.predict_nganh(diem_hb_info, top_k=5, nguyen_vong=interest)
        elif method == "THPT QG" and goi_y_nganh_thpt:
            m1 = m2 = m3 = round(score / 3.0, 2)
            results = goi_y_nganh_thpt(m1, m2, m3, diem_ut=0.0, thu_tu_nv=1, tohop='D01', nguyen_vong=interest, top_n=5)
        elif tt_predict:
            results = tt_predict(score, diem_anh=0.0, nguyen_vong=interest, top_n=5)

        self.profile_interest.set(interest)
        results = enrich_major_results(results, self._current_profile())

        card_text = f"📊 BÁO CÁO TƯ VẤN HƯỚNG NGHIỆP HUIT (Họ tên: {self.student_name})\n"
        card_text += f"──────────────────────────────────────────────────\n"
        card_text += f"• Nhóm ngành ưu tiên: {interest}\n"
        card_text += f"• Điểm số dự kiến: {score} ({method})\n"

        ov_scores = {'dgnl': None, 'hoc_ba': None, 'thpt': None, 'tuyen_thang': None}
        if method == "ĐGNL":
            ov_scores['dgnl'] = score
            ov_scores['hoc_ba'] = [7.5, 7.5, 7.5]
            ov_scores['thpt'] = [7.5, 7.5, 7.5]
        elif method == "Học bạ":
            m_val = score / 3.0
            ov_scores['hoc_ba'] = [m_val, m_val, m_val]
            ov_scores['thpt'] = [max(0, m_val - 0.5), max(0, m_val - 0.5), max(0, m_val - 0.5)]
        elif method == "THPT QG":
            m_val = score / 3.0
            ov_scores['thpt'] = [m_val, m_val, m_val]
            ov_scores['hoc_ba'] = [min(10, m_val + 0.3), min(10, m_val + 0.3), min(10, m_val + 0.3)]
        else:
            ov_scores['tuyen_thang'] = [score/3.0, score/3.0, score/3.0]

        ranked_methods = rank_admission_methods(ov_scores)
        best_method = ranked_methods[0]['method'] if ranked_methods else method

        card_text += f"• Đánh giá mức độ sẵn sàng các phương thức xét tuyển:\n"
        for idx, rm in enumerate(ranked_methods[:2], 1):
            rec_str = " (Khuyên dùng)" if rm['recommended'] else ""
            card_text += f"   {idx}. {rm['method']}: {rm['score']}% - {rm['level']}{rec_str}\n"

        card_text += f"\n🎯 TOP 3 NGÀNH ĐỀ XUẤT PHÙ HỢP NHẤT:\n"
        for idx, r in enumerate(results[:3], 1):
            suitability = f"{r.get('xac_suat', 50):.1f}%"
            reasons = ", ".join(r.get('ly_do_ho_tro', []))
            reasons_str = f" ({reasons})" if reasons else ""
            card_text += f"   {idx}. {r.get('ten_nganh')} - Mã ngành: {r.get('ma_nganh')}\n"
            card_text += f"      Độ phù hợp: {suitability}{reasons_str}\n"

        card_text += f"──────────────────────────────────────────────────\n"
        card_text += f"💡 Lời khuyên: Bạn có độ phù hợp cao tại nhóm ngành {interest}. Hãy đăng ký xét tuyển sớm bằng phương thức {best_method} để tăng tối đa cơ hội trúng tuyển HUIT!"

        self._append_to_chat_log("Hệ thống Hướng nghiệp", card_text, is_ai=True, is_card=True)

        followup = (
            f"Báo cáo hướng nghiệp đã sẵn sàng! Bây giờ, {self.student_name} có thể hỏi tôi bất kỳ câu hỏi nào "
            f"về các ngành học đề xuất, học phí, chương trình đào tạo hoặc ký túc xá tại HUIT..."
        )
        self._append_to_chat_log("Trợ lý AI", followup, is_ai=True)

    def _process_free_qa(self, text):
        cleaned = text.lower()
        if "học phí" in cleaned or "hoc phi" in cleaned or "tiền học" in cleaned:
            response = (
                "Học phí tại Trường Đại học Công Thương TP.HCM (HUIT) được tính theo tín chỉ thực tế:\n"
                "- Các ngành thuộc khối Kinh tế, Luật, Ngôn ngữ: khoảng 26 - 28 triệu đồng / năm học.\n"
                "- Các ngành thuộc khối Kỹ thuật, Công nghệ thông tin, Thực phẩm: khoảng 28 - 30 triệu đồng / năm học.\n"
                "Lộ trình tăng học phí được cam kết không quá 10% mỗi năm theo đúng quy định."
            )
        elif "công nghệ thông tin" in cleaned or "cntt" in cleaned or "an toàn thông tin" in cleaned or "khoa học dữ liệu" in cleaned:
            response = (
                "Nhóm ngành Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu là ngành thế mạnh của HUIT:\n"
                "- Bao gồm: Công nghệ thông tin (7480201), An toàn thông tin (7480202) và Khoa học dữ liệu (7460108).\n"
                "- Điểm chuẩn xét học bạ dao động khoảng 22 - 25 điểm. Điểm thi tốt nghiệp THPT khoảng 20 - 23 điểm.\n"
                "- Cơ hội việc làm rộng mở nhờ sự liên kết đào tạo chặt chẽ giữa nhà trường với nhiều doanh nghiệp công nghệ lớn."
            )
        elif "thực phẩm" in cleaned or "dinh dưỡng" in cleaned or "chế biến" in cleaned:
            response = (
                "Trường HUIT (trước đây là trường Thực phẩm) tự hào có truyền thống lâu đời nhất về ngành Thực phẩm:\n"
                "- Các ngành: Công nghệ Thực phẩm (7540101), Đảm bảo chất lượng & An toàn thực phẩm (7540106), Công nghệ chế biến thủy sản (7540105), Khoa học dinh dưỡng và ẩm thực (7819009).\n"
                "- Điểm chuẩn học bạ thường ở mức khá cao (24 - 26 điểm). Điểm thi THPT khoảng 21 - 24 điểm.\n"
                "- Trường trang bị nhiều xưởng thực nghiệm quy mô bán công nghiệp phục vụ việc thực hành trực tiếp."
            )
        elif "tuyển thẳng" in cleaned or "tuyen thang" in cleaned or "học lực giỏi" in cleaned:
            response = (
                "Chính sách xét tuyển thẳng tại HUIT:\n"
                "1. Học sinh đạt giải các kỳ thi Học sinh giỏi quốc gia, Khoa học kỹ thuật quốc gia.\n"
                "2. Thí sinh tốt nghiệp THPT đạt học lực Giỏi 3 năm liên tiếp.\n"
                "3. Thí sinh có chứng chỉ IELTS từ 5.5 trở lên kết hợp với kết quả học bạ đạt loại Khá trở lên ở lớp 12."
            )
        elif "ký túc xá" in cleaned or "ktx" in cleaned or "chỗ ở" in cleaned:
            response = (
                "Ký túc xá của HUIT sạch sẽ, khép kín và an ninh tuyệt đối:\n"
                "- Vị trí thuận tiện, phòng từ 4 - 8 sinh viên đầy đủ tiện nghi cơ bản.\n"
                "- Chi phí KTX rất rẻ, khoảng 250.000đ - 450.000đ/tháng/sinh viên.\n"
                "- Có chính sách ưu tiên xét chỗ ở cho tân sinh viên khó khăn hoặc diện chính sách."
            )
        elif "học bạ" in cleaned or "xét học bạ" in cleaned:
            response = (
                "Thông tin xét học bạ HUIT:\n"
                "- Tính tổng điểm trung bình cộng 3 môn theo tổ hợp của 5 học kỳ THPT (cả năm Lớp 10, Lớp 11 và Học kỳ 1 Lớp 12).\n"
                "- Ngưỡng nhận hồ sơ đăng ký xét tuyển tối thiểu là 18.0 điểm.\n"
                "- Phương thức này giúp các thí sinh giảm áp lực thi cử và đăng ký xét tuyển trực tuyến tiện lợi."
            )
        elif "ngôn ngữ" in cleaned or "tiếng anh" in cleaned or "tiếng trung" in cleaned:
            response = (
                "HUIT đào tạo 2 ngành Ngôn ngữ chính quy:\n"
                "- Ngôn ngữ Anh (7220201) và Ngôn ngữ Trung Quốc (7220204).\n"
                "- Xét tuyển qua các tổ hợp: D01 (Toán, Văn, Anh), A01 (Toán, Lý, Anh), D09 (Toán, Sử, Anh), D14 (Văn, Sử, Anh).\n"
                "- Chương trình học hướng tới kỹ năng giao tiếp tự tin, thương mại quốc tế và cơ hội thực tập nước ngoài."
            )
        elif "du lịch" in cleaned or "khách sạn" in cleaned or "nhà hàng" in cleaned:
            response = (
                "Khối ngành Du lịch - Khách sạn tại HUIT sở hữu mạng lưới đối tác khách sạn 4-5 sao rộng khắp:\n"
                "- Các ngành: Du lịch (7810101), Quản trị dịch vụ du lịch và lữ hành (7810103), Quản trị khách sạn (7810201), Quản trị nhà hàng và dịch vụ ăn uống (7810202).\n"
                "- Sinh viên được thực hành tại nhà hàng, quầy bar, buồng phòng đạt tiêu chuẩn khách sạn cao cấp ngay tại khu thực hành của trường."
            )
        elif "kinh doanh" in cleaned or "marketing" in cleaned or "quản trị" in cleaned:
            response = (
                "Nhóm ngành Kinh doanh của HUIT có chương trình học cập nhật xu hướng thị trường:\n"
                "- Bao gồm: Quản trị kinh doanh (7340101), Marketing (7340115), Kinh doanh quốc tế (7340120), Thương mại điện tử (7340122).\n"
                "- Điểm chuẩn học bạ dao động khoảng 23 - 25 điểm.\n"
                "- Sinh viên được cọ xát qua các cuộc thi khởi nghiệp và thực hành giải bài toán kinh doanh thực tế."
            )
        else:
            response = (
                f"Cảm ơn câu hỏi của {self.student_name}. Để cập nhật các thông tin tuyển sinh mới nhất và chính xác nhất "
                f"của trường Đại học Công Thương TP.HCM (HUIT), bạn có thể truy cập website: https://tuyensinh.huit.edu.vn "
                f"hoặc gọi trực tiếp đến tổng đài tư vấn: 028.3816.1673."
            )
        self._append_to_chat_log("Trợ lý AI", response, is_ai=True)



if __name__ == '__main__':
    app = App()
    app.mainloop()
