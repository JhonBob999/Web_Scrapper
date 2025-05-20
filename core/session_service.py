# core/session_service.py

import os
import json
from datetime import datetime

# Определяем директории для хранения сессий и результатов
SESSIONS_DIR = "sessions"
RESULTS_DIR = "results"

os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ========= Функции для работы с сессиями (были в session_manager.py) =========

def generate_session_name():
    """Генерирует имя сессии на основе текущей даты и времени."""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    return f"session_{now}"

def save_session(session_name, tasks):
    """
    Сохраняет текущую сессию.
    :param session_name: имя сессии
    :param tasks: список словарей с параметрами задач
    :return: путь к файлу сохранённой сессии
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
    """Загружает сессию по заданному пути к JSON-файлу."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_sessions():
    """
    Возвращает список всех сессий с информацией (имя файла, дата, количество задач).
    :return: список словарей с данными сессий
    """
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
    """Удаляет файл сессии по заданному пути."""
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def get_cookie_file_name(url):
    """
    Возвращает имя файла cookies для указанного URL.
    Предполагается, что функция get_cookie_path определена в модуле cookie_manager.
    """
    from core.cookie_manager import get_cookie_path
    return os.path.basename(get_cookie_path(url))

# ========= Класс для работы с сессиями в UI (был в session_controller.py) =========

class SessionController:
    """
    Класс, отвечающий за интеграцию сохранения/восстановления сессии с UI.
    Использует функции сохранения сессии, определённые выше.
    """

    def __init__(self, table_controller, add_task_callback, task_params, task_results, task_intervals):
        self.table = table_controller
        self.add_task = add_task_callback
        self.task_params = task_params
        self.task_results = task_results
        self.task_intervals = task_intervals

    def save_session(self, session_name):
        """
        Сохраняет сессию, собирая данные по всем задачам из таблицы.
        :param session_name: имя сессии
        :return: путь к сохранённому файлу сессии
        """
        tasks = []

        for row in range(self.table.table.rowCount()):
            task = self.table.get_task_data(row)
            params = self.task_params.get(row, {})
            results = self.task_results.get(row, [])
            timer_interval = self.task_intervals.get(row, 0)
            cookies_file = get_cookie_file_name(task["url"])

            tasks.append({
                "url": task["url"],
                "selector": task["selector"],
                "method": task["method"],
                "status": task["status"],
                "params": params,
                "cookies_file": cookies_file,
                "results": results,
                "timer_interval": timer_interval,
                "last_run": task["last_run"],
            })

        return save_session(session_name, tasks)

    def restore_session(self, session_data):
        """
        Восстанавливает сессию из данных, загруженных из JSON.
        Заполняет таблицу и соответствующие словари параметров, результатов и интервалов.
        :param session_data: данные сессии (словарь)
        """
        from PyQt5.QtWidgets import QTableWidgetItem

        self.clear_all_tasks()

        for i, task in enumerate(session_data.get("tasks", [])):
            self.add_task(task["url"], task["selector"], task["method"], task["status"])

            self.task_params[i] = task.get("params", {})
            self.task_results[i] = {
                "url": task["url"],
                "status": task["status"],
                "results": task.get("results", []),
                "message": task.get("log_path", ""),
                "last_run": task.get("last_run", "")
            }
            self.task_intervals[i] = task.get("timer_interval", 0)

            # Обновляем отображение "Last Run"
            self.table.set_last_run(i, task.get("last_run", ""))

            # Устанавливаем tooltip для cookies
            self.table.table.setItem(i, 7, QTableWidgetItem(task.get("cookies_file", "")))

            # Устанавливаем иконку для параметров
            self.table.table.setItem(i, 8, QTableWidgetItem("🛠 Настроить"))

            # Записываем интервал таймера
            timer_text = f"{self.task_intervals[i]} сек" if self.task_intervals[i] else "–"
            self.table.table.setItem(i, 9, QTableWidgetItem(timer_text))

        self.table.table.resizeColumnsToContents()

    def clear_all_tasks(self):
        """
        Очищает таблицу и внутренние словари, связанные с задачами.
        """
        self.table.table.setRowCount(0)
        self.task_params.clear()
        self.task_results.clear()
        self.task_intervals.clear()
