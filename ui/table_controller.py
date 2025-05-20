# ui/table_controller.py

from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt
from ui.table_utils import colorize_row_by_status

class TableController:
    def __init__(self, table_widget, task_params):
        self.table = table_widget
        self.task_params = task_params

    def get_task_data(self, row: int) -> dict:
        """Возвращает данные строки таблицы как словарь"""
        get_text = lambda col: self.table.item(row, col).text().strip() if self.table.item(row, col) else ""

        return {
            "url": get_text(1),
            "selector": get_text(2),
            "method": get_text(3),
            "status": get_text(4),
            "params": self.task_params.get(row, {}),
            "last_run": get_text(10)
        }

    def update_row_status(self, row: int, status: str):
        """Обновляет статус и перекрашивает строку"""
        self.table.setItem(row, 4, QTableWidgetItem(status))
        colorize_row_by_status(self.table, row)

    def set_last_run(self, row: int, time_str: str):
        """Устанавливает значение в колонке Last Run"""
        self.table.setItem(row, 10, QTableWidgetItem(time_str))

    def apply_filters(self, filters: list):
        """
        Применяет список фильтров к таблице.
        Пример: [("URL", "cnn"), ("Status", "Ошибка")]
        """
        col_map = {
            "URL": 1,
            "Selector": 2,
            "Status": 4,
            "Last Run": 10
        }

        for row in range(self.table.rowCount()):
            match = True
            for field, value in filters:
                col = col_map.get(field)
                if col is None:
                    continue
                item = self.table.item(row, col)
                if not item or value.lower() not in item.text().lower():
                    match = False
                    break
            self.table.setRowHidden(row, not match)
