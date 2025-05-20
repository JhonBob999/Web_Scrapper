from PyQt5.QtWidgets import QLabel, QComboBox, QSpinBox, QPushButton, QHBoxLayout
from dialogs.base_dialog import BaseDialog

class TimerDialog(BaseDialog):
    def __init__(self, parent=None, current_seconds=None):
        super().__init__(parent, title="Настройка таймера")
        self.resize(350, 200)
        self.result_seconds = None

        # Готовые интервалы
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Выбрать готовый таймер", 0)
        self.preset_combo.addItem("1 минута", 60)
        self.preset_combo.addItem("5 минут", 300)
        self.preset_combo.addItem("30 минут", 1800)
        self.preset_combo.addItem("1 час", 3600)
        self.preset_combo.addItem("6 часов", 21600)
        self.add_widget(QLabel("Готовые интервалы"))
        self.add_widget(self.preset_combo)

        # Ручной ввод
        self.custom_spin = QSpinBox()
        self.custom_spin.setRange(1, 86400)
        self.custom_spin.setSuffix(" сек")
        self.custom_spin.setValue(int(current_seconds) if current_seconds else 60)
        self.add_widget(QLabel("Или введите вручную (в секундах):"))
        self.add_widget(self.custom_spin)

        # Кнопки действия
        btn_layout = QHBoxLayout()

        self.ok_btn = QPushButton("Установить")
        self.ok_btn.clicked.connect(self.accept_dialog)
        btn_layout.addWidget(self.ok_btn)

        self.clear_btn = QPushButton("Отключить")
        self.clear_btn.clicked.connect(self.clear_timer)
        btn_layout.addWidget(self.clear_btn)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.layout.insertLayout(self.layout.count() - 1, btn_layout)

        self.preset_combo.currentIndexChanged.connect(self.update_custom_value)

    def update_custom_value(self, index):
        seconds = self.preset_combo.itemData(index)
        if seconds:
            self.custom_spin.setValue(seconds)

    def accept_dialog(self):
        self.result_seconds = self.custom_spin.value()
        self.accept()

    def clear_timer(self):
        self.result_seconds = 0
        self.accept()
