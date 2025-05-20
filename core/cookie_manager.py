import os
import json
from urllib.parse import urlparse

COOKIES_DIR = "./cookies"

def sanitize_url(url: str) -> str:
    """
    Превращает https://cnn.com в cnn.com,
    https://example.com/news -> example.com_news
    cnn.com -> cnn.com
    """
    parsed = urlparse(url)
    netloc = parsed.netloc or parsed.path  # подстраховка если без схемы
    path = parsed.path.replace("/", "_").strip("_")

    # 🧠 если path дублирует netloc — не повторяем
    if path == netloc or path == "":
        return netloc.replace(":", "_")
    
    return f"{netloc}_{path}".replace(":", "_")


def get_cookie_path(url: str):
    os.makedirs(COOKIES_DIR, exist_ok=True)
    filename = f"cookies_{sanitize_url(url)}.json"
    return os.path.join(COOKIES_DIR, filename)

def save_cookies(url: str, cookies: dict):
    path = get_cookie_path(url)

    # 🔒 Если cookies пустые и файл уже существует — не перезаписываем
    if not cookies and os.path.exists(path):
        print(f"[cookie_manager] Пустые куки, файл уже существует — не сохраняем: {path}")
        return

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=4, ensure_ascii=False)

    print(f"[cookie_manager] Куки сохранены: {path}")

def load_cookies(url: str):
    path = get_cookie_path(url)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def cookie_exists(url: str):
    return os.path.exists(get_cookie_path(url))
