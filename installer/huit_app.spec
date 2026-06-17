# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file cho HUIT – Hệ thống Gợi ý Ngành học
# Tạo bởi build script – chạy: pyinstaller huit_app.spec

import os
from pathlib import Path

# SPECPATH là thư mục chứa file .spec (hiện là installer/)
# ROOT phải là thư mục gốc của dự án (lùi lại 1 cấp)
ROOT = Path(SPECPATH).parent

# ── Dữ liệu đi kèm (data files) ──────────────────────────────────────────
added_data = [
    # Toàn bộ thư mục models/
    (str(ROOT / 'models'), 'models'),
    # Logo và icon dùng trong cửa sổ desktop
    (str(ROOT / 'apps' / 'desktop' / 'assets'), 'apps/desktop/assets'),
    # Dataset nghiên cứu (giữ tương thích với bản đóng gói trước)
    (str(ROOT / 'data' / 'DXDuong.xlsx'), 'data'),
]

# ── Hidden imports bắt buộc khi pack sklearn/numpy/pandas ────────────────
hidden_imports = [
    'apps',
    'apps.desktop.app',
    'apps.desktop.theme',
    'huit_career_advisor',
    'huit_career_advisor.domain.advisory',
    'huit_career_advisor.domain.catalog',
    'huit_career_advisor.inference.academic_record',
    'huit_career_advisor.inference.dgnl',
    'huit_career_advisor.inference.direct_admission',
    'huit_career_advisor.inference.thpt',
    'scripts', # Đảm bảo package scripts được nhận diện
    'scripts.Goi_y_nganh_nghe',
    'scripts.Goi_y_nganh_hoc_ba',
    'scripts.Goi_y_nganh_thpt',
    'scripts.Goi_y_nganh_tuyen_thang',
    'scripts.hoc_ba_analyzer',
    'sklearn',
    'sklearn.ensemble',
    'sklearn.ensemble._forest',
    'sklearn.naive_bayes',
    'sklearn.svm',
    'sklearn.preprocessing',
    'sklearn.pipeline',
    'sklearn.utils',
    'sklearn.metrics',
    'sklearn.model_selection',
    'sklearn.tree',
    'sklearn.neighbors',
    'sklearn.linear_model',
    'numpy',
    'scipy',
    'scipy.special',
    'scipy.linalg',
    'scipy.sparse',
    'pandas',
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',
    'joblib',
    'joblib.externals.loky',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
]

a = Analysis(
    [str(ROOT / 'app_gui.py')], # Đường dẫn tuyệt đối tới file chính
    pathex=[str(ROOT)],
    binaries=[],
    datas=added_data,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(ROOT / '_runtime_hook.py')],
    excludes=[
        'matplotlib', 'PIL', 'cv2', 'torch', 'tensorflow',
        'IPython', 'jupyter', 'notebook', 'pytest', 'sphinx',
        'docutils', 'cryptography', 'ssl',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HUIT_GoiYNganh',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'apps' / 'desktop' / 'assets' / 'app_icon.ico'),
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HUIT_GoiYNganh',
)
