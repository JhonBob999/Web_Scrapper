from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCalendarWidget,
    QListWidget, QLabel, QPushButton, QMessageBox
)
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QTextCharFormat, QBrush, QColor
from datetime import datetime
from core.session_manager import list_sessions, load_session


class CalendarDialog(QDialog):
    def __init__(self, parent, task_results, load_session_callback):
        super().__init__(parent)
        self.setWindowTitle("📆 История по дате")
        self.resize(800, 500)

        self.task_results = task_results or {}
        self.load_session_callback = load_session_callback

        # Layouts
        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Calendar Widget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self.update_lists)
        left_layout.addWidget(self.calendar)

        # Tasks list
        self.tasks_label = QLabel("📋 Задачи на дату")
        self.task_list = QListWidget()
        right_layout.addWidget(self.tasks_label)
        right_layout.addWidget(self.task_list)

        # Sessions list
        self.sessions_label = QLabel("💾 Сессии на дату")
        self.session_list = QListWidget()
        self.session_list.itemDoubleClicked.connect(self.load_selected_session)
        right_layout.addWidget(self.sessions_label)
        right_layout.addWidget(self.session_list)

        # Show in Table Button
        self.show_button = QPushButton("🔍 Показать задачи в таблице")
        self.show_button.clicked.connect(self.emit_filtered_rows)
        right_layout.addWidget(self.show_button)

        # Close Button
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.close)
        right_layout.addWidget(self.close_btn)

        # Final Layout
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.highlight_dates()
        self.update_lists()

    def highlight_dates(self):
        format_task = QTextCharFormat()
        format_task.setBackground(QBrush(QColor("lightgreen")))

        format_session = QTextCharFormat()
        format_session.setBackground(QBrush(QColor("lightblue")))

        task_dates = set()
        for data in self.task_results.values():
            last_run = data.get("last_run", "")
            if last_run:
                try:
                    dt = datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S")
                    task_dates.add(dt.date())
                except:
                    continue

        session_dates = set()
        for session in list_sessions():
            dt_str = session.get("datetime", "")
            if dt_str:
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    session_dates.add(dt.date())
                except:
                    continue

        for date in task_dates:
            self.calendar.setDateTextFormat(QDate(date.year, date.month, date.day), format_task)

        for date in session_dates:
            if date in task_dates:
                continue  # чтобы не перекрывать
            self.calendar.setDateTextFormat(QDate(date.year, date.month, date.day), format_session)

    def update_lists(self):
        selected_date = self.calendar.selectedDate().toPyDate()
        self.selected_str = selected_date.strftime("%Y-%m-%d")

        # Filter task_results
        self.task_list.clear()
        self.filtered_rows = []
        for row, data in self.task_results.items():
            last_run = data.get("last_run", "")
            if last_run.startswith(self.selected_str):
                self.task_list.addItem(f"#{row+1} → {data.get('url')}")
                self.filtered_rows.append(row)

        # Filter sessions
        self.session_list.clear()
        for session in list_sessions():
            session_date = session.get("datetime", "").split(" ")[0]
            if session_date == self.selected_str:
                self.session_list.addItem(session.get("session_name"))

    def load_selected_session(self):
        item = self.session_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Ошибка", "Выберите сессию для загрузки")
            return

        session_name = item.text()
        path = f"sessions/{session_name}.json"
        session_data = load_session(path)
        self.load_session_callback(session_data)
        self.accept()

    def emit_filtered_rows(self):
        if hasattr(self.parent(), "apply_table_filters"):
            filters = [("Last Run", self.selected_str)]
            self.parent().apply_table_filters(filters)
        self.accept()