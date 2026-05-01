#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HUIT – Hệ thống Gợi ý Ngành học
Modern Desktop GUI v2.0  (Tkinter)
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# ── Unicode fix trên Windows ───────────────────────────────────────────────
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── Import các mô-đun inference ───────────────────────────────────────────
try:
    from scripts.Goi_y_nganh_nghe import goi_y_nganh_simple as dgnl_predict
except Exception:
    dgnl_predict = None

try:
    from scripts.Goi_y_nganh_thpt import goi_y_nganh_thpt, allowed_tohops_for_group
except Exception:
    goi_y_nganh_thpt = None
    allowed_tohops_for_group = lambda g: set()

try:
    from scripts.Goi_y_nganh_tuyen_thang import goi_y_nganh_tuyen_thang_simple as tt_predict
except Exception:
    tt_predict = None

try:
    from scripts.hoc_ba_analyzer import HocBaAnalyzer, TO_HOP_MON
except Exception:
    HocBaAnalyzer = None
    TO_HOP_MON = {}

# ══════════════════════════════════════════════════════════════════════════
#  THEME CONSTANTS
# ══════════════════════════════════════════════════════════════════════════
C = {
    # Header / Sidebar
    'header_bg':      '#1a3a6b',
    'sidebar_bg':     '#1b2d4e',
    'sidebar_hover':  '#243d6a',
    'sidebar_active': '#2e5eaa',
    # Content area
    'content_bg':     '#f0f4f8',
    'card_bg':        '#ffffff',
    'card_border':    '#d1dce8',
    # Text
    'text_dark':      '#1e293b',
    'text_muted':     '#64748b',
    'text_light':     '#f1f5f9',
    'text_header':    '#ffffff',
    # Accent
    'accent':         '#2563eb',
    'accent_dark':    '#1d4ed8',
    'accent_hover':   '#1e40af',
    # Semantic colours
    'success':        '#16a34a',
    'success_light':  '#dcfce7',
    'warning':        '#ca8a04',
    'warning_light':  '#fef9c3',
    'danger':         '#dc2626',
    # Treeview rows
    'row_even':       '#f8faff',
    'row_odd':        '#ffffff',
    'row_top':        '#d1fae5',   # rank 1-3  – green
    'row_mid':        '#fef3c7',   # rank 4-6  – yellow
    # Inputs
    'input_bg':       '#f8fafc',
    'input_focus':    '#eff6ff',
    # Separator
    'sep':            '#cbd5e1',
    # Status bar
    'status_bg':      '#1a3a6b',
}

F = {
    'app_title':  ('Segoe UI', 18, 'bold'),
    'app_sub':    ('Segoe UI', 9),
    'nav':        ('Segoe UI', 11, 'bold'),
    'section':    ('Segoe UI', 12, 'bold'),
    'label':      ('Segoe UI', 10),
    'label_b':    ('Segoe UI', 10, 'bold'),
    'entry':      ('Segoe UI', 11),
    'button':     ('Segoe UI', 11, 'bold'),
    'result_h':   ('Segoe UI', 11, 'bold'),
    'result':     ('Segoe UI', 10),
    'status':     ('Segoe UI', 9),
    'small':      ('Segoe UI', 9),
}

GROUP_OPTIONS = [
    'Công nghệ – Chế biến – Thực phẩm',
    'Kỹ thuật – Cơ khí – Tự động hóa',
    'Hóa học – Sinh học – Môi trường – Vật liệu',
    'Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu',
    'Kinh doanh – Quản trị – Marketing',
    'Kế toán – Tài chính – Ngân hàng',
    'Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt',
    'Luật – Xã hội – Ngôn ngữ',
    'Du lịch – Nhà hàng – Khách sạn – Dịch vụ',
]

NAV_ITEMS = [
    ('🎓', 'ĐGNL',         'Đánh giá năng lực'),
    ('📚', 'Học bạ',        'Xét học bạ THPT'),
    ('⭐', 'Tuyển thẳng',  'Xét tuyển thẳng'),
    ('📊', 'THPT QG',       'Điểm thi THPT'),
]


# ══════════════════════════════════════════════════════════════════════════
#  HELPER WIDGETS
# ══════════════════════════════════════════════════════════════════════════

def make_card(parent, title=None, padx=16, pady=12):
    """Trả về (outer_frame, inner_frame). outer có viền nhạt, inner là nền trắng."""
    outer = tk.Frame(parent, bg=C['card_border'], bd=0)
    inner = tk.Frame(outer, bg=C['card_bg'], bd=0, padx=padx, pady=pady)
    inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    if title:
        tk.Label(inner, text=title, font=F['section'],
                 bg=C['card_bg'], fg=C['accent']).pack(anchor=tk.W, pady=(0, 8))
    return outer, inner


def styled_entry(parent, textvariable, width=18, **kw):
    return ttk.Entry(parent, textvariable=textvariable,
                     width=width, font=F['entry'], **kw)


def styled_combo(parent, textvariable, values, width=22, state='readonly'):
    return ttk.Combobox(parent, textvariable=textvariable, values=values,
                        width=width, state=state, font=F['entry'])


def label_row(parent, text, row, col=0, **kw):
    lbl = tk.Label(parent, text=text, font=F['label'],
                   bg=C['card_bg'], fg=C['text_dark'], anchor='w', **kw)
    lbl.grid(row=row, column=col, sticky='w', padx=(0, 10), pady=4)
    return lbl


def section_sep(parent, row, colspan=4):
    f = tk.Frame(parent, bg=C['sep'], height=1)
    f.grid(row=row, column=0, columnspan=colspan, sticky='ew', pady=8)
    return f


# ── Modern button with hover ──────────────────────────────────────────────
class IconButton(tk.Frame):
    def __init__(self, parent, text, command, icon='',
                 bg=None, fg='#ffffff', hover=None, **kw):
        self._bg    = bg    or C['accent']
        self._hover = hover or C['accent_hover']
        self._fg    = fg
        super().__init__(parent, bg=self._bg, cursor='hand2', **kw)
        full = f'{icon}  {text}' if icon else text
        self._lbl = tk.Label(self, text=full, font=F['button'],
                             bg=self._bg, fg=self._fg, padx=18, pady=8)
        self._lbl.pack()
        for w in (self, self._lbl):
            w.bind('<Enter>',    self._on_enter)
            w.bind('<Leave>',    self._on_leave)
            w.bind('<Button-1>', lambda e: command())

    def _on_enter(self, _):
        self.config(bg=self._hover);  self._lbl.config(bg=self._hover)

    def _on_leave(self, _):
        self.config(bg=self._bg);     self._lbl.config(bg=self._bg)


# ── Results Treeview with coloured rows ───────────────────────────────────
class ResultTable(tk.Frame):
    COLS = [
        ('rank',  '#',          42,   tk.CENTER),
        ('ma',    'Mã ngành',   90,   tk.W),
        ('ten',   'Tên ngành',  360,  tk.W),
        ('xs',    'Xác suất',   90,   tk.CENTER),
        ('flags', 'Ghi chú',   180,   tk.W),
    ]

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C['card_bg'], **kw)
        uid = f'T{id(self)}'
        s = ttk.Style()
        s.configure(f'{uid}.Treeview',
                    font=F['result'], rowheight=26,
                    background=C['row_odd'], fieldbackground=C['row_odd'],
                    foreground=C['text_dark'], borderwidth=0)
        s.configure(f'{uid}.Treeview.Heading',
                    font=F['result_h'],
                    background=C['accent'], foreground='#ffffff',
                    relief='flat', padding=4)
        s.map(f'{uid}.Treeview',
              background=[('selected', C['accent'])],
              foreground=[('selected', '#ffffff')])

        cols = [c[0] for c in self.COLS]
        self._tree = ttk.Treeview(self, columns=cols, show='headings',
                                  height=12, style=f'{uid}.Treeview')
        for cid, hd, w, anc in self.COLS:
            self._tree.heading(cid, text=hd)
            self._tree.column(cid, width=w, minwidth=w, anchor=anc)

        self._tree.tag_configure('top',  background=C['row_top'])
        self._tree.tag_configure('mid',  background=C['row_mid'])
        self._tree.tag_configure('even', background=C['row_even'])
        self._tree.tag_configure('odd',  background=C['row_odd'])

        vsb = ttk.Scrollbar(self, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscroll=vsb.set)
        self._tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def populate(self, results):
        self.clear()
        if not results:
            self._tree.insert('', tk.END,
                              values=('—', '—', '  Không có kết quả', '—', ''))
            return
        for idx, item in enumerate(results, 1):
            ma   = item.get('ma_nganh', '')
            ten  = item.get('ten_nganh', '')
            xs   = item.get('xac_suat', 0)
            flag_parts = []
            if item.get('to_hop_phu_hop') is True:
                flag_parts.append('✅ tổ hợp phù hợp')
            if item.get('to_hop_phu_hop') is False:
                flag_parts.append('⚠️ không mở tổ hợp')
            if item.get('thuoc_nhom_mong_muon') is True:
                flag_parts.append('🎯 thuộc nhóm')
            if item.get('thuoc_nhom_mong_muon') is False:
                flag_parts.append('📊 ngoài nhóm')
            if idx <= 3:
                tag = 'top'
            elif idx <= 6:
                tag = 'mid'
            elif idx % 2 == 0:
                tag = 'even'
            else:
                tag = 'odd'
            xs_str = f'{xs}%' if isinstance(xs, (int, float)) else str(xs)
            self._tree.insert('', tk.END,
                              values=(idx, ma, ten, xs_str, ', '.join(flag_parts)),
                              tags=(tag,))

    def clear(self):
        for iid in self._tree.get_children():
            self._tree.delete(iid)


# ══════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('HUIT – Hệ thống Gợi ý Ngành học')
        self.geometry('1100x700')
        self.minsize(900, 600)
        self.configure(bg=C['content_bg'])
        self._apply_global_style()
        self._current_page = tk.StringVar(value='ĐGNL')
        self._status_var   = tk.StringVar(value='Sẵn sàng')
        self._build_layout()
        self.after(150, lambda: self._show_page('ĐGNL'))

    # ── Global ttk style ──────────────────────────────────────────────────
    def _apply_global_style(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('TFrame',    background=C['content_bg'])
        s.configure('TLabel',    background=C['content_bg'],
                                 foreground=C['text_dark'], font=F['label'])
        s.configure('TEntry',    fieldbackground=C['input_bg'],
                                 foreground=C['text_dark'], borderwidth=1, relief='solid')
        s.map('TEntry', fieldbackground=[('focus', C['input_focus'])])
        s.configure('TCombobox', fieldbackground=C['input_bg'],
                                 background=C['input_bg'],
                                 foreground=C['text_dark'], arrowcolor=C['accent'])
        s.configure('TRadiobutton', background=C['card_bg'],
                                    foreground=C['text_dark'], font=F['label'])
        s.configure('TScrollbar', background=C['card_border'],
                                  troughcolor=C['content_bg'],
                                  arrowcolor=C['text_muted'])

    # ── Layout skeleton ───────────────────────────────────────────────────
    def _build_layout(self):
        self._build_header()
        body = tk.Frame(self, bg=C['content_bg'])
        body.pack(fill=tk.BOTH, expand=True)
        self._build_sidebar(body)
        self._content_host = tk.Frame(body, bg=C['content_bg'])
        self._content_host.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                                padx=16, pady=16)
        self._pages = {}
        self._build_page_dgnl()
        self._build_page_hocba()
        self._build_page_tuyenthang()
        self._build_page_pt1()
        self._build_statusbar()

    # ── Header ────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=C['header_bg'], height=72)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text='⬡ HUIT', font=('Segoe UI', 22, 'bold'),
                 bg=C['header_bg'], fg='#60a5fa').pack(side=tk.LEFT, padx=(20, 0), pady=12)
        tk.Frame(hdr, bg='#3b5998', width=2, height=44).pack(
            side=tk.LEFT, pady=14, padx=14)

        info = tk.Frame(hdr, bg=C['header_bg'])
        info.pack(side=tk.LEFT)
        tk.Label(info, text='Hệ thống Gợi ý Ngành học', font=F['app_title'],
                 bg=C['header_bg'], fg='#ffffff').pack(anchor=tk.W, pady=(16, 0))
        tk.Label(info,
                 text='Trường Đại học Công Thương TP.HCM  ·  AI Advisory System',
                 font=F['app_sub'], bg=C['header_bg'], fg='#93c5fd').pack(anchor=tk.W)

        self._clock_var = tk.StringVar()
        tk.Label(hdr, textvariable=self._clock_var,
                 font=('Segoe UI', 10), bg=C['header_bg'], fg='#93c5fd').pack(
            side=tk.RIGHT, padx=24)
        self._tick()

    def _tick(self):
        self._clock_var.set(datetime.now().strftime('%H:%M:%S  |  %d/%m/%Y'))
        self.after(1000, self._tick)

    # ── Sidebar ───────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C['sidebar_bg'], width=195)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)

        tk.Label(sb, text='MENU CHÍNH', font=('Segoe UI', 8, 'bold'),
                 bg=C['sidebar_bg'], fg='#6b8bb5').pack(
            anchor=tk.W, padx=18, pady=(22, 6))

        self._nav_btns = {}
        for icon, title, sub in NAV_ITEMS:
            self._nav_btns[title] = self._make_nav_btn(sb, icon, title, sub)

        tk.Frame(sb, bg='#2a3f65', height=1).pack(fill=tk.X, padx=16, pady=14)
        tk.Label(sb, text='v2.0  ·  2025',
                 font=('Segoe UI', 8), bg=C['sidebar_bg'], fg='#3d5a80').pack(
            anchor=tk.W, padx=18)

    def _make_nav_btn(self, parent, icon, title, subtitle):
        btn_f = tk.Frame(parent, bg=C['sidebar_bg'], cursor='hand2')
        btn_f.pack(fill=tk.X, padx=8, pady=2)

        icon_lbl = tk.Label(btn_f, text=icon, font=('Segoe UI', 18),
                            bg=C['sidebar_bg'], fg='#60a5fa', width=3)
        icon_lbl.pack(side=tk.LEFT, padx=(6, 0), pady=7)

        txt_f = tk.Frame(btn_f, bg=C['sidebar_bg'])
        txt_f.pack(side=tk.LEFT, padx=6, pady=7)

        t_lbl = tk.Label(txt_f, text=title, font=F['nav'],
                         bg=C['sidebar_bg'], fg=C['text_light'], anchor='w')
        t_lbl.pack(anchor=tk.W)

        s_lbl = tk.Label(txt_f, text=subtitle, font=('Segoe UI', 8),
                         bg=C['sidebar_bg'], fg='#6b8bb5', anchor='w')
        s_lbl.pack(anchor=tk.W)

        widgets = [btn_f, icon_lbl, txt_f, t_lbl, s_lbl]

        def _click(_=None):
            self._show_page(title)

        def _enter(_=None):
            if self._current_page.get() != title:
                for w in widgets:
                    w.config(bg=C['sidebar_hover'])

        def _leave(_=None):
            if self._current_page.get() != title:
                for w in widgets:
                    w.config(bg=C['sidebar_bg'])

        for w in widgets:
            w.bind('<Button-1>', _click)
            w.bind('<Enter>',    _enter)
            w.bind('<Leave>',    _leave)

        return {'widgets': widgets, 'title_lbl': t_lbl}

    def _show_page(self, name):
        prev = self._current_page.get()
        # Deactivate previous
        if prev in self._nav_btns:
            b = self._nav_btns[prev]
            for w in b['widgets']:
                w.config(bg=C['sidebar_bg'])
            b['title_lbl'].config(fg=C['text_light'])
        # Activate new
        self._current_page.set(name)
        if name in self._nav_btns:
            b = self._nav_btns[name]
            for w in b['widgets']:
                w.config(bg=C['sidebar_active'])
            b['title_lbl'].config(fg='#ffffff')
        # Swap page frames
        for pname, pframe in self._pages.items():
            if pname == name:
                pframe.pack(fill=tk.BOTH, expand=True)
            else:
                pframe.pack_forget()
        self._set_status(f'Đang sử dụng phương thức: {name}')

    # ── Status bar ────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=C['status_bg'], height=26)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self._status_var,
                 font=F['status'], bg=C['status_bg'], fg='#93c5fd',
                 anchor='w').pack(side=tk.LEFT, padx=12)
        tk.Label(bar, text='HUIT AI Advisory System © 2025',
                 font=F['status'], bg=C['status_bg'], fg='#3d5a80').pack(
            side=tk.RIGHT, padx=12)

    def _set_status(self, msg):
        self._status_var.set(f'  {msg}')

    # ── Page title helper ─────────────────────────────────────────────────
    @staticmethod
    def _page_title(parent, title, sub=''):
        hdr = tk.Frame(parent, bg=C['content_bg'])
        hdr.pack(fill=tk.X, pady=(0, 10))
        tk.Label(hdr, text=title, font=('Segoe UI', 14, 'bold'),
                 bg=C['content_bg'], fg=C['text_dark']).pack(anchor=tk.W)
        if sub:
            tk.Label(hdr, text=sub, font=F['small'],
                     bg=C['content_bg'], fg=C['text_muted']).pack(anchor=tk.W)
        tk.Frame(hdr, bg=C['accent'], height=2).pack(fill=tk.X, pady=(4, 0))

    # ══════════════════════════════════════════════════════════════════════
    #  PAGE – ĐGNL
    # ══════════════════════════════════════════════════════════════════════
    def _build_page_dgnl(self):
        page = tk.Frame(self._content_host, bg=C['content_bg'])
        self._pages['ĐGNL'] = page
        self._page_title(page, '🎓  Xét tuyển theo ĐGNL',
                         'Đánh giá năng lực – ĐH Quốc gia TP.HCM / Hà Nội')

        c_out, c_in = make_card(page, padx=20, pady=14)
        c_out.pack(fill=tk.X, pady=(0, 10))

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
        IconButton(btn_r, 'Gợi ý ngành', self._run_dgnl, icon='🔍').pack(side=tk.LEFT)
        IconButton(btn_r, 'Xóa', self._clear_dgnl, icon='🗑',
                   bg='#64748b', hover='#475569').pack(side=tk.LEFT, padx=(10, 0))

        # Results
        r_out, r_in = make_card(page, 'Kết quả gợi ý', padx=12, pady=12)
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
        self._tbl_dgnl.clear()

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
        results = dgnl_predict(diem, diem_dt=0, diem_kv=dut,
                               thu_tu_nv=1, nguyen_vong=group, top_n=12)
        self._tbl_dgnl.populate(results)
        self._set_status(f'Đã gợi ý {len(results)} ngành phù hợp (ĐGNL)')

    # ══════════════════════════════════════════════════════════════════════
    #  PAGE – HỌC BẠ
    # ══════════════════════════════════════════════════════════════════════
    def _build_page_hocba(self):
        page = tk.Frame(self._content_host, bg=C['content_bg'])
        self._pages['Học bạ'] = page
        self._page_title(page, '📚  Xét tuyển theo Học bạ',
                         'Điểm trung bình 3 môn học bạ THPT')

        c_out, c_in = make_card(page, padx=20, pady=14)
        c_out.pack(fill=tk.X, pady=(0, 10))

        label_row(c_in, 'Nhóm ngành:', 0)
        self.hb_group = tk.StringVar()
        cb = styled_combo(c_in, self.hb_group, GROUP_OPTIONS, width=56)
        cb.grid(row=0, column=1, columnspan=3, sticky='w', pady=4)
        cb.bind('<<ComboboxSelected>>', self._on_hb_group_changed)

        label_row(c_in, 'Tổ hợp môn:', 1)
        self.hb_tohop = tk.StringVar()
        self.hb_cb_tohop = styled_combo(c_in, self.hb_tohop, [], width=16)
        self.hb_cb_tohop.grid(row=1, column=1, sticky='w', pady=4)

        section_sep(c_in, 2)

        fields_hb = [
            ('Điểm TB Môn 1 (0–10):', 'hb_m1', 3),
            ('Điểm TB Môn 2 (0–10):', 'hb_m2', 4),
            ('Điểm TB Môn 3 (0–10):', 'hb_m3', 5),
            ('Điểm ưu tiên KV+ĐT (0–3):', 'hb_ut', 6),
        ]
        for lbl_t, attr, r in fields_hb:
            label_row(c_in, lbl_t, r)
            v = tk.StringVar(value=('0' if attr == 'hb_ut' else ''))
            styled_entry(c_in, v, 10).grid(row=r, column=1, sticky='w', pady=4)
            setattr(self, attr, v)

        btn_r = tk.Frame(c_in, bg=C['card_bg'])
        btn_r.grid(row=7, column=0, columnspan=4, sticky='w', pady=(12, 0))
        IconButton(btn_r, 'Gợi ý ngành', self._run_hocba, icon='🔍').pack(side=tk.LEFT)
        IconButton(btn_r, 'Xóa', self._clear_hocba, icon='🗑',
                   bg='#64748b', hover='#475569').pack(side=tk.LEFT, padx=(10, 0))

        r_out, r_in = make_card(page, 'Kết quả gợi ý', padx=12, pady=12)
        r_out.pack(fill=tk.BOTH, expand=True)
        self._tbl_hb = ResultTable(r_in)
        self._tbl_hb.pack(fill=tk.BOTH, expand=True)

    def _on_hb_group_changed(self, *_):
        vals = sorted(allowed_tohops_for_group(self.hb_group.get())
                      if callable(allowed_tohops_for_group) else set())
        self.hb_cb_tohop['values'] = vals
        if vals:
            self.hb_cb_tohop.set(vals[0])

    def _clear_hocba(self):
        for attr in ('hb_m1', 'hb_m2', 'hb_m3'):
            getattr(self, attr).set('')
        self.hb_ut.set('0')
        self._tbl_hb.clear()

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
            m3 = float(self.hb_m3.get()); ut = float(self.hb_ut.get() or 0)
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
        diem_hb_info = {
            'to_hop':         tohop,
            'mon_hoc':        TO_HOP_MON.get(tohop, []),
            'diem_tb_mon1':   m1,
            'diem_tb_mon2':   m2,
            'diem_tb_mon3':   m3,
            'diem_hb':        round(m1 + m2 + m3 + ut, 2),
            'diem_xet_tuyen': round(m1 + m2 + m3 + ut, 2),
        }
        self._set_status('Đang xử lý Học bạ…')
        results = analyzer.predict_nganh(diem_hb_info, top_k=12, nguyen_vong=group)
        self._tbl_hb.populate(results)
        self._set_status(f'Đã gợi ý {len(results)} ngành phù hợp (Học bạ)')

    # ══════════════════════════════════════════════════════════════════════
    #  PAGE – TUYỂN THẲNG
    # ══════════════════════════════════════════════════════════════════════
    def _build_page_tuyenthang(self):
        page = tk.Frame(self._content_host, bg=C['content_bg'])
        self._pages['Tuyển thẳng'] = page
        self._page_title(page, '⭐  Xét tuyển Thẳng',
                         'Dựa trên điểm trung bình toàn cấp THPT')

        c_out, c_in = make_card(page, padx=20, pady=14)
        c_out.pack(fill=tk.X, pady=(0, 10))

        label_row(c_in, 'Nhóm ngành:', 0)
        self.tt_group = tk.StringVar()
        styled_combo(c_in, self.tt_group, GROUP_OPTIONS, width=56).grid(
            row=0, column=1, columnspan=3, sticky='w', pady=4)

        section_sep(c_in, 1)

        label_row(c_in, 'Tổng ĐTB 3 năm (thang 30):', 2)
        self.tt_tb30 = tk.StringVar()
        styled_entry(c_in, self.tt_tb30, 12).grid(row=2, column=1, sticky='w', pady=4)

        label_row(c_in, 'Điểm Tiếng Anh (0–10, tùy chọn):', 3)
        self.tt_anh = tk.StringVar()
        styled_entry(c_in, self.tt_anh, 12).grid(row=3, column=1, sticky='w', pady=4)

        btn_r = tk.Frame(c_in, bg=C['card_bg'])
        btn_r.grid(row=4, column=0, columnspan=4, sticky='w', pady=(12, 0))
        IconButton(btn_r, 'Gợi ý ngành', self._run_tuyenthang, icon='🔍').pack(side=tk.LEFT)
        IconButton(btn_r, 'Xóa', self._clear_tuyenthang, icon='🗑',
                   bg='#64748b', hover='#475569').pack(side=tk.LEFT, padx=(10, 0))

        r_out, r_in = make_card(page, 'Kết quả gợi ý', padx=12, pady=12)
        r_out.pack(fill=tk.BOTH, expand=True)
        self._tbl_tt = ResultTable(r_in)
        self._tbl_tt.pack(fill=tk.BOTH, expand=True)

    def _clear_tuyenthang(self):
        self.tt_tb30.set(''); self.tt_anh.set('')
        self._tbl_tt.clear()

    def _run_tuyenthang(self):
        if tt_predict is None:
            messagebox.showerror('Lỗi', 'Không thể tải mô-đun Tuyển thẳng.')
            return
        if not self.tt_group.get().strip():
            messagebox.showwarning('Thiếu thông tin', 'Vui lòng chọn nhóm ngành.')
            return
        try:
            tb30 = float(self.tt_tb30.get())
        except Exception:
            messagebox.showwarning('Giá trị không hợp lệ', 'Tổng điểm TB phải là số.')
            return
        try:
            diem_anh = float(self.tt_anh.get()) if self.tt_anh.get() else 0.0
        except Exception:
            diem_anh = 0.0
        self._set_status('Đang xử lý Tuyển thẳng…')
        results = tt_predict(tb30, diem_anh, self.tt_group.get().strip(), top_n=12)
        self._tbl_tt.populate(results)
        self._set_status(f'Đã gợi ý {len(results)} ngành phù hợp (Tuyển thẳng)')

    # ══════════════════════════════════════════════════════════════════════
    #  PAGE – THPT QG (PT1)
    # ══════════════════════════════════════════════════════════════════════
    def _build_page_pt1(self):
        page = tk.Frame(self._content_host, bg=C['content_bg'])
        self._pages['THPT QG'] = page
        self._page_title(page, '📊  Xét tuyển THPT Quốc gia',
                         'Điểm thi tốt nghiệp THPT (3 môn + ưu tiên)')

        c_out, c_in = make_card(page, padx=20, pady=14)
        c_out.pack(fill=tk.X, pady=(0, 10))

        label_row(c_in, 'Nhóm ngành:', 0)
        self.pt1_group = tk.StringVar()
        cb = styled_combo(c_in, self.pt1_group, GROUP_OPTIONS, width=56)
        cb.grid(row=0, column=1, columnspan=3, sticky='w', pady=4)
        cb.bind('<<ComboboxSelected>>', self._on_pt1_group_changed)

        label_row(c_in, 'Tổ hợp môn:', 1)
        self.pt1_tohop = tk.StringVar()
        self.pt1_cb_tohop = styled_combo(c_in, self.pt1_tohop, [], width=16)
        self.pt1_cb_tohop.grid(row=1, column=1, sticky='w', pady=4)

        section_sep(c_in, 2)

        for lbl_t, attr, r in [
            ('Điểm Môn 1 (0–10):', 'pt1_m1', 3),
            ('Điểm Môn 2 (0–10):', 'pt1_m2', 4),
            ('Điểm Môn 3 (0–10):', 'pt1_m3', 5),
        ]:
            label_row(c_in, lbl_t, r)
            v = tk.StringVar()
            styled_entry(c_in, v, 10).grid(row=r, column=1, sticky='w', pady=4)
            setattr(self, attr, v)

        label_row(c_in, 'Điểm ưu tiên KV+ĐT:', 6)
        self.pt1_ut = tk.StringVar(value='0')
        styled_entry(c_in, self.pt1_ut, 10).grid(row=6, column=1, sticky='w', pady=4)

        label_row(c_in, 'Thứ tự nguyện vọng (1–5):', 6, col=2)
        self.pt1_nv = tk.StringVar(value='1')
        styled_entry(c_in, self.pt1_nv, 8).grid(row=6, column=3, sticky='w', pady=4)

        btn_r = tk.Frame(c_in, bg=C['card_bg'])
        btn_r.grid(row=7, column=0, columnspan=4, sticky='w', pady=(12, 0))
        IconButton(btn_r, 'Gợi ý ngành', self._run_pt1, icon='🔍').pack(side=tk.LEFT)
        IconButton(btn_r, 'Xóa', self._clear_pt1, icon='🗑',
                   bg='#64748b', hover='#475569').pack(side=tk.LEFT, padx=(10, 0))

        r_out, r_in = make_card(page, 'Kết quả gợi ý', padx=12, pady=12)
        r_out.pack(fill=tk.BOTH, expand=True)
        self._tbl_pt1 = ResultTable(r_in)
        self._tbl_pt1.pack(fill=tk.BOTH, expand=True)

    def _on_pt1_group_changed(self, *_):
        vals = sorted(allowed_tohops_for_group(self.pt1_group.get())
                      if callable(allowed_tohops_for_group) else set())
        self.pt1_cb_tohop['values'] = vals
        if vals:
            self.pt1_cb_tohop.set(vals[0])

    def _clear_pt1(self):
        for attr in ('pt1_m1', 'pt1_m2', 'pt1_m3'):
            getattr(self, attr).set('')
        self.pt1_ut.set('0'); self.pt1_nv.set('1')
        self._tbl_pt1.clear()

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
            m1 = float(self.pt1_m1.get())
            m2 = float(self.pt1_m2.get())
            m3 = float(self.pt1_m3.get())
            ut = float(self.pt1_ut.get() or 0)
            nv = int(self.pt1_nv.get() or 1)
        except Exception:
            messagebox.showwarning('Giá trị không hợp lệ',
                                   'Điểm / thứ tự NV phải là số hợp lệ.')
            return
        self._set_status('Đang xử lý THPT QG…')
        results = goi_y_nganh_thpt(m1, m2, m3, diem_ut=ut, thu_tu_nv=nv,
                                    tohop=tohop, nguyen_vong=group, top_n=12)
        self._tbl_pt1.populate(results)
        self._set_status(f'Đã gợi ý {len(results)} ngành phù hợp (THPT QG)')


# ══════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = App()
    app.mainloop()
