# Runtime hook: đảm bảo working directory = thư mục chứa .exe
# PyInstaller sẽ chạy hook này trước khi khởi động app_gui.py
import sys
import os

# Chuyển CWD về thư mục chứa executable (dist/HUIT_GoiYNganh/)
# Để các đường dẫn tương đối như "models/hocba_models.pkl" hoạt động đúng
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
