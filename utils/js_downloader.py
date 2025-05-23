import os, re
import requests
from urllib.parse import urlparse

def download_js_file(js_url: str, save_dir: str) -> str:
    try:
        os.makedirs(save_dir, exist_ok=True)
        file_name = os.path.basename(urlparse(js_url).path)
        file_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file_name)
        if not file_name.endswith(".js"):
            file_name += ".js"
        save_path = os.path.join(save_dir, file_name)
        
        response = requests.get(js_url, timeout=5)
        if response.ok:
            with open(save_path, "wb") as f:
                f.write(response.content)
            return save_path
        else:
            return ""
    except Exception as e:
        print(f"[Download Error] {js_url} → {e}")
        return ""
