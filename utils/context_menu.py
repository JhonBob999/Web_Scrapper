from PyQt5.QtWidgets import QMenu
from ui import table_utils

def show_context_menu(parent, table, position, lcd_callback, run_task_callback, add_task_callback):
    menu = QMenu()
    menu.addAction("Добавить пустую задачу", lambda: handle_add_empty(add_task_callback, lcd_callback))
    menu.addAction("Добавить шаблон", lambda: handle_add_template(add_task_callback, lcd_callback))
    menu.addSeparator()
    menu.addAction("Удалить строку", lambda: handle_delete(table, lcd_callback))
    menu.addAction("Запустить задачу", lambda: run_task_callback())
    menu.exec_(table.viewport().mapToGlobal(position))
    menu.addSeparator()
    menu.addAction("▶ Запустить выделенные", lambda: parent.run_selected_tasks_bulk())
    menu.addAction("🗑 Удалить выделенные", lambda: parent.delete_selected_tasks_bulk())
    menu.addAction("💾 Сохранить выделенные", lambda: parent.save_selected_results_bulk())

# EMPTY BLANK 

def handle_add_empty(add_task_callback, lcd_callback):
    add_task_callback("", "", "CSS", "Ожидает")
    lcd_callback()

# EXAMPLE BLANK

def handle_add_template(add_task_callback, lcd_callback):
    add_task_callback("https://example.com", "a", "CSS", "Ожидает")
    lcd_callback()

# DELETE ROW

def handle_delete(table, lcd_callback):
    table_utils.delete_selected_row(table)
    lcd_callback()

# RUN CHOOSEN ROW

def handle_run_stub(table, lcd_callback):
    row = table.currentRow()
    if row >= 0:
        table.setItem(row, 4, table_utils.QTableWidgetItem("⏳ Выполняется"))
    lcd_callback()
