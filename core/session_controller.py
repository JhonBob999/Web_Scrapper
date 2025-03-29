# core/session_controller.py

import os
import json
from datetime import datetime
from core import session_manager

class SessionController:
    def __init__(self, table_controller, add_task_callback, task_params, task_results, task_intervals):
        self.table = table_controller
        self.add_task = add_task_callback
        self.task_params = task_params
        self.task_results = task_results
        self.task_intervals = task_intervals

    def save_session(self, session_name):
        tasks = []

        for row in range(self.table.table.rowCount()):
            task = self.table.get_task_data(row)
            params = self.task_params.get(row, {})
            results = self.task_results.get(row, [])
            timer_interval = self.task_intervals.get(row, 0)
            cookies_file = session_manager.get_cookie_file_name(task["url"])

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

        return session_manager.save_session(session_name, tasks)

    def restore_session(self, session_data):
        from PyQt5.QtWidgets import QTableWidgetItem
        from datetime import datetime

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

            # Last Run
            self.table.set_last_run(i, task.get("last_run", ""))

            # Cookies tooltip
            self.table.table.setItem(i, 7, QTableWidgetItem(task.get("cookies_file", "")))

            # Params icon
            self.table.table.setItem(i, 8, QTableWidgetItem("🛠 Настроить"))

            # Timer column
            timer_text = f"{self.task_intervals[i]} сек" if self.task_intervals[i] else "–"
            self.table.table.setItem(i, 9, QTableWidgetItem(timer_text))

        self.table.table.resizeColumnsToContents()

    def clear_all_tasks(self):
        self.table.table.setRowCount(0)
        self.task_params.clear()
        self.task_results.clear()
        self.task_intervals.clear()
