import os
import urllib.request

def download_font(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    urllib.request.urlretrieve(url, dest_path)
    print("Done.")

if __name__ == "__main__":
    base_url = "https://github.com/PolymerElements/font-roboto-local/raw/master/fonts/roboto/"
    fonts = [
        "Roboto-Regular.ttf",
        "Roboto-Medium.ttf",
        "Roboto-Bold.ttf"
    ]
    assets_dir = os.path.join("apps", "desktop", "assets", "fonts")
    for font in fonts:
        url = base_url + font
        dest = os.path.join(assets_dir, font)
        try:
            download_font(url, dest)
        except Exception as e:
            print(f"Failed to download {font}: {e}")
