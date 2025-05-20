from PyQt5.QtCore import QObject
from core.task_worker import TaskWorker
from core import cookie_manager
from ui.table_utils import colorize_row_by_status
from datetime import datetime

class TaskManager(QObject):
    def __init__(self, table, task_results, task_params, update_lcd_callback, update_tooltips_callback, lock_row_callback):
        super().__init__()
        self.table = table
        self.task_results = task_results
        self.task_params = task_params
        self.update_lcd = update_lcd_callback
        self.update_tooltips = update_tooltips_callback
        self.lock_row = lock_row_callback
        self.workers = []

    def run_task(self, row):
        # Получаем данные из таблицы
        url_item = self.table.item(row, 1)
        selector_item = self.table.item(row, 2)
        method_item = self.table.item(row, 3)

        if not url_item or not selector_item or not method_item:
            return

        url = url_item.text().strip()
        selector = selector_item.text().strip()
        method = method_item.text().strip()

        if not url or not selector:
            return

        # Статус
        self.table.setItem(row, 4, self._create_item("⏳ Выполняется"))

        # Last Run
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.table.setItem(row, 10, self._create_item(now_str))

        # Заблокировать редактирование
        self.lock_row(row, True)

        # Параметры
        params = self.task_params.get(row, {})
        cookies = cookie_manager.load_cookies(url) or {}

        # Создаём и запускаем воркера
        worker = TaskWorker(row, url, selector, method, params=params, cookies=cookies)
        worker.task_finished.connect(self.on_task_finished)
        self.workers.append(worker)
        worker.start()

    def on_task_finished(self, row_index, status_text, message, results, cookies):
        self.table.setItem(row_index, 4, self._create_item(status_text))
        colorize_row_by_status(self.table, row_index)
        self.lock_row(row_index, False)  # 🔓 Разблокировать строку

        url = self.table.item(row_index, 1).text()
        cookie_manager.save_cookies(url, cookies)
        self.update_lcd()
        
        self.task_results[row_index] = {
            "url": url,
            "status": status_text,
            "message": message,
            "results": results,
            "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.table.resizeColumnsToContents()
        self.update_tooltips(row_index)  # обновим tooltip (cookies, params и т.д.)


    def _create_item(self, text):
        from PyQt5.QtWidgets import QTableWidgetItem
        return QTableWidgetItem(text)
