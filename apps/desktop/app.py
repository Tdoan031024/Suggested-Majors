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
import threading

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
        self._fixed_height = None
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
            12,
            8,
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
        requested = self._fixed_height or max(96, self._inner.winfo_reqheight() + 32)
        current_req = self._canvas.winfo_reqheight()
        if abs(current_req - requested) > 2:
            self.configure(height=requested)
            self._canvas.configure(height=requested)
        self._redraw()

    def set_fixed_height(self, height):
        try:
            # Tự động điều chỉnh kích thước theo tỉ lệ DPI của màn hình
            scaling = self.winfo_fpixels('1i') / 96.0
            scaled_height = int(height * scaling)
        except Exception:
            scaled_height = height
        self._fixed_height = scaled_height
        self.configure(height=scaled_height)
        self._canvas.configure(height=scaled_height)
        self._redraw()

    def _redraw(self, event=None):
        width = event.width if event else self.winfo_width()
        height = event.height if event else self._fixed_height or max(self._inner.winfo_reqheight() + 32, 96)
        self._canvas.delete('card')
        self._canvas.configure(bg=self.master.cget('bg'))
        rounded_rect(
            self._canvas,
            12,
            14,
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
            max(2, width - 12),
            max(2, height - 14),
            self._radius,
            fill=C[self._fill_key],
            outline='',
            tags='card',
        )
        self._canvas.tag_lower('card')
        self._canvas.coords(self._window, 12, 8)
        self._canvas.itemconfigure(
            self._window,
            width=max(10, width - 30),
            height=max(10, height - 30),
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


class SoftDivider(tk.Canvas):
    """Minimal divider used to separate app chrome regions."""

    def __init__(self, parent, orientation='horizontal'):
        self._orientation = orientation
        width = 1 if orientation == 'vertical' else 1
        height = 1 if orientation == 'horizontal' else 1
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=C['content_bg'],
            highlightthickness=0,
            bd=0,
        )
        self.bind('<Configure>', self._draw)

    def _draw(self, event=None):
        width = event.width if event else max(self.winfo_width(), 1)
        height = event.height if event else max(self.winfo_height(), 1)
        self.delete('all')
        self.configure(bg=C['content_bg'])
        if self._orientation == 'horizontal':
            self.create_rectangle(0, 0, width, height, fill=C['content_bg'], outline='')
            self.create_line(0, 0, width, 0, fill=C['sep'], width=1)
            return

        self.create_rectangle(0, 0, width, height, fill=C['content_bg'], outline='')
        self.create_line(0, 0, 0, height, fill=C['sep'], width=1)

    def apply_theme(self):
        self._draw()


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
        ('prob',  'Đánh giá',   110,  tk.CENTER),
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
            probability_text = 'Phù hợp'
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


# ── Windows Credential Manager Helpers ─────────────────────────────────────
def _win_save_api_key(api_key):
    if sys.platform != 'win32':
        return False
    try:
        import ctypes
        from ctypes import wintypes
        
        class CREDENTIAL_ATTRIBUTE(ctypes.Structure):
            _fields_ = [
                ('Keyword', wintypes.LPWSTR),
                ('Flags', wintypes.DWORD),
                ('ValueSize', wintypes.DWORD),
                ('Value', ctypes.POINTER(ctypes.c_byte))
            ]

        class CREDENTIAL(ctypes.Structure):
            _fields_ = [
                ('Flags', wintypes.DWORD),
                ('Type', wintypes.DWORD),
                ('TargetName', wintypes.LPWSTR),
                ('Comment', wintypes.LPWSTR),
                ('LastWritten', wintypes.FILETIME),
                ('CredentialBlobSize', wintypes.DWORD),
                ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
                ('Persist', wintypes.DWORD),
                ('AttributeCount', wintypes.DWORD),
                ('Attributes', ctypes.POINTER(CREDENTIAL_ATTRIBUTE)),
                ('TargetAlias', wintypes.LPWSTR),
                ('UserName', wintypes.LPWSTR)
            ]

        target = "HUIT_Career_Advisor_Gemini_Key"
        blob = api_key.encode('utf-16le')
        blob_len = len(blob)
        
        blob_type = ctypes.c_byte * blob_len
        blob_data = blob_type.from_buffer_copy(blob)
        
        cred = CREDENTIAL()
        cred.Flags = 0
        cred.Type = 1 # CRED_TYPE_GENERIC
        cred.TargetName = target
        cred.Comment = "Gemini API Key for HUIT Career Advisor"
        cred.Persist = 2 # CRED_PERSIST_LOCAL_MACHINE
        cred.CredentialBlobSize = blob_len
        cred.CredentialBlob = ctypes.cast(blob_data, ctypes.POINTER(ctypes.c_byte))
        cred.UserName = "HUIT_AI_User"
        
        advapi32 = ctypes.windll.advapi32
        advapi32.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wintypes.DWORD]
        advapi32.CredWriteW.restype = wintypes.BOOL
        
        res = advapi32.CredWriteW(ctypes.byref(cred), 0)
        return bool(res)
    except Exception as e:
        print(f"Error saving API key to Windows Credential Store: {e}")
        return False

def _win_load_api_key():
    if sys.platform != 'win32':
        return ""
    try:
        import ctypes
        from ctypes import wintypes
        
        class CREDENTIAL_ATTRIBUTE(ctypes.Structure):
            _fields_ = [
                ('Keyword', wintypes.LPWSTR),
                ('Flags', wintypes.DWORD),
                ('ValueSize', wintypes.DWORD),
                ('Value', ctypes.POINTER(ctypes.c_byte))
            ]

        class CREDENTIAL(ctypes.Structure):
            _fields_ = [
                ('Flags', wintypes.DWORD),
                ('Type', wintypes.DWORD),
                ('TargetName', wintypes.LPWSTR),
                ('Comment', wintypes.LPWSTR),
                ('LastWritten', wintypes.FILETIME),
                ('CredentialBlobSize', wintypes.DWORD),
                ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
                ('Persist', wintypes.DWORD),
                ('AttributeCount', wintypes.DWORD),
                ('Attributes', ctypes.POINTER(CREDENTIAL_ATTRIBUTE)),
                ('TargetAlias', wintypes.LPWSTR),
                ('UserName', wintypes.LPWSTR)
            ]

        target = "HUIT_Career_Advisor_Gemini_Key"
        advapi32 = ctypes.windll.advapi32
        
        advapi32.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
        advapi32.CredReadW.restype = wintypes.BOOL
        advapi32.CredFree.argtypes = [ctypes.c_void_p]
        advapi32.CredFree.restype = None
        
        cred_ptr = ctypes.POINTER(CREDENTIAL)()
        res = advapi32.CredReadW(target, 1, 0, ctypes.byref(cred_ptr))
        if res and cred_ptr:
            cred = cred_ptr.contents
            blob_size = cred.CredentialBlobSize
            blob_ptr = ctypes.cast(cred.CredentialBlob, ctypes.POINTER(ctypes.c_char))
            blob_bytes = ctypes.string_at(blob_ptr, blob_size)
            api_key = blob_bytes.decode('utf-16le')
            advapi32.CredFree(cred_ptr)
            return api_key
    except Exception as e:
        print(f"Error loading API key from Windows Credential Store: {e}")
    return ""

def _win_delete_api_key():
    if sys.platform != 'win32':
        return False
    try:
        import ctypes
        from ctypes import wintypes
        advapi32 = ctypes.windll.advapi32
        advapi32.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        advapi32.CredDeleteW.restype = wintypes.BOOL
        res = advapi32.CredDeleteW("HUIT_Career_Advisor_Gemini_Key", 1, 0)
        return bool(res)
    except Exception as e:
        print(f"Error deleting API key from Windows Credential Store: {e}")
        return False


class App(tk.Tk):

    def __init__(self):
        if sys.platform == 'win32':
            try:
                import ctypes
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per-Monitor DPI aware
                except Exception:
                    try:
                        ctypes.windll.shcore.SetProcessDpiAwareness(1) # System DPI aware
                    except Exception:
                        try:
                            ctypes.windll.user32.SetProcessDPIAware()
                        except Exception:
                            pass
                
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
        settings = self._load_settings()
        init_key = ""
        if sys.platform == 'win32' and settings.get('gemini_api_key_secured', False):
            init_key = _win_load_api_key()
        if not init_key:
            init_key = settings.get('gemini_api_key', '')
        self.gemini_api_key = tk.StringVar(value=init_key)
        self.gemini_api_key.trace_add('write', lambda *_: self._update_api_key(self.gemini_api_key.get()))
        self.gemini_consent_given = settings.get('gemini_consent_given', False)
        self.profile_interest = tk.StringVar(value=NONE_OPTION)
        self.profile_family = tk.StringVar(value=NONE_OPTION)
        self.profile_geography = tk.StringVar(value=GEOGRAPHY_OPTIONS[0])
        self.profile_economy = tk.StringVar(value=ECONOMY_OPTIONS[0])
        self.profile_personality = tk.StringVar(value=PERSONALITY_OPTIONS[0])
        self.profile_mobility = tk.StringVar(value=MOBILITY_OPTIONS[0])
        self.profile_interest_display = tk.StringVar(value='Chưa xác định')
        self.profile_career_goal = tk.StringVar(value='Dễ xin việc')
        self.profile_geography_display = tk.StringVar(value='Đô thị lớn')
        self.profile_mobility_display = tk.StringVar(value='Sẵn sàng học xa nhà')
        self.profile_family_display = tk.StringVar(value='Không xác định')
        self.profile_learning_style = tk.StringVar(value='Học qua dự án')
        self.profile_work_environment = tk.StringVar(value='Văn phòng')
        self._selected_profile_traits = set()
        self._profile_trait_chips = {}
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
        for variable in (
            self.profile_interest_display,
            self.profile_geography_display,
            self.profile_mobility_display,
            self.profile_family_display,
        ):
            variable.trace_add('write', self._sync_orientation_profile)
        self._sync_orientation_profile()
        self._update_profile_summary()

    def _update_api_key(self, value):
        val = value.strip()
        if not val:
            if sys.platform == 'win32':
                _win_delete_api_key()
                self._save_setting('gemini_api_key_secured', False)
            self._save_setting('gemini_api_key', '')
        else:
            if sys.platform == 'win32':
                success = _win_save_api_key(val)
                if success:
                    self._save_setting('gemini_api_key_secured', True)
                    self._save_setting('gemini_api_key', '')
                    return
            self._save_setting('gemini_api_key', val)
            self._save_setting('gemini_api_key_secured', False)

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

    def _load_settings(self):
        try:
            path = self._settings_path()
            if path.exists():
                return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            pass
        return {}

    def _save_setting(self, key, value):
        try:
            settings = self._load_settings()
            settings[key] = value
            path = self._settings_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(settings, ensure_ascii=False, indent=4),
                encoding='utf-8',
            )
        except Exception:
            pass

    def _load_theme_preference(self):
        # Mặc định khởi động luôn sử dụng giao diện sáng
        return 'light'

    def _save_theme_preference(self):
        self._save_setting('theme', self._theme_name)

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
        self._sidebar_separator = SoftDivider(body, orientation='vertical')
        self._sidebar_separator.pack(side=tk.LEFT, fill=tk.Y)
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
        self._build_page_settings()

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
        logo_right = tk.Frame(hdr, bg=C['header_bg'], width=42, height=42)
        logo_right.pack(side=tk.RIGHT, padx=(10, 24))
        logo_right.pack_propagate(False)
        self._header_right_logo = self._header_logo
        if self._header_right_logo is not None:
            tk.Label(
                logo_right,
                image=self._header_right_logo,
                bg=C['header_bg'],
                bd=0,
            ).pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(
                logo_right,
                text='H',
                bg=C['accent'],
                fg='#FFFFFF',
                font=('Segoe UI', 14, 'bold'),
            ).pack(fill=tk.BOTH, expand=True)

        clock = tk.Frame(hdr, bg=C['surface_alt'], padx=14, pady=8)
        clock.pack(side=tk.RIGHT, padx=(10, 24))
        tk.Label(clock, textvariable=self._clock_var,
                 font=F['small'], bg=C['surface_alt'], fg=C['text_muted']).pack()
        self._build_theme_toggle(hdr)
        self._tick()
        self._header_separator = SoftDivider(self, orientation='horizontal')
        self._header_separator.pack(fill=tk.X)

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
        for attr in ('_header_separator', '_sidebar_separator'):
            separator = getattr(self, attr, None)
            if separator is not None:
                separator.apply_theme()
        for trait in getattr(self, '_profile_trait_chips', {}):
            self._draw_profile_chip(trait)
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
        elif isinstance(widget, SoftDivider):
            widget.apply_theme()
        for child in widget.winfo_children():
            self._apply_component_theme(child)

    def _style_chat_widgets(self):
        if not hasattr(self, 'chat_log'):
            return
        try:
            self.chat_log.configure(
                bg=C['surface_alt'],
                fg=C['text_dark'],
                insertbackground=C['accent'],
                selectbackground=C['accent_soft'],
                selectforeground=C['text_dark'],
            )
            self.chat_log.tag_configure(
                'student_tag', font=F['label_b'], foreground=C['accent'])
            self.chat_log.tag_configure(
                'student_msg', font=F['label'], foreground=C['text_dark'],
                lmargin1=120, rmargin=18, spacing1=4, spacing3=12)
            self.chat_log.tag_configure(
                'ai_tag', font=F['label_b'], foreground=C['ai_accent'])
            self.chat_log.tag_configure(
                'ai_msg', font=F['label'], foreground=C['text_dark'],
                lmargin1=18, rmargin=120, spacing1=4, spacing3=12)
            self.chat_log.tag_configure(
                'system_card', font=F['result'], foreground=C['text_muted'],
                background=C['card_bg'], lmargin1=24, rmargin=24,
                spacing1=8, spacing3=8)
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
                if name == 'Cài đặt' and hasattr(self, 'settings_consent_var'):
                    self.settings_consent_var.set(
                        'Đã đồng ý chia sẻ dữ liệu' if getattr(self, 'gemini_consent_given', False) else 'Chưa đồng ý (Sử dụng AI offline)'
                    )
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
            ('Sở thích cá nhân:', self.profile_interest, group_values, 0, 0, 34, 'readonly'),
            ('Nghề nghiệp gia đình:', self.profile_family, group_values, 0, 2, 34, 'readonly'),
            ('Nơi sinh sống:', self.profile_geography, GEOGRAPHY_OPTIONS, 1, 0, 24, 'readonly'),
            ('Kinh tế địa phương:', self.profile_economy, ECONOMY_OPTIONS, 1, 2, 27, 'readonly'),
            ('Đặc điểm cá nhân:', self.profile_personality, PERSONALITY_OPTIONS, 2, 0, 24, 'normal'),
            ('Điều kiện học xa:', self.profile_mobility, MOBILITY_OPTIONS, 2, 2, 27, 'readonly'),
        ]
        for label, variable, values, row, column, width, state in fields:
            label_row(parent, label, start_row + row, col=column)
            styled_combo(
                parent,
                variable,
                values,
                width=width,
                state=state,
            ).grid(
                row=start_row + row,
                column=column + 1,
                sticky='ew',
                padx=(0, 14) if column == 0 else 0,
                pady=4,
            )
        return start_row + 3

    @staticmethod
    def _profile_group_by_keyword(*keywords):
        for group in GROUP_OPTIONS:
            normalized = group.lower()
            if any(keyword.lower() in normalized for keyword in keywords):
                return group
        return NONE_OPTION

    def _sync_orientation_profile(self, *_):
        interest_map = {
            'Công nghệ thông tin': self._profile_group_by_keyword('công nghệ thông tin'),
            'Kỹ thuật': self._profile_group_by_keyword('kỹ thuật'),
            'Kinh doanh': self._profile_group_by_keyword('kinh doanh', 'quản trị'),
            'Marketing': self._profile_group_by_keyword('marketing'),
            'Du lịch': self._profile_group_by_keyword('du lịch'),
            'Thực phẩm': self._profile_group_by_keyword('thực phẩm'),
            'Y tế': self._profile_group_by_keyword('hóa học', 'sinh học'),
            'Giáo dục': self._profile_group_by_keyword('luật', 'xã hội', 'ngôn ngữ'),
            'Nghệ thuật': self._profile_group_by_keyword('marketing'),
            'Chưa xác định': NONE_OPTION,
        }
        family_map = {
            'Kinh doanh': self._profile_group_by_keyword('kinh doanh', 'quản trị'),
            'Giáo viên': self._profile_group_by_keyword('luật', 'xã hội', 'ngôn ngữ'),
            'Công chức': self._profile_group_by_keyword('luật', 'xã hội'),
            'Kỹ sư': self._profile_group_by_keyword('kỹ thuật'),
            'Bác sĩ': self._profile_group_by_keyword('hóa học', 'sinh học'),
            'Nông nghiệp': self._profile_group_by_keyword('thực phẩm'),
            'Thủy sản': self._profile_group_by_keyword('thực phẩm'),
            'Công nhân': self._profile_group_by_keyword('kỹ thuật'),
            'Không xác định': NONE_OPTION,
        }
        geography_map = {
            'Đô thị lớn': 'Đô thị lớn',
            'Đô thị vừa': 'Thị xã / ven đô',
            'Nông thôn': 'Nông thôn',
            'Miền núi': 'Vùng xa / khó khăn',
            'Ven biển': 'Thị xã / ven đô',
            'Khu công nghiệp': 'Thị xã / ven đô',
        }
        economy_map = {
            'Đô thị lớn': 'Công nghệ số - thương mại',
            'Đô thị vừa': 'Đa dạng',
            'Nông thôn': 'Nông nghiệp - thực phẩm',
            'Miền núi': 'Nông nghiệp - thực phẩm',
            'Ven biển': 'Dịch vụ - du lịch',
            'Khu công nghiệp': 'Công nghiệp - sản xuất',
        }
        mobility_map = {
            'Chỉ học gần nhà': 'Cần học gần nhà',
            'Có thể học trong tỉnh': 'Ưu tiên trường trong khu vực',
            'Có thể học tại TP.HCM hoặc Hà Nội': 'Ưu tiên trường trong khu vực',
            'Sẵn sàng học xa nhà': 'Sẵn sàng học xa nhà',
        }
        self.profile_interest.set(interest_map.get(self.profile_interest_display.get(), NONE_OPTION))
        self.profile_family.set(family_map.get(self.profile_family_display.get(), NONE_OPTION))
        self.profile_geography.set(geography_map.get(self.profile_geography_display.get(), GEOGRAPHY_OPTIONS[0]))
        self.profile_economy.set(economy_map.get(self.profile_geography_display.get(), ECONOMY_OPTIONS[0]))
        self.profile_mobility.set(mobility_map.get(self.profile_mobility_display.get(), MOBILITY_OPTIONS[0]))

    def _sync_profile_traits(self):
        if not self._selected_profile_traits:
            self.profile_personality.set(PERSONALITY_OPTIONS[0])
            return
        trait_text = ' '.join(self._selected_profile_traits)
        if any(key in trait_text for key in ('logic', 'nghiên cứu')):
            self.profile_personality.set('Phân tích - công nghệ')
        elif any(key in trait_text for key in ('sáng tạo', 'giao tiếp', 'nhóm')):
            self.profile_personality.set('Sáng tạo - giao tiếp')
        elif any(key in trait_text for key in ('lãnh đạo', 'tỉ mỉ')):
            self.profile_personality.set('Tổ chức - kinh doanh')
        elif 'ngoài trời' in trait_text:
            self.profile_personality.set('Thực hành - kỹ thuật')
        else:
            self.profile_personality.set(PERSONALITY_OPTIONS[0])

    def _profile_field(self, parent, label, variable, values, row, column):
        tk.Label(
            parent,
            text=label,
            bg=C['card_bg'],
            fg=C['text_dark'],
            font=F['label_b'],
            anchor='w',
        ).grid(row=row * 2, column=column, sticky='w', pady=(0, 6))
        styled_combo(parent, variable, values, width=24).grid(
            row=row * 2 + 1,
            column=column,
            sticky='ew',
            padx=(0, 14) if column == 0 else 0,
            pady=(0, 14),
        )

    def _profile_group_card(self, parent, row, column, title, subtitle='', columnspan=1, icon=''):
        card = RoundedCard(parent, padx=22, pady=18, radius=20)
        content = card.content
        card.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky='nsew',
            padx=(0, 12) if column == 0 and columnspan == 1 else (12, 0) if column == 1 else 0,
            pady=(0, 18),
        )
        head = tk.Frame(content, bg=C['card_bg'])
        head.pack(fill=tk.X, pady=(0, 8))
        if icon:
            tk.Label(
                head,
                text=icon,
                bg=C['accent_soft'],
                fg=C['accent'],
                font=('Segoe UI Emoji', 15),
                width=3,
            ).pack(side=tk.LEFT, padx=(0, 10), ipady=4)
        title_box = tk.Frame(head, bg=C['card_bg'])
        title_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(
            title_box,
            text=title,
            bg=C['card_bg'],
            fg=C['text_dark'],
            font=F['section'],
            anchor='w',
        ).pack(anchor=tk.W)
        if subtitle:
            tk.Label(
                title_box,
                text=subtitle,
                bg=C['card_bg'],
                fg=C['text_muted'],
                font=F['small'],
                wraplength=360,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=(3, 0))
        body = tk.Frame(content, bg=C['card_bg'])
        body.pack(fill=tk.X)
        for index in range(2):
            body.grid_columnconfigure(index, weight=1, uniform='profile_fields')
        return body

    def _profile_chip(self, parent, text, index=0):
        chip = tk.Label(
            parent,
            text=text,
            bg=C['secondary'],
            fg=C['text_dark'],
            font=F['small_medium'],
            padx=12,
            pady=7,
            cursor='hand2',
            bd=0,
            highlightthickness=1,
            highlightbackground=C['card_border'],
        )
        chip.bind('<Button-1>', lambda _event, value=text: self._toggle_profile_trait(value))
        chip.bind('<Enter>', lambda _event, value=text: self._hover_profile_chip(value, True))
        chip.bind('<Leave>', lambda _event, value=text: self._hover_profile_chip(value, False))
        chip.grid(row=index // 4, column=index % 4, sticky='w', padx=(0, 12), pady=(0, 10))
        self._profile_trait_chips[text] = chip
        self._draw_profile_chip(text)

    def _hover_profile_chip(self, text, active):
        chip = self._profile_trait_chips.get(text)
        if chip is None or text in self._selected_profile_traits:
            return
        chip.configure(bg=C['surface_hover'] if active else C['secondary'])

    def _toggle_profile_trait(self, text):
        if text in self._selected_profile_traits:
            self._selected_profile_traits.remove(text)
        else:
            self._selected_profile_traits.add(text)
        self._draw_profile_chip(text)
        self._sync_profile_traits()

    def _draw_profile_chip(self, text):
        chip = self._profile_trait_chips.get(text)
        if chip is None:
            return
        selected = text in self._selected_profile_traits
        chip.configure(
            text=f'✓ {text}' if selected else text,
            bg=C['accent'] if selected else C['secondary'],
            fg='#FFFFFF' if selected else C['text_dark'],
            highlightbackground=C['accent_ring'] if selected else C['card_border'],
        )

    def _build_orientation_profile_section(self, parent):
        profile_card, profile_content = make_card(parent, padx=24, pady=22)
        profile_card.pack(fill=tk.X, pady=(0, 18))

        groups = tk.Frame(profile_content, bg=C['card_bg'])
        groups.pack(fill=tk.X)
        groups.grid_columnconfigure(0, weight=1, uniform='orientation_groups')
        groups.grid_columnconfigure(1, weight=1, uniform='orientation_groups')

        group1 = self._profile_group_card(
            groups,
            0,
            0,
            'Sở thích và định hướng',
            'Xác định lĩnh vực quan tâm, mục tiêu và cách học phù hợp.',
            icon='🎯',
        )
        self._profile_field(
            group1,
            'Sở thích chính',
            self.profile_interest_display,
            ['Công nghệ thông tin', 'Kỹ thuật', 'Kinh doanh', 'Marketing', 'Du lịch', 'Thực phẩm', 'Y tế', 'Giáo dục', 'Nghệ thuật', 'Chưa xác định'],
            0,
            0,
        )
        self._profile_field(
            group1,
            'Mục tiêu nghề nghiệp',
            self.profile_career_goal,
            ['Thu nhập cao', 'Dễ xin việc', 'Ổn định lâu dài', 'Làm việc quốc tế', 'Khởi nghiệp', 'Nghiên cứu khoa học', 'Phục vụ cộng đồng'],
            0,
            1,
        )
        self._profile_field(
            group1,
            'Phong cách học tập',
            self.profile_learning_style,
            ['Thực hành nhiều', 'Lý thuyết nghiên cứu', 'Học qua dự án', 'Học theo nhóm', 'Tự học'],
            1,
            0,
        )

        group2 = self._profile_group_card(
            groups,
            0,
            1,
            'Hồ sơ cá nhân',
            'Bổ sung bối cảnh học tập, gia đình và môi trường làm việc.',
            icon='👤',
        )
        self._profile_field(
            group2,
            'Môi trường sống',
            self.profile_geography_display,
            ['Đô thị lớn', 'Đô thị vừa', 'Nông thôn', 'Miền núi', 'Ven biển', 'Khu công nghiệp'],
            0,
            0,
        )
        self._profile_field(
            group2,
            'Điều kiện học tập',
            self.profile_mobility_display,
            ['Chỉ học gần nhà', 'Có thể học trong tỉnh', 'Có thể học tại TP.HCM hoặc Hà Nội', 'Sẵn sàng học xa nhà'],
            0,
            1,
        )
        self._profile_field(
            group2,
            'Nghề nghiệp gia đình',
            self.profile_family_display,
            ['Kinh doanh', 'Giáo viên', 'Công chức', 'Kỹ sư', 'Bác sĩ', 'Nông nghiệp', 'Thủy sản', 'Công nhân', 'Không xác định'],
            1,
            0,
        )
        self._profile_field(
            group2,
            'Môi trường làm việc',
            self.profile_work_environment,
            ['Văn phòng', 'Nhà máy', 'Phòng thí nghiệm', 'Trường học', 'Bệnh viện', 'Làm việc ngoài hiện trường', 'Làm việc từ xa'],
            1,
            1,
        )

        group3 = self._profile_group_card(
            groups,
            1,
            0,
            'Đặc điểm cá nhân',
            'Chọn một hoặc nhiều đặc điểm nổi bật để AI hiểu rõ hơn phong cách học tập và làm việc của bạn.',
            columnspan=2,
            icon='✨',
        )
        chip_wrap = tk.Frame(group3, bg=C['card_bg'])
        chip_wrap.grid(row=0, column=0, columnspan=2, sticky='ew')
        for column in range(4):
            chip_wrap.grid_columnconfigure(column, weight=1)
        for index, trait in enumerate((
            'Tư duy logic tốt',
            'Thích sáng tạo',
            'Giao tiếp tốt',
            'Cẩn thận tỉ mỉ',
            'Thích nghiên cứu',
            'Thích làm việc nhóm',
            'Có tố chất lãnh đạo',
            'Thích hoạt động ngoài trời',
        )):
            self._profile_chip(chip_wrap, trait, index)

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
        intro.grid(row=0, column=0, columnspan=3, sticky='nsew', pady=(0, 22))
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
            wraplength=980,
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
        row.pack(fill=tk.X, pady=(6, 18))
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
                    f"• {item.get('ten_nganh', 'Ngành phù hợp')}: phù hợp với hồ sơ"
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
                badge.configure(text='Phù hợp')
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
        self.ov_kv = tk.StringVar(value='KV3')
        self.ov_dt = tk.StringVar(value='Không ưu tiên')

        method_grid = tk.Frame(content, bg=C['content_bg'])
        method_grid.pack(fill=tk.X, pady=(0, 8))
        for column in range(2):
            method_grid.grid_columnconfigure(column, weight=1, uniform='overview_methods')
        try:
            scaling = self.winfo_fpixels('1i') / 96.0
            row_minsize = int(268 * scaling)
        except Exception:
            row_minsize = 268
        for row in range(2):
            method_grid.grid_rowconfigure(row, weight=1, uniform='overview_method_rows', minsize=row_minsize)

        card, panel = make_card(method_grid, padx=22, pady=18)
        card.grid(row=1, column=1, sticky='nsew', padx=(12, 0), pady=(0, 24))
        card.set_fixed_height(268)
        self._method_card_header(
            panel,
            '🧠',
            'Đánh giá năng lực ĐHQG-HCM',
            'Nhập tổng điểm ĐGNL theo thang 600-1200.',
            'accent',
        )
        dgnl_row = tk.Frame(panel, bg=C['card_bg'])
        dgnl_row.pack(fill=tk.X, pady=(10, 0))
        dgnl_row.grid_columnconfigure(0, weight=0)
        dgnl_row.grid_columnconfigure(1, weight=1)
        tk.Label(
            dgnl_row,
            text='Tổng điểm ĐGNL',
            bg=C['card_bg'],
            fg=C['text_dark'],
            font=F['label_b'],
        ).grid(row=0, column=0, sticky='w', padx=(0, 18))
        styled_entry(dgnl_row, self.ov_dgnl, 16).grid(row=0, column=1, sticky='w')

        card, panel = make_card(method_grid, padx=22, pady=18)
        card.grid(row=0, column=0, sticky='nsew', padx=(0, 12), pady=(0, 24))
        card.set_fixed_height(268)
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
        card.set_fixed_height(268)
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
        card.set_fixed_height(268)
        self._method_card_header(
            panel,
            '🎯',
            'Tuyển thẳng',
            'Nhập điểm trung bình lớp 10, 11, 12 và điểm tiếng Anh nếu có.',
            'ai_accent',
        )
        self._build_direct_score_card(panel)

        priority_card, panel = make_card(content, padx=22, pady=18)
        priority_card.pack(fill=tk.X, pady=(0, 24))
        priority_card.set_fixed_height(252)
        self._method_card_header(
            panel,
            '⚙',
            'Ưu tiên xét tuyển',
            'Thiết lập khu vực và đối tượng ưu tiên dùng chung cho các phương thức.',
            'warning',
        )
        prefs = tk.Frame(panel, bg=C['card_bg'])
        prefs.pack(fill=tk.X, pady=(8, 28))
        for column in range(2):
            prefs.grid_columnconfigure(column, weight=1)
        tk.Label(prefs, text='Khu vực', bg=C['card_bg'], fg=C['text_dark'], font=F['label_b']).grid(row=0, column=0, sticky='w', pady=(0, 6))
        styled_combo(prefs, self.ov_kv, ['KV1', 'KV2-NT', 'KV2', 'KV3'], width=22).grid(row=1, column=0, sticky='ew', padx=(0, 22), pady=(0, 18))
        tk.Label(prefs, text='Đối tượng', bg=C['card_bg'], fg=C['text_dark'], font=F['label_b']).grid(row=0, column=1, sticky='w', pady=(0, 6))
        styled_combo(
            prefs,
            self.ov_dt,
            ['Nhóm 1 (01-04)', 'Nhóm 2 (05-07)', 'Không ưu tiên'],
            width=22,
        ).grid(row=1, column=1, sticky='ew', padx=(22, 0), pady=(0, 18))

        self._build_orientation_profile_section(content)

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
        IconButton(
            action_row,
            'Xuất báo cáo HTML',
            self._export_career_report,
            bg=C['secondary'],
            fg=C['text_dark'],
            hover=C['secondary_hover'],
            width=160,
        ).pack(side=tk.LEFT, padx=(10, 0))

        self._build_overview_metrics(content)

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

    def _export_career_report(self):
        scores = self._overview_input(show_errors=True)
        if not scores:
            return
        
        if not self._overview_major_results:
            self._run_overview()
            if not self._overview_major_results:
                messagebox.showwarning(
                    'Không có kết quả',
                    'Không tìm thấy kết quả ngành học phù hợp để xuất báo cáo.',
                )
                return
        
        methods = rank_admission_methods(scores)
        
        import html
        student_name = html.escape(getattr(self, 'student_name', '').strip() or 'Thí sinh hướng nghiệp')
        kv = html.escape(self.ov_kv.get())
        dt = html.escape(self.ov_dt.get())
        sot_thich = html.escape(self.profile_interest.get())
        dac_diem = html.escape(self.profile_personality.get())
        vung_mien = html.escape(self.profile_geography.get())
        
        diem_details_html = ""
        if scores['dgnl'] is not None:
            diem_details_html += f"<li><strong>Điểm ĐGNL ĐHQG:</strong> {scores['dgnl']:.1f} điểm</li>"
        if scores['hoc_ba']:
            hb_tohop = self.ov_hb_tohop.get()
            diem_details_html += f"<li><strong>Điểm Học bạ ({hb_tohop}):</strong> {sum(scores['hoc_ba']):.2f} điểm (môn lẻ: {', '.join(str(x) for x in scores['hoc_ba'])})</li>"
        if scores['thpt']:
            thpt_tohop = self.ov_thpt_tohop.get()
            diem_details_html += f"<li><strong>Điểm thi THPT ({thpt_tohop}):</strong> {sum(scores['thpt']):.2f} điểm (môn lẻ: {', '.join(str(x) for x in scores['thpt'])})</li>"
        if scores['tuyen_thang']:
            diem_details_html += f"<li><strong>Điểm TB 3 năm (Tuyển thẳng):</strong> {sum(scores['tuyen_thang'])/3.0:.2f}/10 (môn lẻ: {', '.join(str(x) for x in scores['tuyen_thang'])})"
            eng_val = self.ov_english.get().strip()
            if eng_val:
                diem_details_html += f" - Tiếng Anh: {eng_val}"
            diem_details_html += "</li>"

        methods_tbody = ""
        for idx, m in enumerate(methods, 1):
            badge_class = "badge-recommended" if m['recommended'] else ("badge-high" if m['level'] == 'Cao' else ("badge-medium" if m['level'] == 'Trung bình' else "badge-low"))
            rec_text = "Khuyên dùng" if m['recommended'] else "Tham khảo"
            methods_tbody += f"""
            <tr>
                <td>{idx}</td>
                <td><strong>{m['method']}</strong></td>
                <td>{m['score']}%</td>
                <td><span class="badge {badge_class}">{m['level']}</span></td>
                <td>{rec_text}</td>
            </tr>
            """
            
        majors_tbody = ""
        for idx, r in enumerate(self._overview_major_results, 1):
            ly_do_list = r.get('ly_do_ho_tro', [])
            ly_do_str = ", ".join(ly_do_list) if ly_do_list else "Độ phù hợp học tập cao"
            majors_tbody += f"""
            <tr>
                <td>{idx}</td>
                <td><code>{r.get('ma_nganh')}</code></td>
                <td><strong>{r.get('ten_nganh')}</strong></td>
                <td><span class="badge badge-high">{r.get('xac_suat')}%</span></td>
                <td>{ly_do_str}</td>
            </tr>
            """
            
        best_method = methods[0]['method'] if methods else 'Học bạ'
        best_level = methods[0]['level'] if methods else 'Chưa rõ'
        advice_text = f"Dựa trên phân tích hồ sơ, bạn có độ sẵn sàng đạt <strong>{methods[0]['score']}% ({best_level})</strong> cho phương thức <strong>{best_method}</strong>. Chúng tôi khuyên bạn nên tập trung nộp hồ sơ xét tuyển bằng phương thức này để tối ưu hóa cơ hội trúng tuyển vào HUIT."

        html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Báo cáo Kết quả Hướng nghiệp HUIT - {student_name}</title>
    <style>
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            color: #333333;
            background-color: #f4f6f8;
            margin: 0;
            padding: 40px 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 850px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.05);
            padding: 40px;
            border-top: 8px solid #9E1B22;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #eaeaea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header-left h1 {{
            color: #9E1B22;
            margin: 0;
            font-size: 26px;
            font-weight: 700;
        }}
        .header-left p {{
            color: #666666;
            margin: 5px 0 0 0;
            font-size: 14px;
        }}
        .btn-print {{
            background-color: #9E1B22;
            color: #ffffff;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: background-color 0.2s;
        }}
        .btn-print:hover {{
            background-color: #82151B;
        }}
        .section-title {{
            color: #2c3e50;
            font-size: 18px;
            font-weight: 600;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #D4AF37;
            padding-left: 10px;
        }}
        .grid-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            background: #fdfdfd;
            border: 1px solid #eaeaea;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .info-item {{
            font-size: 15px;
        }}
        .info-item strong {{
            color: #555555;
        }}
        .scores-list {{
            margin: 5px 0 0 0;
            padding-left: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        th, td {{
            text-align: left;
            padding: 12px 15px;
            border-bottom: 1px solid #eaeaea;
        }}
        th {{
            background-color: #f8f9fa;
            color: #333333;
            font-weight: 600;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-recommended {{
            background-color: #e3fcf7;
            color: #0aa883;
        }}
        .badge-high {{
            background-color: #e8f4fd;
            color: #1a73e8;
        }}
        .badge-medium {{
            background-color: #fff8e1;
            color: #f57c00;
        }}
        .badge-low {{
            background-color: #fce8e6;
            color: #d93025;
        }}
        .advice-box {{
            background-color: #fff9f0;
            border: 1px solid #ffe8cc;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            margin-bottom: 30px;
        }}
        .advice-box h4 {{
            margin: 0 0 10px 0;
            color: #d97706;
            font-size: 16px;
        }}
        code {{
            font-family: Consolas, monospace;
            background-color: #f1f3f5;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            color: #888888;
            font-size: 12px;
            margin-top: 50px;
            border-top: 1px solid #eaeaea;
            padding-top: 20px;
        }}
        @media print {{
            body {{
                background-color: #ffffff;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 0;
                border-top: none;
            }}
            .btn-print {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>HỆ THỐNG GỢI Ý NGÀNH HỌC HUIT</h1>
                <p>Báo cáo Phân tích Hồ sơ & Đề xuất Hướng nghiệp Cá nhân</p>
            </div>
            <div>
                <button class="btn-print" onclick="window.print()">In báo cáo</button>
            </div>
        </div>

        <div class="section-title">Thông tin hồ sơ thí sinh</div>
        <div class="grid-info">
            <div class="info-item">
                <p><strong>Họ và tên:</strong> {student_name}</p>
                <p><strong>Ngày lập báo cáo:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
                <p><strong>Khu vực tuyển sinh:</strong> {kv}</p>
                <p><strong>Đối tượng ưu tiên:</strong> {dt}</p>
            </div>
            <div class="info-item">
                <p><strong>Nhóm ngành quan tâm:</strong> {sot_thich}</p>
                <p><strong>Đặc điểm cá nhân:</strong> {dac_diem}</p>
                <p><strong>Địa lý / Vùng miền:</strong> {vung_mien}</p>
                <p><strong>Điểm số ghi nhận:</strong></p>
                <ul class="scores-list">
                    {diem_details_html}
                </ul>
            </div>
        </div>

        <div class="section-title">Đánh giá mức độ sẵn sàng theo phương thức xét tuyển</div>
        <table>
            <thead>
                <tr>
                    <th>STT</th>
                    <th>Phương thức xét tuyển</th>
                    <th>Điểm số độ phù hợp</th>
                    <th>Trạng thái sẵn sàng</th>
                    <th>Đề xuất</th>
                </tr>
            </thead>
            <tbody>
                {methods_tbody}
            </tbody>
        </table>

        <div class="section-title">Top 12 ngành đào tạo HUIT phù hợp nhất</div>
        <table>
            <thead>
                <tr>
                    <th>STT</th>
                    <th>Mã ngành</th>
                    <th>Tên ngành đào tạo</th>
                    <th>Độ phù hợp</th>
                    <th>Lý do & Gợi ý</th>
                </tr>
            </thead>
            <tbody>
                {majors_tbody}
            </tbody>
        </table>

        <div class="advice-box">
            <h4>💡 Lời khuyên hướng nghiệp tuyển sinh HUIT</h4>
            <p>{advice_text}</p>
            <p>Để biết thêm thông tin chi tiết về đề án tuyển sinh, học phí và cách nộp hồ sơ trực tuyến, vui lòng truy cập trang thông tin tuyển sinh chính thức HUIT tại: <a href="https://ts.huit.edu.vn" target="_blank">ts.huit.edu.vn</a>.</p>
        </div>

        <div class="footer">
            <p>© {datetime.now().year} Trường Đại học Công thương TP.HCM (HUIT) - Hệ thống Hướng nghiệp & Tuyển sinh thông minh</p>
        </div>
    </div>
</body>
</html>
"""
        try:
            desktop_path = Path(os.path.expanduser('~')) / 'Desktop'
            report_file = desktop_path / 'Bao_cao_Huong_nghiep_HUIT.html'
            report_file.write_text(html_content, encoding='utf-8')
            
            messagebox.showinfo(
                'Xuất báo cáo thành công',
                f'Báo cáo hướng nghiệp đã được tạo thành công ngoài Desktop:\n\n{report_file}\n\nĐang tự động mở báo cáo trong trình duyệt của bạn...',
            )
            
            import webbrowser
            webbrowser.open(report_file.as_uri())
        except Exception as e:
            messagebox.showerror(
                'Lỗi xuất báo cáo',
                f'Không thể tạo báo cáo hướng nghiệp: {str(e)}',
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
        notes = []
        if abs(s - 600) < 0.001:
            notes.append('Điểm đang ở ngưỡng sàn 600, nên cân nhắc thêm phương thức xét tuyển khác.')
        if dut > 0:
            notes.append(f'+ {dut} điểm ưu tiên (quy định mới)')
        self._dUTInfo.config(text='  ' + ' | '.join(notes) if notes else '')

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
        if abs(diem - 600) < 0.001:
            self._set_status('ĐGNL ở ngưỡng sàn 600, nên đối chiếu thêm Học bạ hoặc THPT QG')
        else:
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

        label_row(c_in, 'Tổ hợp môn:', 1)
        tk.Label(
            c_in,
            text='Không áp dụng – xét theo ĐTB 3 năm và điều kiện tuyển thẳng',
            font=F['small'],
            bg=C['card_bg'],
            fg=C['text_muted'],
        ).grid(row=1, column=1, columnspan=3, sticky='w', pady=4)

        section_sep(c_in, 2)

        self.tt_l10 = tk.StringVar(); self.tt_l11 = tk.StringVar(); self.tt_l12 = tk.StringVar()
        grade_fields = [
            ('ĐTB Lớp 10 (0–10):', self.tt_l10, 3, 0),
            ('ĐTB Lớp 11 (0–10):', self.tt_l11, 3, 2),
            ('ĐTB Lớp 12 (0–10):', self.tt_l12, 4, 0),
        ]
        for lbl, var, row, col in grade_fields:
            label_row(c_in, lbl, row, col=col)
            styled_entry(c_in, var, 12).grid(
                row=row, column=col + 1, sticky='w', pady=4)
            var.trace_add('write', self._tt_update_sum)

        self._ttSumLbl = label_row(
            c_in, 'Tổng ĐTB 3 năm (thang 30):', 4, col=2)
        self._ttSumVal = tk.Label(c_in, text='0.0', font=('Segoe UI', 11, 'bold'),
                                  bg=C['card_bg'], fg=C['accent'])
        self._ttSumVal.grid(row=4, column=3, sticky='w', pady=4)

        label_row(c_in, 'Điểm Tiếng Anh (0–10, tùy chọn):', 5)
        self.tt_anh = tk.StringVar()
        styled_entry(c_in, self.tt_anh, 12).grid(
            row=5, column=1, sticky='w', pady=4)

        btn_r = tk.Frame(c_in, bg=C['card_bg'])
        btn_r.grid(row=6, column=0, columnspan=4, sticky='w', pady=(12, 0))
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
            year_scores = [
                float(self.tt_l10.get() or 0),
                float(self.tt_l11.get() or 0),
                float(self.tt_l12.get() or 0),
            ]
            if not all(0 <= score <= 10 for score in year_scores):
                messagebox.showwarning(
                    'Giá trị không hợp lệ',
                    'Điểm trung bình từng năm phải nằm trong khoảng 0–10.',
                )
                return
            tb30 = sum(year_scores)
            if tb30 <= 0:
                raise ValueError
        except Exception:
            messagebox.showwarning('Giá trị không hợp lệ', 'Vui lòng nhập điểm trung bình các năm.')
            return
        try:
            diem_anh = float(self.tt_anh.get()) if self.tt_anh.get() else 0.0
        except Exception:
            messagebox.showwarning('Giá trị không hợp lệ', 'Điểm Tiếng Anh phải là số từ 0 đến 10.')
            return
        if not 0 <= diem_anh <= 10:
            messagebox.showwarning('Giá trị không hợp lệ', 'Điểm Tiếng Anh phải nằm trong khoảng 0–10.')
            return
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
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)

        chat_shell = tk.Frame(page, bg=C['card_bg'])
        chat_shell.grid(row=0, column=0, sticky='nsew')
        chat_shell.grid_columnconfigure(0, weight=1)
        chat_shell.grid_rowconfigure(0, weight=1)

        chat_content = tk.Frame(chat_shell, bg=C['card_bg'], padx=22, pady=18)
        chat_content.grid(row=0, column=0, sticky='nsew')
        chat_content.grid_columnconfigure(0, weight=1)
        chat_content.grid_rowconfigure(1, weight=1)

        def _sync_chat_content_width(event):
            chat_content.grid_columnconfigure(0, minsize=max(1, event.width))

        chat_content.bind('<Configure>', _sync_chat_content_width)

        chat_header = tk.Frame(chat_content, bg=C['card_bg'])
        chat_header.grid(row=0, column=0, sticky='ew', pady=(0, 14))
        tk.Label(
            chat_header,
            text='🤖',
            bg=C['accent_soft'],
            fg=C['accent'],
            font=('Segoe UI Emoji', 20),
            width=3,
        ).pack(side=tk.LEFT, padx=(0, 12), ipady=6)
        header_text = tk.Frame(chat_header, bg=C['card_bg'])
        header_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(
            header_text,
            text='Trợ lý AI Hướng nghiệp HUIT',
            bg=C['card_bg'],
            fg=C['ai_accent'],
            font=F['hero_title'],
        ).pack(anchor=tk.W)
        tk.Label(
            header_text,
            text='Trao đổi trực tiếp để phân tích hồ sơ, so sánh phương thức và gợi ý ngành học phù hợp.',
            bg=C['card_bg'],
            fg=C['text_muted'],
            font=F['small'],
        ).pack(anchor=tk.W, pady=(2, 0))
        log_frame = tk.Frame(chat_content, bg=C['surface_alt'])
        log_frame.grid(row=1, column=0, sticky='nsew', pady=(0, 14))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        self.chat_log = tk.Text(
            log_frame,
            wrap=tk.WORD,
            height=12,
            font=F['result'],
            bg=C['surface_alt'],
            fg=C['text_dark'],
            bd=0,
            highlightthickness=0,
            insertbackground=C['accent'],
            selectbackground=C['accent_soft'],
            selectforeground=C['text_dark'],
            padx=24,
            pady=20,
        )
        self.chat_log.grid(row=0, column=0, sticky='nsew')
        chat_scroll = ttk.Scrollbar(log_frame, orient='vertical', command=self.chat_log.yview, style='Modern.Vertical.TScrollbar')
        chat_scroll.grid(row=0, column=1, sticky='ns')
        self.chat_log.configure(yscrollcommand=chat_scroll.set)
        self.chat_log.configure(state='disabled')

        self._style_chat_widgets()

        input_frame = tk.Frame(chat_content, bg=C['surface_alt'], padx=14, pady=12)
        input_frame.grid(row=2, column=0, sticky='ew')
        input_frame.grid_columnconfigure(0, weight=1)

        self.chat_input_var = tk.StringVar()
        self.chat_input_entry = styled_entry(input_frame, self.chat_input_var, width=50)
        self.chat_input_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        self.chat_input_entry.bind('<Return>', lambda _event: self._send_chat_message())

        IconButton(input_frame, 'Gửi', self._send_chat_message, width=96).grid(row=0, column=1)
        IconButton(input_frame, 'Làm mới', self._reset_chat, bg=C['secondary'], fg=C['text_dark'], hover=C['secondary_hover'], width=112).grid(row=0, column=2, padx=(10, 0))
        self.chat_busy_var = tk.StringVar(value='')
        tk.Label(
            input_frame,
            textvariable=self.chat_busy_var,
            bg=C['surface_alt'],
            fg=C['ai_accent'],
            font=F['small_medium'],
        ).grid(row=1, column=0, columnspan=3, sticky='w', pady=(8, 0))

        quick_frame = tk.Frame(input_frame, bg=C['surface_alt'])
        quick_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(12, 0))



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
                bg=C['secondary'],
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
                b.configure(bg=C['secondary'])
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
        self._process_chat_with_loading(text)

    def _send_quick_prompt(self, text):
        self._process_chat_with_loading(text)

    def _process_chat_with_loading(self, text):
        is_free_qa = (hasattr(self, 'chat_state') and self.chat_state == 'state_qa')
        if hasattr(self, 'chat_busy_var'):
            if is_free_qa:
                self.chat_busy_var.set('AI đang suy nghĩ...')
                self._set_status('Trợ lý AI đang xử lý...')
            else:
                self.chat_busy_var.set('AI đang phân tích câu trả lời...')
                self._set_status('Trợ lý AI đang xử lý...')
            self.update_idletasks()
        try:
            self._process_message(text)
        finally:
            if not is_free_qa and hasattr(self, 'chat_busy_var'):
                self.chat_busy_var.set('')
                self._set_status('Trợ lý AI sẵn sàng')

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
            reasons = ", ".join(r.get('ly_do_ho_tro', []))
            reasons_str = f" ({reasons})" if reasons else ""
            card_text += f"   {idx}. {r.get('ten_nganh')} - Mã ngành: {r.get('ma_nganh')}\n"
            card_text += f"      Đánh giá: phù hợp với hồ sơ{reasons_str}\n"

        card_text += f"──────────────────────────────────────────────────\n"
        card_text += f"💡 Lời khuyên: Bạn có độ phù hợp cao tại nhóm ngành {interest}. Hãy đăng ký xét tuyển sớm bằng phương thức {best_method} để tăng tối đa cơ hội trúng tuyển HUIT!"

        self._append_to_chat_log("Hệ thống Hướng nghiệp", card_text, is_ai=True, is_card=True)

        followup = (
            f"Báo cáo hướng nghiệp đã sẵn sàng! Bây giờ, {self.student_name} có thể hỏi tôi bất kỳ câu hỏi nào "
            f"về các ngành học đề xuất, học phí, chương trình đào tạo hoặc ký túc xá tại HUIT..."
        )
        self._append_to_chat_log("Trợ lý AI", followup, is_ai=True)
    def _process_free_qa(self, text):
        api_key = self.gemini_api_key.get().strip()
        if not api_key:
            self._process_fallback_qa(text)
            if hasattr(self, 'chat_busy_var'):
                self.chat_busy_var.set('')
                self._set_status('Trợ lý AI sẵn sàng')
            return

        if not getattr(self, 'gemini_consent_given', False):
            agree = messagebox.askyesno(
                "Đồng ý điều khoản quyền riêng tư",
                "Để cung cấp câu trả lời cá nhân hóa thông minh, thông tin điểm số, sở thích và nội dung trò chuyện của bạn sẽ được gửi tới dịch vụ trí tuệ nhân tạo Google Gemini.\n\nBạn có đồng ý chia sẻ thông tin này không?",
                icon='info'
            )
            if agree:
                self.gemini_consent_given = True
                self._save_setting('gemini_consent_given', True)
            else:
                self._process_fallback_qa(text)
                if hasattr(self, 'chat_busy_var'):
                    self.chat_busy_var.set('')
                    self._set_status('Trợ lý AI sẵn sàng')
                return

        threading.Thread(target=self._query_gemini_api_call, args=(text, api_key), daemon=True).start()

    def _query_gemini_api_call(self, text, api_key):
        import urllib.request
        import urllib.error
        import json

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        
        system_context = (
            "Bạn là Trợ lý Hướng nghiệp AI chính thức của Trường Đại học Công thương TP.HCM (HUIT).\n"
            "Hãy tư vấn một cách thân thiện, chính xác, khách quan, và thuyết phục.\n\n"
            f"Thông tin học sinh hiện tại:\n"
            f"- Họ tên: {self.student_name}\n"
            f"- Phương thức dự kiến xét tuyển: {self.student_scores.get('method', 'Chưa rõ')}\n"
            f"- Điểm số dự kiến: {self.student_scores.get('score', 'Chưa rõ')}\n"
            f"- Nhóm ngành quan tâm: {self.student_interest}\n\n"
            "Thông tin về HUIT cần biết:\n"
            "- Học phí: Trung bình khoảng 30 - 40 triệu đồng/năm tùy theo ngành và số tín chỉ đăng ký (khoảng 1.2M - 1.5M/tín chỉ).\n"
            "- Trường có 9 nhóm ngành đào tạo chính: Công nghệ - Chế biến - Thực phẩm, Kỹ thuật - Cơ khí - Tự động hóa, Hóa học - Sinh học - Môi trường - Vật liệu, Công nghệ thông tin - Trí tuệ nhân tạo - Dữ liệu, Kinh doanh - Quản trị - Marketing, Kế toán - Tài chính - Ngân hàng, Logistics - Quản lý chuỗi cung ứng - Kinh doanh chuyên biệt, Luật - Xã hội - Ngôn ngữ, Du lịch - Nhà hàng - Khách sạn - Dịch vụ.\n"
            "- Ký túc xá khang trang tại TP.HCM, đầy đủ tiện nghi, an ninh tốt.\n"
            "- Địa chỉ: 140 Lê Trọng Tấn, P. Tây Thạnh, Q. Tân Phú, TP.HCM.\n"
            "- Website tuyển sinh: https://ts.huit.edu.vn\n\n"
            "Hãy trả lời câu hỏi sau bằng tiếng Việt, ngắn gọn (khoảng 2-4 câu hoặc liệt kê ngắn gọn), trực tiếp giải đáp thắc mắc của học sinh."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_context}\n\nHọc sinh hỏi: {text}"}
                    ]
                }
            ],
            "tools": [
                {"google_search": {}}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800
            }
        }

        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=headers, 
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_data = json.loads(response.read().decode('utf-8'))
                ans = resp_data['candidates'][0]['content']['parts'][0]['text']
            
            self.after(0, lambda: self._handle_gemini_success(ans))
        except urllib.error.HTTPError:
            self.after(0, lambda: self._handle_gemini_error(text, is_offline=False))
        except urllib.error.URLError:
            self.after(0, lambda: self._handle_gemini_error(text, is_offline=True))
        except Exception:
            self.after(0, lambda: self._handle_gemini_error(text, is_offline=False))

    def _handle_gemini_success(self, ans):
        self._offline_warning_shown = False
        self._append_to_chat_log("Trợ lý AI", ans.strip(), is_ai=True)
        if hasattr(self, 'chat_busy_var'):
            self.chat_busy_var.set('')
            self._set_status('Trợ lý AI sẵn sàng')

    def _handle_gemini_error(self, text, is_offline=False):
        if is_offline:
            fallback_msg = "(Thiết bị của bạn hiện không có kết nối Internet. Trợ lý AI HUIT tạm thời chuyển sang chế độ tư vấn ngoại tuyến/offline)"
            if not getattr(self, '_offline_warning_shown', False):
                self._offline_warning_shown = True
                messagebox.showwarning(
                    "Lỗi kết nối mạng",
                    "Thiết bị của bạn hiện không có kết nối Internet.\nHệ thống sẽ chuyển sang chế độ tư vấn offline."
                )
        else:
            fallback_msg = "(Không kết nối được Gemini AI. Tôi xin phép trả lời bằng bộ câu hỏi offline của HUIT)"
            
        self._append_to_chat_log("Trợ lý AI", fallback_msg, is_ai=True)
        self._process_fallback_qa(text)
        if hasattr(self, 'chat_busy_var'):
            self.chat_busy_var.set('')
            self._set_status('Trợ lý AI sẵn sàng')

    def _process_fallback_qa(self, text):
        cleaned = text.lower()
        if "học phí" in cleaned or "hoc phi" in cleaned or "tiền học" in cleaned:
            ans = (
                "Học phí tại HUIT dao động khoảng 30 - 40 triệu đồng/năm học, tính theo số tín chỉ đăng ký thực tế "
                "(trung bình khoảng 1.2M - 1.5M/tín chỉ). Học phí được giữ ổn định và công bố minh bạch đầu khóa học."
            )
        elif "tuyển thẳng" in cleaned or "tuyen thang" in cleaned or "xét tuyển thẳng" in cleaned:
            ans = (
                "Điều kiện xét tuyển thẳng HUIT bao gồm: Học sinh giỏi THPT các năm, hoặc đạt giải học sinh giỏi quốc gia, "
                "khoa học kỹ thuật cấp quốc gia, hoặc sở hữu chứng chỉ quốc tế (IELTS từ 5.5, TOEFL, v.v.) kết hợp học bạ khá trở lên."
            )
        elif "ký túc xá" in cleaned or "ky tuc xa" in cleaned or "chỗ ở" in cleaned or "phòng trọ" in cleaned:
            ans = (
                "Trường HUIT có khu Ký túc xá hiện đại nằm gần cơ sở học tập chính, đáp ứng đầy đủ tiện nghi, internet tốc độ cao, "
                "an ninh 24/7 với chi phí rất ưu đãi dành riêng cho sinh viên của trường."
            )
        elif "ngành" in cleaned or "nganh" in cleaned or "học gì" in cleaned:
            ans = (
                "HUIT đào tạo 9 nhóm ngành lớn bao gồm: Công nghệ Thực phẩm, Kỹ thuật - Cơ khí - Tự động hóa, CNTT - Trí tuệ nhân tạo, "
                "Hóa học - Sinh học - Môi trường, Kinh doanh - Marketing, Kế toán - Tài chính, Logistics, Luật - Ngôn ngữ và Du lịch. "
                "Bạn có thể xem chi tiết ở mục tuyển sinh trên trang chủ HUIT."
            )
        elif "địa chỉ" in cleaned or "ở đâu" in cleaned or "dia chi" in cleaned:
            ans = (
                "Cơ sở chính của Trường Đại học Công thương TP.HCM nằm tại số 140 Lê Trọng Tấn, Phường Tây Thạnh, Quận Tân Phú, TP.HCM. "
                "Trường nằm ở khu vực giao thông thuận lợi, sầm uất và nhiều tiện ích."
            )
        elif "website" in cleaned or "trang chủ" in cleaned or "web" in cleaned:
            ans = (
                "Bạn có thể truy cập trang chủ của trường tại: https://huit.edu.vn hoặc trang thông tin tuyển sinh chính thức: https://ts.huit.edu.vn"
            )
        else:
            ans = (
                f"Cảm ơn {self.student_name} đã đặt câu hỏi. HUIT đào tạo đa ngành với các lĩnh vực nổi bật như Công nghệ thực phẩm, CNTT, Kinh doanh. "
                "Nếu bạn cần thêm thông tin chi tiết về học phí, ký túc xá hay điểm chuẩn các năm, hãy nhắn cụ thể hơn nhé!"
            )
        self._append_to_chat_log("Trợ lý AI", ans, is_ai=True)

    def _build_page_settings(self):
        page = tk.Frame(self._content_host, bg=C['content_bg'])
        self._pages['Cài đặt'] = page
        page.grid_columnconfigure(0, weight=1)
        
        title_frame = tk.Frame(page, bg=C['content_bg'])
        title_frame.pack(fill=tk.X, pady=(0, 18))
        tk.Label(
            title_frame,
            text='Cài đặt hệ thống',
            font=F['page_title'],
            bg=C['content_bg'],
            fg=C['text_header'],
        ).pack(anchor=tk.W)
        tk.Label(
            title_frame,
            text='Cấu hình khóa API Key, tùy chỉnh giao diện và quản lý quyền riêng tư dữ liệu cá nhân.',
            font=F['small'],
            bg=C['content_bg'],
            fg=C['text_muted'],
        ).pack(anchor=tk.W, pady=(4, 0))

        ai_card, ai_content = make_card(page, 'Cấu hình Trợ lý AI (Google Gemini)')
        ai_card.pack(fill=tk.X, pady=(0, 14))
        
        tk.Label(
            ai_content,
            text='Nhập Gemini API Key để kích hoạt tính năng chat tự do tư vấn hướng nghiệp:',
            font=F['label'],
            bg=C['card_bg'],
            fg=C['text_dark'],
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
        
        self.settings_api_show = tk.BooleanVar(value=False)
        self.settings_api_entry = styled_entry(
            ai_content,
            self.gemini_api_key,
            show='*',
            width=50
        )
        self.settings_api_entry.grid(row=1, column=0, sticky='w', pady=(0, 10))
        
        def toggle_settings_api_visibility():
            if self.settings_api_show.get():
                self.settings_api_entry.configure(show='*')
                self.settings_api_show.set(False)
                self.settings_api_btn.configure(text='Hiện khóa')
            else:
                self.settings_api_entry.configure(show='')
                self.settings_api_show.set(True)
                self.settings_api_btn.configure(text='Ẩn khóa')
                
        def delete_api_key():
            self.gemini_api_key.set('')
            messagebox.showinfo('Đã xóa', 'Đã xóa API Key khỏi cấu hình.')

        self.settings_api_btn = IconButton(
            ai_content,
            'Hiện khóa',
            toggle_settings_api_visibility,
            bg=C['secondary'],
            fg=C['text_dark'],
            hover=C['secondary_hover'],
            width=100
        )
        self.settings_api_btn.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=(0, 10))
        
        IconButton(
            ai_content,
            'Xóa khóa API',
            delete_api_key,
            bg=C['secondary'],
            fg=C['text_dark'],
            hover=C['secondary_hover'],
            width=120
        ).grid(row=1, column=2, sticky='w', padx=(10, 0), pady=(0, 10))

        tk.Label(
            ai_content,
            text='Quyền riêng tư & Chia sẻ dữ liệu:',
            font=F['label_b'],
            bg=C['card_bg'],
            fg=C['text_dark'],
        ).grid(row=2, column=0, columnspan=3, sticky='w', pady=(10, 4))
        
        self.settings_consent_var = tk.StringVar(
            value='Đã đồng ý chia sẻ dữ liệu' if getattr(self, 'gemini_consent_given', False) else 'Chưa đồng ý (Sử dụng AI offline)'
        )
        
        self.settings_consent_lbl = tk.Label(
            ai_content,
            textvariable=self.settings_consent_var,
            font=F['label'],
            bg=C['card_bg'],
            fg=C['accent'],
        )
        self.settings_consent_lbl.grid(row=3, column=0, sticky='w')
        
        def reset_consent():
            self.gemini_consent_given = False
            self._save_setting('gemini_consent_given', False)
            self.settings_consent_var.set('Chưa đồng ý (Sử dụng AI offline)')
            messagebox.showinfo('Quyền riêng tư', 'Đã đặt lại quyền riêng tư. Hộp thoại hỏi ý kiến sẽ hiển thị lại trong lần trò chuyện tiếp theo.')

        IconButton(
            ai_content,
            'Đặt lại quyền riêng tư',
            reset_consent,
            bg=C['secondary'],
            fg=C['text_dark'],
            hover=C['secondary_hover'],
            width=180
        ).grid(row=3, column=1, columnspan=2, sticky='w', padx=(10, 0))

        ui_card, ui_content = make_card(page, 'Tùy chỉnh giao diện & Hiển thị')
        ui_card.pack(fill=tk.X, pady=(0, 14))
        
        tk.Label(
            ui_content,
            text='Chế độ màu hiển thị (Giao diện):',
            font=F['label'],
            bg=C['card_bg'],
            fg=C['text_dark'],
        ).grid(row=0, column=0, sticky='w', pady=(0, 10))
        
        def toggle_theme_settings():
            self._toggle_theme()
            theme_btn.configure(text='Chuyển sang Giao diện Sáng' if self._theme_name == 'dark' else 'Chuyển sang Giao diện Tối')

        theme_btn = IconButton(
            ui_content,
            'Chuyển sang Giao diện Tối' if self._theme_name == 'light' else 'Chuyển sang Giao diện Sáng',
            toggle_theme_settings,
            bg=C['secondary'],
            fg=C['text_dark'],
            hover=C['secondary_hover'],
            width=240
        )
        theme_btn.grid(row=0, column=1, sticky='w', padx=(20, 0), pady=(0, 10))

        info_card, info_content = make_card(page, 'Thông tin sản phẩm')
        info_card.pack(fill=tk.X)
        
        tk.Label(
            info_content,
            text='Phiên bản ứng dụng: v2.0-stable\nPhiên bản mô hình: HUIT-ML-2026.06\nBản quyền thuộc về Trường Đại học Công thương TP.HCM (HUIT)',
            font=F['small'],
            bg=C['card_bg'],
            fg=C['text_muted'],
            justify=tk.LEFT
        ).pack(anchor=tk.W)


if __name__ == '__main__':
    app = App()
    app.mainloop()
