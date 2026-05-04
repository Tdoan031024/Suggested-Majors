from PIL import Image
import os

img_path = r'd:\ADuong_HUIT\Code_goi_y_huong_nghiep\logo_cropped_m.png'
ico_path = r'd:\ADuong_HUIT\Code_goi_y_huong_nghiep\app_icon.ico'

if os.path.exists(img_path):
    img = Image.open(img_path).convert("RGBA")
    # Since user already cropped it, we just ensure it's resized to standard icon sizes
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, sizes=icon_sizes)
    print(f"Successfully converted {img_path} to {ico_path}")
else:
    print("Source image not found.")
