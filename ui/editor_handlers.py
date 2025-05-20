from PyQt5.QtWidgets import QLineEdit, QComboBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QTableWidgetItem

def edit_cell(parent, table, row, column):
    if column == 1:
        edit_url_cell(parent, table, row, column)
    elif column == 2:
        edit_selector_modal(parent, table, row, column)
    elif column == 3:
        edit_method_cell(parent, table, row, column)

def edit_url_cell(parent, table, row, column):
    item = table.item(row, column)
    if not item:
        return
    editor = QLineEdit(parent)
    editor.setText(item.text())
    table.setCellWidget(row, column, editor)
    editor.editingFinished.connect(lambda: finish_edit_url(table, row, column, editor))
    editor.setFocus()

def finish_edit_url(table, row, column, editor):
    new_value = editor.text()
    table.setItem(row, column, QTableWidgetItem(new_value))
    table.setCellWidget(row, column, None)

def edit_method_cell(parent, table, row, column):
    combo = QComboBox(parent)
    combo.addItems(["CSS", "XPath"])
    current = table.item(row, column)
    if current:
        index = combo.findText(current.text())
        if index >= 0:
            combo.setCurrentIndex(index)
    combo.currentIndexChanged.connect(lambda: finish_edit_method(table, row, column, combo))
    table.setCellWidget(row, column, combo)

def finish_edit_method(table, row, column, combo):
    value = combo.currentText()
    table.setItem(row, column, QTableWidgetItem(value))
    table.setCellWidget(row, column, None)

def edit_selector_modal(parent, table, row, column):
    current = table.item(row, column)
    text = current.text() if current else ""

    dialog = QDialog(parent)
    dialog.setWindowTitle("Редактировать селектор")
    layout = QVBoxLayout(dialog)

    editor = QTextEdit()
    editor.setPlainText(text)
    layout.addWidget(editor)

    button = QPushButton("Сохранить")
    layout.addWidget(button)
    button.clicked.connect(dialog.accept)

    if dialog.exec_():
        new_value = editor.toPlainText().strip()
        table.setItem(row, column, QTableWidgetItem(new_value))
