from PyQt5.QtWidgets import (
    QComboBox, QLineEdit, QPushButton, QLabel, QWidget,
    QMessageBox, QHBoxLayout, QVBoxLayout
)
from dialogs.base_dialog import BaseDialog

class SearchDialog(BaseDialog):
    def __init__(self, parent=None, search_callback=None, initial_filters=None):
        super().__init__(parent, title="Поиск задач")
        self.resize(500, 400)
        self.search_callback = search_callback
        self.filter_blocks = []

        # Контейнер для фильтров
        self.filters_container = QVBoxLayout()
        self.layout.insertLayout(self.layout.count() - 1, self.filters_container)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        self.add_filter_btn = QPushButton("➕ Добавить фильтр")
        self.add_filter_btn.clicked.connect(self.add_filter_block)
        btn_layout.addWidget(self.add_filter_btn)

        self.search_btn = QPushButton("🔍 Найти")
        self.search_btn.clicked.connect(self.apply_search)
        btn_layout.addWidget(self.search_btn)

        self.reset_btn = QPushButton("♻ Сбросить")
        self.reset_btn.clicked.connect(self.reset_search)
        btn_layout.addWidget(self.reset_btn)

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)

        self.layout.insertLayout(self.layout.count() - 1, btn_layout)

        if initial_filters:
            self.set_filters(initial_filters)
        else:
            self.add_filter_block()

    def add_filter_block(self, field_text="URL", value_text=""):
        block = QWidget()
        layout = QHBoxLayout(block)

        field_combo = QComboBox()
        field_combo.addItems(["URL", "Selector", "Status"])
        field_combo.setCurrentText(str(field_text))
        layout.addWidget(field_combo)

        value_input = QLineEdit()
        value_input.setPlaceholderText("Введите значение для поиска")
        value_input.setText(str(value_text))
        layout.addWidget(value_input)

        remove_btn = QPushButton("❌")
        remove_btn.setFixedWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_filter_block(block))
        layout.addWidget(remove_btn)

        self.filters_container.addWidget(block)
        self.filter_blocks.append((field_combo, value_input, block))

    def remove_filter_block(self, block):
        for field_combo, value_input, b in self.filter_blocks:
            if b == block:
                self.filters_container.removeWidget(b)
                b.setParent(None)
                self.filter_blocks.remove((field_combo, value_input, b))
                break

    def apply_search(self):
        filters = []
        for field_combo, value_input, _ in self.filter_blocks:
            field = field_combo.currentText()
            value = value_input.text().strip()
            if value:
                filters.append((field, value))

        if not filters:
            QMessageBox.warning(self, "Нет условий", "Добавьте хотя бы один фильтр с непустым значением.")
            return

        if self.search_callback:
            self.search_callback(filters)
        self.accept()

    def reset_search(self):
        if self.search_callback:
            self.search_callback([])
        self.accept()

    def set_filters(self, filters):
        for _, _, block in self.filter_blocks:
            self.filters_container.removeWidget(block)
            block.setParent(None)
        self.filter_blocks.clear()

        for field, value in filters:
            if not isinstance(field, str) or not isinstance(value, str):
                continue
            self.add_filter_block(field_text=field, value_text=value)
