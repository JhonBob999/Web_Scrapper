import json
import os
from datetime import datetime

# SETTINGS MANAGER

DEFAULT_SETTINGS = {
    "dark_theme": False,
    "auto_save": False,
    "proxy_rotation": False,
    "last_used_proxy": ""
}

SETTINGS_FILE = "user_settings.json"

# LOAD SETTINGS
# LOAD SETTINGS

def load_settings():
    """Загружает настройки из файла или возвращает настройки по умолчанию."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        return DEFAULT_SETTINGS.copy()

# SAVE SETTINGS
# SAVE SETTINGS

def save_settings(settings):
    """Сохраняет настройки в файл."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)

# RESET SETTINGS
# RESET SETTINGS

def reset_settings():
    """Сбрасывает настройки на умолчания."""
    save_settings(DEFAULT_SETTINGS.copy())
    
    
# HISTORY MANAGER

HISTORY_FILE = "history.json"
MAX_HISTORY_ITEMS = 10

# LOAD SCRAPPING HISTORY
# LOAD SCRAPPING HISTORY

def load_history():
    """Загружает историю парсинга из файла"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

# SAVE SCRAPPING HISTORY TO JSON
# SAVE SCRAPPING HISTORY TO JSON

def save_to_history(urls, selector, use_xpath):
    """Сохраняет новый запрос в историю парсинга"""
    history = load_history()

    new_item = {
        "urls": urls,
        "selector": selector,
        "use_xpath": use_xpath,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Убираем старые повторы, если они есть (чтобы не было дубликатов)
    history = [item for item in history if item["urls"] != urls or item["selector"] != selector]

    # Добавляем элемент в начало истории
    history.insert(0, new_item)

    # Ограничиваем размер истории
    history = history[:MAX_HISTORY_ITEMS]

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4, ensure_ascii=False)
