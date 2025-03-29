import os
import json
from datetime import datetime

SESSIONS_DIR = "sessions"
RESULTS_DIR = "results"

os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def generate_session_name():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    return f"session_{now}"

def save_session(session_name, tasks):
    """
    Сохраняет текущую сессию.
    tasks — список словарей с параметрами задач
    """
    session_data = {
        "session_name": session_name,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tasks": []
    }

    result_dir = os.path.join(RESULTS_DIR, session_name)
    os.makedirs(result_dir, exist_ok=True)

    for i, task in enumerate(tasks):
        result_path = None
        if task.get("results"):
            result_path = os.path.join(result_dir, f"task_{i}.json")
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(task["results"], f, indent=4, ensure_ascii=False)

        session_data["tasks"].append({
            "url": task.get("url", ""),
            "selector": task.get("selector", ""),
            "method": task.get("method", "CSS"),
            "status": task.get("status", "Ожидает"),
            "params": task.get("params", {}),
            "cookies_file": task.get("cookies_file", ""),
            "results_path": result_path,
            "log_path": task.get("log_path", ""),
            "timer_interval": task.get("timer_interval", 0),
            "last_run": task.get("last_run", "")
        })

    path = os.path.join(SESSIONS_DIR, f"{session_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=4, ensure_ascii=False)

    return path

def load_session(path):
    """Загружает сессию по пути к JSON"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_sessions():
    """Возвращает список всех сессий (имя файла, дата)"""
    sessions = []
    for file in sorted(os.listdir(SESSIONS_DIR), reverse=True):
        if file.endswith(".json"):
            path = os.path.join(SESSIONS_DIR, file)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                sessions.append({
                    "file": file,
                    "path": path,
                    "session_name": data.get("session_name", file),
                    "datetime": data.get("datetime", ""),
                    "task_count": len(data.get("tasks", []))
                })
    return sessions

def delete_session(path):
    """Удаляет файл сессии"""
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def get_cookie_file_name(url):
    from .cookie_manager import get_cookie_path
    return os.path.basename(get_cookie_path(url))

