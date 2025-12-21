#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI ứng dụng gợi ý ngành HUIT (Tkinter)
- 4 tab: DGNL, Học bạ, Tuyển thẳng, PT1
- Runtime dùng các mô hình .pkl trong thư mục models/ (đã có sẵn)

Yêu cầu: Python 3.8+, không cần thư viện ngoài chuẩn.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

# Bảo đảm Unicode trên Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# Import các mô-đun hiện có
try:
    from Goi_y_nganh_nghe import goi_y_nganh_simple as dgnl_predict
except Exception as e:
    dgnl_predict = None

try:
    from Goi_y_nganh_thpt import goi_y_nganh_thpt, allowed_tohops_for_group
except Exception:
    goi_y_nganh_thpt = None
    allowed_tohops_for_group = lambda g: set()

try:
    from Goi_y_nganh_tuyen_thang import goi_y_nganh_tuyen_thang_simple as tt_predict
except Exception:
    tt_predict = None

try:
    from hoc_ba_analyzer import HocBaAnalyzer, TO_HOP_MON
except Exception:
    HocBaAnalyzer = None
    TO_HOP_MON = {}


GROUP_OPTIONS = [
    'Công nghệ – Chế biến – Thực phẩm',
    'Kỹ thuật – Cơ khí – Tự động hóa',
    'Hóa học – Sinh học – Môi trường – Vật liệu',
    'Công nghệ thông tin – Trí tuệ nhân tạo – Dữ liệu',
    'Kinh doanh – Quản trị – Marketing',
    'Kế toán – Tài chính – Ngân hàng',
    'Logistics – Quản lý chuỗi cung ứng – Kinh doanh chuyên biệt',
    'Luật – Xã hội – Ngôn ngữ',
    'Du lịch – Nhà hàng – Khách sạn – Dịch vụ'
]


def _build_results_table(parent):
    cols = ("ma_nganh", "ten_nganh", "xac_suat", "flags")
    tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
    tree.heading("ma_nganh", text="Mã ngành")
    tree.heading("ten_nganh", text="Tên ngành")
    tree.heading("xac_suat", text="Xác suất (%)")
    tree.heading("flags", text="Ghi chú")
    tree.column("ma_nganh", width=100, anchor=tk.W)
    tree.column("ten_nganh", width=360, anchor=tk.W)
    tree.column("xac_suat", width=110, anchor=tk.E)
    tree.column("flags", width=180, anchor=tk.W)
    vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscroll=vsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)
    return tree


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HUIT – Gợi ý ngành (GUI)")
        self.geometry("900x650")
        self._build_ui()

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)

        # Tabs
        self.tab_dgnl = ttk.Frame(nb)
        self.tab_hb = ttk.Frame(nb)
        self.tab_tt = ttk.Frame(nb)
        self.tab_pt1 = ttk.Frame(nb)

        nb.add(self.tab_dgnl, text="DGNL")
        nb.add(self.tab_hb, text="Học bạ")
        nb.add(self.tab_tt, text="Tuyển thẳng")
        nb.add(self.tab_pt1, text="PT1 (THPT)")

        self._build_tab_dgnl()
        self._build_tab_hocba()
        self._build_tab_tuyenthang()
        self._build_tab_pt1()

    # =============== DGNL ==================
    def _build_tab_dgnl(self):
        frm = ttk.Frame(self.tab_dgnl, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)
        # Dòng 0: chọn cách nhập điểm
        ttk.Label(frm, text="Cách nhập điểm:").grid(row=0, column=0, sticky=tk.W)
        self.dgnl_input_mode = tk.StringVar(value='tong')
        ttk.Radiobutton(frm, text="Nhập tổng điểm DGNL", variable=self.dgnl_input_mode, value='tong').grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(frm, text="Nhập điểm từng môn", variable=self.dgnl_input_mode, value='mon').grid(row=0, column=2, sticky=tk.W)
        # Dòng 1: tổng điểm
        self.dgnl_total = tk.StringVar()
        self.dgnl_total_label = ttk.Label(frm, text="Tổng điểm DGNL (600–1200):")
        self.dgnl_total_entry = ttk.Entry(frm, textvariable=self.dgnl_total, width=20)
        self.dgnl_total_label.grid(row=1, column=0, sticky=tk.W)
        self.dgnl_total_entry.grid(row=1, column=1, sticky=tk.W)
        # Dòng 2-5: điểm từng môn
        dgnl_mon_names = ["Tiếng Việt", "Tiếng Anh", "Toán học", "Tư duy khoa học"]
        self.dgnl_mon_vars = []
        self.dgnl_mon_labels = []
        self.dgnl_mon_entries = []
        for i, mon in enumerate(dgnl_mon_names):
            var = tk.StringVar()
            lbl = ttk.Label(frm, text=f"Điểm {mon} (0-300):", padding=(0, 4))
            ent = ttk.Entry(frm, textvariable=var, width=10)
            self.dgnl_mon_vars.append(var)
            self.dgnl_mon_labels.append(lbl)
            self.dgnl_mon_entries.append(ent)
            lbl.grid(row=2+i, column=0, sticky=tk.W, pady=2)
            ent.grid(row=2+i, column=1, sticky=tk.W, pady=2)
            lbl.grid_remove()
            ent.grid_remove()
        # Ô tổng điểm DGNL và tổng điểm xét tuyển
        self.dgnl_sum_label = ttk.Label(frm, text="Tổng điểm DGNL:")
        self.dgnl_sum_value = ttk.Label(frm, text="0 / 1200", font=("Segoe UI", 11, "bold"))
        self.dgnl_sum_label.grid(row=6, column=0, sticky=tk.W, pady=(4,2))
        self.dgnl_sum_value.grid(row=6, column=1, sticky=tk.W, pady=(4,2))
        self.dgnl_sum_label.grid_remove()
        self.dgnl_sum_value.grid_remove()
        self.dgnl_xt_label = ttk.Label(frm, text="Tổng điểm xét tuyển:")
        self.dgnl_xt_value = ttk.Label(frm, text="0 / 1200", font=("Segoe UI", 11, "bold"))
        self.dgnl_xt_label.grid(row=6, column=2, sticky=tk.W, pady=(4,2))
        self.dgnl_xt_value.grid(row=6, column=3, sticky=tk.W, pady=(4,2))
        self.dgnl_xt_label.grid_remove()
        self.dgnl_xt_value.grid_remove()
        row = 7
        # Nhóm ngành
        ttk.Label(frm, text="Nhóm ngành ưa thích (tùy chọn):").grid(row=row, column=0, sticky=tk.W)
        self.dgnl_group = tk.StringVar()
        ttk.Combobox(frm, textvariable=self.dgnl_group, values=["(Không)"] + GROUP_OPTIONS, state="readonly", width=60).grid(row=row, column=1, sticky=tk.W)
        self.dgnl_group.set("(Không)")
        row += 1
        # Điểm ưu tiên
        ttk.Label(frm, text="Đối tượng ưu tiên:").grid(row=row, column=0, sticky=tk.W)
        self.dgnl_ut = tk.StringVar(value='none')
        ttk.Combobox(frm, textvariable=self.dgnl_ut, values=["none", "ƯT1 (01–04)", "ƯT2 (05–07)"], state="readonly", width=15).grid(row=row, column=1, sticky=tk.W)
        ttk.Label(frm, text="Khu vực:").grid(row=row, column=2, sticky=tk.W)
        self.dgnl_kv = tk.StringVar(value='KV3')
        ttk.Combobox(frm, textvariable=self.dgnl_kv, values=["KV1", "KV2-NT", "KV2", "KV3"], state="readonly", width=10).grid(row=row, column=3, sticky=tk.W)
        row += 1
        self.dgnl_ut_display = ttk.Label(frm, text="")
        self.dgnl_ut_display.grid(row=row, column=0, columnspan=4, sticky=tk.W)
        row += 1
        ttk.Button(frm, text="Gợi ý", command=self._run_dgnl).grid(row=row, column=0, pady=6, sticky=tk.W)
        row += 1
        res_frame = ttk.LabelFrame(frm, text="Kết quả", padding=5)
        res_frame.grid(row=row, column=0, columnspan=4, sticky="nsew")
        frm.grid_rowconfigure(row, weight=1)
        frm.grid_columnconfigure(1, weight=1)
        self.tree_dgnl = _build_results_table(res_frame)
        # Sự kiện chuyển đổi nhập điểm
        def _toggle_dgnl_input(*_):
            mode = self.dgnl_input_mode.get()
            if mode == 'tong':
                self.dgnl_total_label.grid()
                self.dgnl_total_entry.grid()
                for i in range(4):
                    self.dgnl_mon_labels[i].grid_remove()
                    self.dgnl_mon_entries[i].grid_remove()
                self.dgnl_sum_label.grid_remove()
                self.dgnl_sum_value.grid_remove()
                self.dgnl_xt_label.grid()
                self.dgnl_xt_value.grid()
            else:
                self.dgnl_total_label.grid_remove()
                self.dgnl_total_entry.grid_remove()
                for i in range(4):
                    self.dgnl_mon_labels[i].grid()
                    self.dgnl_mon_entries[i].grid()
                self.dgnl_sum_label.grid()
                self.dgnl_sum_value.grid()
                self.dgnl_xt_label.grid()
                self.dgnl_xt_value.grid()
        def _update_sum_and_xt(*_):
            try:
                if self.dgnl_input_mode.get() == 'mon':
                    s = sum(float(v.get() or 0) for v in self.dgnl_mon_vars)
                else:
                    s = float(self.dgnl_total.get() or 0)
            except:
                s = 0
            # Tính điểm ưu tiên
            ut_map = {'none': 0, 'ƯT1 (01–04)': 80, 'ƯT2 (05–07)': 40}
            kv_map = {'KV1': 30, 'KV2-NT': 20, 'KV2': 10, 'KV3': 0}
            muc_ut = ut_map.get(self.dgnl_ut.get(), 0)
            muc_kv = kv_map.get(self.dgnl_kv.get(), 0)
            diem_ut = muc_ut + muc_kv
            if s >= 900 and diem_ut > 0:
                diem_ut = ((1200 - s) / 300) * diem_ut
                diem_ut = round(diem_ut, 2)
            self.dgnl_sum_value.config(text=f"{s:.0f} / 1200")
            self.dgnl_xt_value.config(text=f"{s+diem_ut:.2f} / 1200")
        for v in self.dgnl_mon_vars:
            v.trace_add("write", _update_sum_and_xt)
        self.dgnl_total.trace_add("write", _update_sum_and_xt)
        self.dgnl_ut.trace_add("write", _update_sum_and_xt)
        self.dgnl_kv.trace_add("write", _update_sum_and_xt)
        self.dgnl_input_mode.trace_add('write', _toggle_dgnl_input)
        self.dgnl_input_mode.trace_add('write', _update_sum_and_xt)
        _toggle_dgnl_input()
        _update_sum_and_xt()

    def _run_dgnl(self):
        if dgnl_predict is None:
            messagebox.showerror("Lỗi", "Không thể tải mô-đun DGNL. Kiểm tra file 'Goi_y_nganh_nghe.py'.")
            return
        mode = self.dgnl_input_mode.get()
        diem_thanh_phan = None
        if mode == 'tong':
            try:
                diem = float(self.dgnl_total.get())
                if not (600 <= diem <= 1200):
                    raise ValueError()
            except Exception:
                messagebox.showwarning("Giá trị không hợp lệ", "Vui lòng nhập số (600–1200).")
                return
        else:
            try:
                mon_labels = ["Tiếng Việt", "Tiếng Anh", "Toán học", "Tư duy khoa học"]
                diem_thanh_phan = {
                    'vietnamese': float(self.dgnl_mon_vars[0].get() or 0),
                    'english': float(self.dgnl_mon_vars[1].get() or 0),
                    'math': float(self.dgnl_mon_vars[2].get() or 0),
                    'science': float(self.dgnl_mon_vars[3].get() or 0)
                }
                # Kiểm tra từng môn
                for i, key in enumerate(['vietnamese','english','math','science']):
                    val = diem_thanh_phan[key]
                    if not (0 <= val <= 300):
                        messagebox.showwarning("Sai giá trị", f"Điểm {mon_labels[i]} phải từ 0-300!")
                        return
                diem = sum(diem_thanh_phan.values())
                if not (600 <= diem <= 1200):
                    messagebox.showwarning("Sai tổng điểm", "Tổng điểm phải từ 600 đến 1200.")
                    return
                # Tổng kết từng môn
                mon_icons = ['📝','🌍','🔢','🧪']
                ket_qua = [f"   {icon} {mon_labels[i]}: {diem_thanh_phan[k]:.1f}" for i,(icon,k) in enumerate(zip(mon_icons,['vietnamese','english','math','science']))]
                msg = "✅ TỔNG KẾT ĐIỂM DGNL:\n" + "\n".join(ket_qua) + f"\n   📊 TỔNG ĐIỂM: {diem:.1f}/1200"
                # Phân tích thế mạnh
                the_manh = []
                if diem_thanh_phan['math'] >= 240:
                    the_manh.append('Toán học')
                if diem_thanh_phan['english'] >= 240:
                    the_manh.append('Tiếng Anh')
                if diem_thanh_phan['science'] >= 240:
                    the_manh.append('Tư duy khoa học')
                if diem_thanh_phan['vietnamese'] >= 240:
                    the_manh.append('Tiếng Việt')
                if the_manh:
                    msg += "\n\n🎯 PHÂN TÍCH THẾ MẠNH:\n   " + ", ".join(the_manh)
                else:
                    msg += "\n\n🎯 PHÂN TÍCH THẾ MẠNH:\n   ⚠️ Chưa có môn nào nổi bật (>= 240 điểm)"
                # Cần cải thiện
                yeu_diem = []
                for k, ten in zip(['vietnamese','english','math','science'], mon_labels):
                    if diem_thanh_phan[k] < 180:
                        yeu_diem.append(f"📉 {ten} ({diem_thanh_phan[k]:.1f} điểm)")
                if yeu_diem:
                    msg += "\n\n📈 CẦN CẢI THIỆN:\n   " + "\n   ".join(yeu_diem)
                messagebox.showinfo("Phân tích thành phần DGNL", msg)
            except Exception as e:
                messagebox.showwarning("Lỗi nhập", f"{e}")
                return
        # Tính điểm ưu tiên
        ut_map = {'none': 0, 'ƯT1 (01–04)': 80, 'ƯT2 (05–07)': 40}
        kv_map = {'KV1': 30, 'KV2-NT': 20, 'KV2': 10, 'KV3': 0}
        muc_ut = ut_map.get(self.dgnl_ut.get(), 0)
        muc_kv = kv_map.get(self.dgnl_kv.get(), 0)
        diem_ut = muc_ut + muc_kv
        # Quy định mới: nếu tổng điểm >= 900 thì điểm ưu tiên giảm tuyến tính
        if diem >= 900 and diem_ut > 0:
            diem_ut = ((1200 - diem) / 300) * diem_ut
            diem_ut = round(diem_ut, 2)
        self.dgnl_ut_display.config(text=f"Điểm ưu tiên được cộng: {diem_ut} (theo quy định mới)")
        group = self.dgnl_group.get()
        if group == "(Không)":
            group = None
        results = dgnl_predict(diem, diem_dt=0, diem_kv=diem_ut, thu_tu_nv=1, nguyen_vong=group, top_n=12)
        self._populate_results(self.tree_dgnl, results)

    # =============== HỌC BẠ =================
    def _build_tab_hocba(self):
        frm = ttk.Frame(self.tab_hb, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frm, text="Chọn nhóm ngành:").grid(row=row, column=0, sticky=tk.W)
        self.hb_group = tk.StringVar()
        cb = ttk.Combobox(frm, textvariable=self.hb_group, values=GROUP_OPTIONS, state="readonly", width=60)
        cb.grid(row=row, column=1, sticky=tk.W)
        cb.bind("<<ComboboxSelected>>", self._on_hb_group_changed)

        row += 1
        ttk.Label(frm, text="Chọn tổ hợp:").grid(row=row, column=0, sticky=tk.W)
        self.hb_tohop = tk.StringVar()
        self.hb_cb_tohop = ttk.Combobox(frm, textvariable=self.hb_tohop, values=[], state="readonly", width=20)
        self.hb_cb_tohop.grid(row=row, column=1, sticky=tk.W)

        # Điểm TB 3 môn (đơn giản hóa nhập liệu)
        row += 1
        ttk.Label(frm, text="Điểm TB Môn 1 (0-10):").grid(row=row, column=0, sticky=tk.W)
        self.hb_m1 = tk.StringVar(); ttk.Entry(frm, textvariable=self.hb_m1, width=10).grid(row=row, column=1, sticky=tk.W)
        row += 1
        ttk.Label(frm, text="Điểm TB Môn 2 (0-10):").grid(row=row, column=0, sticky=tk.W)
        self.hb_m2 = tk.StringVar(); ttk.Entry(frm, textvariable=self.hb_m2, width=10).grid(row=row, column=1, sticky=tk.W)
        row += 1
        ttk.Label(frm, text="Điểm TB Môn 3 (0-10):").grid(row=row, column=0, sticky=tk.W)
        self.hb_m3 = tk.StringVar(); ttk.Entry(frm, textvariable=self.hb_m3, width=10).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(frm, text="Điểm ưu tiên KV+ĐT (0-3):").grid(row=row, column=0, sticky=tk.W)
        self.hb_ut = tk.StringVar(value="0"); ttk.Entry(frm, textvariable=self.hb_ut, width=10).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Button(frm, text="Gợi ý", command=self._run_hocba).grid(row=row, column=0, pady=6, sticky=tk.W)

        row += 1
        res_frame = ttk.LabelFrame(frm, text="Kết quả", padding=5)
        res_frame.grid(row=row, column=0, columnspan=2, sticky="nsew")
        frm.grid_rowconfigure(row, weight=1)
        frm.grid_columnconfigure(1, weight=1)
        self.tree_hb = _build_results_table(res_frame)

    def _on_hb_group_changed(self, *_):
        group = self.hb_group.get()
        # Lấy tổ hợp từ mô-đun PT1 để giữ đồng bộ
        tohop_set = allowed_tohops_for_group(group) if callable(allowed_tohops_for_group) else set()
        self.hb_cb_tohop["values"] = sorted(list(tohop_set))
        if tohop_set:
            self.hb_cb_tohop.set(sorted(list(tohop_set))[0])

    def _run_hocba(self):
        if HocBaAnalyzer is None:
            messagebox.showerror("Lỗi", "Không thể tải HocBaAnalyzer. Kiểm tra 'hoc_ba_analyzer.py'.")
            return
        group = self.hb_group.get().strip()
        tohop = self.hb_tohop.get().strip().upper()
        if not group or not tohop:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn nhóm ngành và tổ hợp.")
            return
        try:
            m1 = float(self.hb_m1.get()); m2 = float(self.hb_m2.get()); m3 = float(self.hb_m3.get())
            ut = float(self.hb_ut.get()) if self.hb_ut.get() else 0.0
        except Exception:
            messagebox.showwarning("Giá trị không hợp lệ", "Điểm phải là số.")
            return
        if not (0 <= m1 <= 10 and 0 <= m2 <= 10 and 0 <= m3 <= 10):
            messagebox.showwarning("Giá trị không hợp lệ", "Điểm TB môn phải trong [0,10].")
            return

        # Tạo diem_hb_info tối giản theo interface của analyzer
        analyzer = HocBaAnalyzer()
        if not analyzer.load_models():
            messagebox.showerror("Thiếu mô hình", "Chưa có models/hocba_models.pkl. Hãy huấn luyện trước.")
            return
        diem_hb_info = {
            'to_hop': tohop,
            'mon_hoc': TO_HOP_MON.get(tohop, []),
            'diem_tb_mon1': m1,
            'diem_tb_mon2': m2,
            'diem_tb_mon3': m3,
            'diem_hb': round(m1 + m2 + m3 + ut, 2),
            'diem_xet_tuyen': round(m1 + m2 + m3 + ut, 2)
        }
        results = analyzer.predict_nganh(diem_hb_info, top_k=12, nguyen_vong=group)
        self._populate_results(self.tree_hb, results)

    # =============== TUYỂN THẲNG ============
    def _build_tab_tuyenthang(self):
        frm = ttk.Frame(self.tab_tt, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frm, text="Chọn nhóm ngành:").grid(row=row, column=0, sticky=tk.W)
        self.tt_group = tk.StringVar()
        ttk.Combobox(frm, textvariable=self.tt_group, values=GROUP_OPTIONS, state="readonly", width=60).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(frm, text="Tổng điểm TB 3 năm (thang 30):").grid(row=row, column=0, sticky=tk.W)
        self.tt_tb30 = tk.StringVar(); ttk.Entry(frm, textvariable=self.tt_tb30, width=10).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(frm, text="Điểm Tiếng Anh (0-10, tùy chọn):").grid(row=row, column=0, sticky=tk.W)
        self.tt_anh = tk.StringVar(value=""); ttk.Entry(frm, textvariable=self.tt_anh, width=10).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Button(frm, text="Gợi ý", command=self._run_tuyenthang).grid(row=row, column=0, pady=6, sticky=tk.W)

        row += 1
        res_frame = ttk.LabelFrame(frm, text="Kết quả", padding=5)
        res_frame.grid(row=row, column=0, columnspan=2, sticky="nsew")
        frm.grid_rowconfigure(row, weight=1)
        frm.grid_columnconfigure(1, weight=1)
        self.tree_tt = _build_results_table(res_frame)

    def _run_tuyenthang(self):
        if tt_predict is None:
            messagebox.showerror("Lỗi", "Không thể tải mô-đun Tuyển thẳng.")
            return
        group = self.tt_group.get().strip()
        if not group:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn nhóm ngành.")
            return
        try:
            tb30 = float(self.tt_tb30.get())
        except Exception:
            messagebox.showwarning("Giá trị không hợp lệ", "Tổng điểm TB (30) phải là số.")
            return
        try:
            diem_anh = float(self.tt_anh.get()) if self.tt_anh.get() else 0.0
        except Exception:
            diem_anh = 0.0
        results = tt_predict(tb30, diem_anh, group, top_n=12)
        self._populate_results(self.tree_tt, results)

    # =============== PT1 ====================
    def _build_tab_pt1(self):
        frm = ttk.Frame(self.tab_pt1, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frm, text="Chọn nhóm ngành:").grid(row=row, column=0, sticky=tk.W)
        self.pt1_group = tk.StringVar()
        cb = ttk.Combobox(frm, textvariable=self.pt1_group, values=GROUP_OPTIONS, state="readonly", width=60)
        cb.grid(row=row, column=1, sticky=tk.W)
        cb.bind("<<ComboboxSelected>>", self._on_pt1_group_changed)

        row += 1
        ttk.Label(frm, text="Chọn tổ hợp:").grid(row=row, column=0, sticky=tk.W)
        self.pt1_tohop = tk.StringVar()
        self.pt1_cb_tohop = ttk.Combobox(frm, textvariable=self.pt1_tohop, values=[], state="readonly", width=20)
        self.pt1_cb_tohop.grid(row=row, column=1, sticky=tk.W)

        # Điểm
        row += 1
        ttk.Label(frm, text="Điểm môn 1 (0-10):").grid(row=row, column=0, sticky=tk.W)
        self.pt1_m1 = tk.StringVar(); ttk.Entry(frm, textvariable=self.pt1_m1, width=10).grid(row=row, column=1, sticky=tk.W)
        row += 1
        ttk.Label(frm, text="Điểm môn 2 (0-10):").grid(row=row, column=0, sticky=tk.W)
        self.pt1_m2 = tk.StringVar(); ttk.Entry(frm, textvariable=self.pt1_m2, width=10).grid(row=row, column=1, sticky=tk.W)
        row += 1
        ttk.Label(frm, text="Điểm môn 3 (0-10):").grid(row=row, column=0, sticky=tk.W)
        self.pt1_m3 = tk.StringVar(); ttk.Entry(frm, textvariable=self.pt1_m3, width=10).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(frm, text="Điểm ưu tiên (KV+ĐT):").grid(row=row, column=0, sticky=tk.W)
        self.pt1_ut = tk.StringVar(value="0"); ttk.Entry(frm, textvariable=self.pt1_ut, width=10).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(frm, text="Thứ tự NV (1-5):").grid(row=row, column=0, sticky=tk.W)
        self.pt1_nv = tk.StringVar(value="1"); ttk.Entry(frm, textvariable=self.pt1_nv, width=10).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Button(frm, text="Gợi ý", command=self._run_pt1).grid(row=row, column=0, pady=6, sticky=tk.W)

        row += 1
        res_frame = ttk.LabelFrame(frm, text="Kết quả", padding=5)
        res_frame.grid(row=row, column=0, columnspan=2, sticky="nsew")
        frm.grid_rowconfigure(row, weight=1)
        frm.grid_columnconfigure(1, weight=1)
        self.tree_pt1 = _build_results_table(res_frame)

    def _on_pt1_group_changed(self, *_):
        group = self.pt1_group.get()
        tohop_set = allowed_tohops_for_group(group) if callable(allowed_tohops_for_group) else set()
        self.pt1_cb_tohop["values"] = sorted(list(tohop_set))
        if tohop_set:
            self.pt1_cb_tohop.set(sorted(list(tohop_set))[0])

    def _run_pt1(self):
        if goi_y_nganh_thpt is None:
            messagebox.showerror("Lỗi", "Không thể tải mô-đun PT1.")
            return
        group = self.pt1_group.get().strip()
        tohop = self.pt1_tohop.get().strip().upper()
        if not group or not tohop:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn nhóm ngành và tổ hợp.")
            return
        try:
            m1 = float(self.pt1_m1.get()); m2 = float(self.pt1_m2.get()); m3 = float(self.pt1_m3.get())
            ut = float(self.pt1_ut.get()) if self.pt1_ut.get() else 0.0
            nv = int(self.pt1_nv.get()) if self.pt1_nv.get() else 1
        except Exception:
            messagebox.showwarning("Giá trị không hợp lệ", "Điểm/Thứ tự NV phải là số.")
            return
        results = goi_y_nganh_thpt(m1, m2, m3, diem_ut=ut, thu_tu_nv=nv, tohop=tohop, nguyen_vong=group, top_n=12)
        # Kết quả đã bao gồm cờ to_hop_phu_hop, thuoc_nhom_mong_muon
        self._populate_results(self.tree_pt1, results)

    # =============== Helpers ================
    def _populate_results(self, tree: ttk.Treeview, results):
        for i in tree.get_children():
            tree.delete(i)
        if not results:
            return
        for item in results:
            ma = item.get('ma_nganh')
            ten = item.get('ten_nganh')
            xs = item.get('xac_suat')
            flags = []
            if item.get('to_hop_phu_hop') is True:
                flags.append('✅ tổ hợp phù hợp')
            if item.get('to_hop_phu_hop') is False:
                flags.append('⚠️ không mở tổ hợp')
            if item.get('thuoc_nhom_mong_muon') is True:
                flags.append('🎯 thuộc nhóm')
            if item.get('thuoc_nhom_mong_muon') is False:
                # Chỉ gắn cờ "ngoài nhóm" khi user có chọn nhóm
                flags.append('📊 ngoài nhóm')
            tree.insert('', tk.END, values=(ma, ten, xs, ", ".join(flags)))


if __name__ == '__main__':
    app = App()
    app.mainloop()