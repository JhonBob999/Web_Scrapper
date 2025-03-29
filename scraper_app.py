from PyQt5.QtWidgets import QMainWindow, QFileDialog, QPushButton, QMenu, QDialog
from PyQt5.QtCore import Qt, QTimer
# Core import
from core.exporter import save_to_csv, save_to_excel, export_data_to_json
from core import cookie_manager
from core.storage import load_settings, save_settings
from core.session_service import SessionController
# Date import
from datetime import datetime
# pyright: reportMissingImports=false
import sip

# Полный доступ к table_utils через namespace
from ui import table_utils
# Дополнительно — импорт часто используемых функций напрямую
from ui.table_utils import (
    update_lcd_counters,
    colorize_row_by_status,
    add_task_row as base_add_task_row,
    create_save_button
)
from ui.table_controller import TableController
from ui import editor_handlers
from ui.scraper_ui import Ui_MainWindow
# Utils import
from utils.context_menu import show_context_menu
# Dialog import
from dialogs.params_dialog import show_params_dialog
from dialogs.session_dialog import SessionHistoryDialog
from dialogs.search_dialog import SearchDialog
from dialogs.timer_dialog import TimerDialog
from dialogs.timer_dialog import TimerDialog
from dialogs.analytics_dialog import AnalyticsDialog
from dialogs.calendar_dialog import CalendarDialog


# USER SETTINGS FILE
USER_SETTINGS_FILE = "user_settings.json"


class ScraperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Calendar Widget
        self.ui.action_open_calendar.triggered.connect(self.open_calendar_dialog)

        # Column settings
        self.load_column_widths()

        # 📦 Инициализация ВСЕХ рабочих структур ДО добавления задач
        self.task_params = {}     # row -> request params
        self.task_intervals = {}  # row -> seconds
        self.task_timers = {}     # row -> QTimer
        self.task_results = {}    # row -> result list
        self.workers = []         # list of TaskWorker

        # ✅ Инициализация TaskManager
        from core.task_manager import TaskManager
        self.task_manager = TaskManager(
            table=self.ui.tasks_table,
            task_results=self.task_results,
            task_params=self.task_params,
            update_lcd_callback=self.update_lcd,
            update_tooltips_callback=self.update_tooltips,
            lock_row_callback=self.lock_row
        )
        
        # Table controller
        self.table_controller = TableController(
            table_widget=self.ui.tasks_table,
            task_params=self.task_params
        )
        
        # SessionControler
        self.session_controller = SessionController(
            table_controller=self.table_controller,
            add_task_callback=self.add_task_row,  # метод, который добавляет строку в таблицу
            task_params=self.task_params,
            task_results=self.task_results,
            task_intervals=self.task_intervals
        )
        
        # Search connection
        self.ui.action_search_tasks.triggered.connect(self.open_search_dialog)

        # Filters for search
        self.active_filters = []

        # Sessions
        self.ui.action_manage_sessions.triggered.connect(self.open_session_history)
        self.ui.action_save_session.triggered.connect(self.save_current_session)

        # 📌 Контекстное меню
        self.ui.tasks_table.setContextMenuPolicy(3)  # Qt.CustomContextMenu
        self.ui.tasks_table.customContextMenuRequested.connect(self.show_table_context_menu)

        # 📌 Двойной клик — редактирование
        self.ui.tasks_table.cellDoubleClicked.connect(self.edit_cell_handler)

        # 📌 Toolbar действия
        self.ui.action_add_task_2.triggered.connect(self.add_template_task)
        self.ui.action_del_task.triggered.connect(self.delete_task)
        self.ui.action_run_task.triggered.connect(self.run_task_stub)
        self.ui.action_run_selected_bulk.triggered.connect(self.run_selected_tasks_bulk)
        self.ui.action_delete_selected_bulk.triggered.connect(self.delete_selected_tasks_bulk)
        self.ui.action_save_selected_bulk.triggered.connect(self.save_selected_results_bulk)
        self.ui.action_run_analytics.triggered.connect(self.run_analytics_dialog)

        # 📌 Добавим одну задачу для примера (после инициализации task_params!)
        self.add_template_task()

        # Привязываем к действию кнопку запуска
        self.ui.action_run_task.triggered.connect(self.run_selected_task)

        # LCD Timer counter
        self.lcd_counters = {
            "total": self.ui.lcd_total,
            "running": self.ui.lcd_running,
            "success": self.ui.lcd_success,
            "error": self.ui.lcd_error,
            "stopped": self.ui.lcd_stopped
        }


    # ============================
    # 🔹 Действия
    # ============================

    def add_task_row(self, url, selector, method, status):
        row_position = self.ui.tasks_table.rowCount()

        # 🔹 Добавляем строку через table_logic
        base_add_task_row(self.ui.tasks_table, url, selector, method, status)

        # 🔹 Кнопка "Сохранить"
        save_button = create_save_button()
        save_button.clicked.connect(lambda _, r=row_position: self.save_task_result(r))
        self.ui.tasks_table.setCellWidget(row_position, 6, save_button)
        
        # COOKIE BUTTON IN TABLE
        cookie_button = QPushButton("🍪 Куки")
        cookie_button.clicked.connect(lambda _, r=row_position: self.load_cookie_file(r))
        self.ui.tasks_table.setCellWidget(row_position, 7, cookie_button)
        
        # 🔹 Вот сюда ДОБАВЬ ⬇️ пустую ячейку для Last Run
        self.ui.tasks_table.setItem(row_position, 10, self.create_item("")) 
        
        # Update Toolbar Tips
        self.update_tooltips(row_position)


    def add_template_task(self):
        self.add_task_row("https://example.com", "a", "CSS", "Ожидает")
        self.update_lcd()
    
    def delete_task(self):
        table_utils.delete_selected_row(self.ui.tasks_table)
        self.update_lcd()

    def run_task_stub(self):
        row = self.ui.tasks_table.currentRow()
        if row >= 0:
            self.table_controller.update_row_status(row, "⏳ Выполняется")
        self.update_lcd()

    # ============================
    # 🔹 Контекстное меню
    # ============================

    def show_table_context_menu(self, position):
        index = self.ui.tasks_table.indexAt(position)
        row = index.row()
        column = index.column()

        if row < 0:
            return

        # 💡 Если кликнули по колонке Timer
        if column == 9:
            menu = QMenu()

            menu.addAction("🔁 Переустановить таймер", lambda: self.edit_timer_for_row(row))
            menu.addAction("⏹ Отключить таймер", lambda: self.configure_task_timer(row, 0))

            menu.exec_(self.ui.tasks_table.viewport().mapToGlobal(position))
            return

        # 🔁 Иначе — обычное меню
        show_context_menu(
            self,
            self.ui.tasks_table,
            position,
            lambda: update_lcd_counters(self.ui.tasks_table, self.lcd_counters),
            self.run_selected_task,
            self.add_task_row
        )

    # ============================
    # 🔹 Редактирование ячеек
    # ============================

    def edit_cell_handler(self, row, column):
        if column == 9:  # Таймер
            self.configure_timer_dialog(row)
            return

        if column == 8:  # Params
            self.edit_params_modal(row)

        editor_handlers.edit_cell(
            parent=self,
            table=self.ui.tasks_table,
            row=row,
            column=column
        )
        
    def edit_params_modal(self, row):
        old_params = self.task_params.get(row, {})
        result = show_params_dialog(self, old_params)
        
        if result:
            self.task_params[row] = result
            self.ui.tasks_table.setItem(row, 8, self.create_item("✅ Настроено"))
            self.statusBar().showMessage(f"🛠 Параметры обновлены для строки #{row + 1}")
            self.update_tooltips(row)  # ⬅️ Обновляем подсказку
        else:
            self.statusBar().showMessage("❌ Параметры не были изменены")


    # ============================
    # 🔹 LCD обновление
    # ============================

    def update_lcd(self):
        table_utils.update_lcd_counters(
            self.ui.tasks_table,
            {
                'total': self.ui.lcd_total,
                'running': self.ui.lcd_running,
                'success': self.ui.lcd_success,
                'error': self.ui.lcd_error,
                'stopped': self.ui.lcd_stopped,
            }
        )
        
    def run_selected_task(self):
        row = self.ui.tasks_table.currentRow()
        if row < 0:
            self.statusBar().showMessage("⚠ Выберите задачу для запуска")
            return
        self.task_manager.run_task(row)

    def on_task_finished(self, row_index, status_text, message, results, cookies):
        
        self.ui.tasks_table.setItem(row_index, 4, self.create_item(status_text))
        colorize_row_by_status(self.ui.tasks_table, row_index)
        self.lock_row(row_index, False)  # 🔓 Разблокировать строку
        task = self.table_controller.get_task_data(row_index)
        url = task["url"]
        cookie_manager.save_cookies(url, cookies)
        self.statusBar().showMessage(f"Задача #{row_index + 1} завершена: {message}")
        self.update_lcd()

        task = self.table_controller.get_task_data(row_index)
        url = task["url"]

        self.task_results[row_index] = {
            "url": url,
            "status": status_text,
            "message": message,
            "results": results,
            "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.ui.tasks_table.resizeColumnsToContents()

    def create_item(self, text):
        from PyQt5.QtWidgets import QTableWidgetItem
        return QTableWidgetItem(text)


    def save_task_result(self, row_index):
        task = self.task_results.get(row_index)
        if not task or not task.get("results"):
            self.statusBar().showMessage("⚠ Нет данных для сохранения")
            return

        url = task["url"]
        results = task["results"]

        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить результат", "", 
                                                "JSON (*.json);;CSV (*.csv);;Excel (*.xlsx)")

        if not file_path:
            return

        if file_path.endswith(".csv"):
            save_to_csv({url: results}, file_path)
        elif file_path.endswith(".xlsx"):
            save_to_excel({url: results}, file_path)
        else:
            data = export_data_to_json({url: results}, format_type="default")
            with open(file_path, "w", encoding="utf-8") as f:
                import json
                json.dump(data, f, indent=4, ensure_ascii=False)

        self.statusBar().showMessage(f"✅ Сохранено: {file_path}")
        
        
    def lock_row(self, row_index, lock=True):
        """Блокирует или разблокирует редактирование ячеек строки."""
        for col in range(1, 4):  # URL, Selector, Method — колонки 1, 2, 3
            item = self.ui.tasks_table.item(row_index, col)
            if item:
                flags = item.flags()
                if lock:
                    item.setFlags(flags & ~Qt.ItemIsEditable)
                else:
                    item.setFlags(flags | Qt.ItemIsEditable)
                    
    
    def load_cookie_file(self, row_index):
        task = self.table_controller.get_task_data(row_index)
        url = task["url"]
        if cookie_manager.cookie_exists(url):
            path = cookie_manager.get_cookie_path(url)
            self.statusBar().showMessage(f"🍪 Куки загружены: {path}")
        else:
            self.statusBar().showMessage(f"⚠ Куки для задачи #{row_index + 1} не найдены")
         
         
    # SESSION SECTION
    # SESSION SECTION   
            
    def open_session_history(self):
        def load_callback(session_data):
            self.restore_session(session_data)

        dialog = SessionHistoryDialog(self, load_callback=load_callback)
        dialog.exec_()
        
    # RESTORE SESSION 
    # RESTORE SESSION
        
    def restore_session(self, session_data):
        self.session_controller.restore_session(session_data)
        self.statusBar().showMessage("Сессия восстановлена успешно")
   
    # SAVE SESSION
    # SAVE SESSION
        
    def save_current_session(self):
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Сохранение сессии", "Введите имя сессии:")
        if ok and name:
            path = self.session_controller.save_session(name)
            self.statusBar().showMessage(f"Сессия сохранена: {path}")
            
    # SEARCH BLOCK SECTION
    
    def open_search_dialog(self):
        def handle_filters(filters):
            self.active_filters = filters  # Сохраняем текущие
            self.table_controller.apply_filters(filters)

        dialog = SearchDialog(self, search_callback=handle_filters, initial_filters=self.active_filters)
        dialog.exec_()

        
        
    # SEARCH TABLE FILTER 

    def apply_table_filters(self, filters):
        """
        Поддержка:
        - ИЛИ для одного поля (URL, Selector, Status)
        - И между разными полями
        - Точная проверка селекторов (разделённые запятыми)
        """
        from collections import defaultdict

        grouped = defaultdict(list)
        for field, value in filters:
            grouped[field].append(value.lower())

        field_to_column = {"URL": 1, "Selector": 2, "Status": 4, "Last Run": 10}

        for row in range(self.ui.tasks_table.rowCount()):
            match = True

            for field, values in grouped.items():
                col_index = field_to_column.get(field)
                if col_index is None:
                    continue

                item = self.ui.tasks_table.item(row, col_index)
                cell_text = item.text().lower() if item else ""

                if field == "Selector":
                    selectors = [s.strip() for s in cell_text.split(",")]
                    if not any(v in selectors for v in values):
                        match = False
                        break
                else:
                    if not any(v in cell_text for v in values):
                        match = False
                        break

            self.ui.tasks_table.setRowHidden(row, not match)
            
            
    # TIMER SETTINGS BLOCK
    
    def configure_timer_dialog(self, row):
        current = self.task_intervals.get(row, 0)
        dialog = TimerDialog(self, current_seconds=current)
        if dialog.exec_():
            seconds = dialog.result_seconds or 0
            self.task_intervals[row] = seconds
            label = "Отключено" if seconds == 0 else f"⏱ {seconds // 60} мин"
            self.ui.tasks_table.setItem(row, 9, self.create_item(label))
            self.configure_task_timer(row, seconds)
            
    # TIMER CONFIGURE

    def configure_task_timer(self, row, seconds):
        # ⛔ Безопасно останавливаем старый таймер
        old_timer = self.task_timers.get(row)
        if old_timer and not sip.isdeleted(old_timer):
            old_timer.stop()
            old_timer.deleteLater()

        # Обновляем интервал
        self.task_intervals[row] = seconds

        # Обновляем отображение в колонке
        label = "Отключено" if seconds == 0 else f"⏱ {seconds // 60} мин"
        self.ui.tasks_table.setItem(row, 9, self.create_item(label))

        # Если задан новый интервал — создаём таймер
        if seconds > 0:
            timer = QTimer(self)
            timer.timeout.connect(lambda r=row: self.run_scheduled_task(r))
            timer.start(seconds * 1000)
            self.task_timers[row] = timer

        self.update_tooltips(row)

    
    # START TIMER
    
    def run_scheduled_task(self, row):
        self.ui.tasks_table.selectRow(row)

        # 🕓 Устанавливаем время последнего запуска
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.table_controller.set_last_run(row, timestamp)
        self.run_selected_task()
        
    # EDIT TIMER METHOD
    
    def edit_timer_for_row(self, row):
        current_seconds = self.task_intervals.get(row, 0)
        dialog = TimerDialog(self, current_seconds=current_seconds)

        if dialog.exec_() == QDialog.Accepted:
            seconds = dialog.result_seconds
            self.configure_task_timer(row, seconds)
            self.update_tooltips(row)

        
    # TOOLBAR TIPS EXPLANATION
    
    def update_tooltips(self, row):
        url_item = self.ui.tasks_table.item(row, 1)
        params_item = self.ui.tasks_table.item(row, 8)
        timer_item = self.ui.tasks_table.item(row, 9)

        if url_item:
            from core.cookie_manager import get_cookie_path
            url = url_item.text()
            tooltip = get_cookie_path(url)
            url_item.setToolTip(f"🍪 Cookies path: {tooltip}")

        if params_item:
            params = self.task_params.get(row, {})
            if not params:
                params_item.setToolTip("❌ No params set")
            else:
                desc = []
                if params.get("proxy"):
                    desc.append(f"Proxy: {params['proxy']}")
                if params.get("user_agent"):
                    desc.append(f"UA: {params['user_agent'][:40]}...")
                if params.get("timeout"):
                    desc.append(f"Timeout: {params['timeout']}s")
                if params.get("headers"):
                    desc.append(f"Headers: {len(params['headers'])} items")
                params_item.setToolTip(" | ".join(desc))

        if timer_item:
            seconds = self.task_intervals.get(row, 0)
            if seconds:
                timer_item.setToolTip(f"⏱ Task will auto-run in ~{seconds} sec")
            else:
                timer_item.setToolTip("⏹ Timer disabled")
                
    # SELECTED ROWS WITH CTRL/SHIFT
    # SELECTED ROWS WITH CTRL/SHIFT
    
    def get_selected_rows(self):
        return list(set(index.row() for index in self.ui.tasks_table.selectedIndexes()))
    
    def run_selected_tasks_bulk(self):
        rows = self.get_selected_rows()
        for row in rows:
            self.ui.tasks_table.selectRow(row)  # для совместимости с текущим методом
            self.run_selected_task()
            

    def delete_selected_tasks_bulk(self):
        rows = sorted(self.get_selected_rows(), reverse=True)
        for row in rows:
            self.ui.tasks_table.removeRow(row)
        self.update_lcd()
        
        
    def save_selected_results_bulk(self):
        rows = self.get_selected_rows()
        for row in rows:
            self.save_task_result(row)
            
    # SAVE COLUMN WIDTH
            
    def save_column_widths(self):
        settings = load_settings()
        widths = {}

        for col in range(self.ui.tasks_table.columnCount()):
            widths[str(col)] = self.ui.tasks_table.columnWidth(col)

        settings["column_widths"] = widths
        save_settings(settings)
            
    # LOAD SAVE COLUMN WIDTH

    def load_column_widths(self):
        settings = load_settings()
        widths = settings.get("column_widths", {})

        for col_str, width in widths.items():
            col = int(col_str)
            if 0 <= col < self.ui.tasks_table.columnCount():
                self.ui.tasks_table.setColumnWidth(col, width)

            
    # WHEN CLOSE APP SAVE COLUMN WIDTH
    
    def closeEvent(self, event):
        self.save_column_widths()
        event.accept()
        
    # ANALYTICS QDIALOG
    
    def run_analytics_dialog(self):
        rows = self.get_selected_rows()
        if not rows:
            self.statusBar().showMessage("⚠ Выберите задачи для анализа")
            return

        dialog = AnalyticsDialog(self, rows=rows, task_results=self.task_results)
        dialog.exec_()


    def open_calendar_dialog(self):
        dialog = CalendarDialog(self, self.task_results, self.restore_session)
        dialog.exec_()