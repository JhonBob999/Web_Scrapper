from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
from PyQt5.QtCore import QSettings, QPoint, QSize

class BaseDialog(QDialog):
    def __init__(self, parent=None, title="Dialog"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.layout = QVBoxLayout(self)

        # Создание кнопок ОК и Отмена
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        # Загрузка сохранённых настроек
        self.load_settings()

    def add_widget(self, widget):
        """Добавляет виджет перед кнопками."""
        self.layout.insertWidget(self.layout.count() - 1, widget)

    def accept(self):
        """Сохранение настроек и закрытие диалога при нажатии ОК."""
        self.save_settings()
        super().accept()

    def reject(self):
        """Сохранение настроек и закрытие диалога при нажатии Отмена."""
        self.save_settings()
        super().reject()

    def load_settings(self):
        """Загружает сохранённую позицию и размер окна."""
        settings = QSettings("YourCompany", "YourApp")
        pos = settings.value(f"{self.windowTitle()}_pos", QPoint(200, 200))
        size = settings.value(f"{self.windowTitle()}_size", QSize(400, 300))
        self.move(pos)
        self.resize(size)

    def save_settings(self):
        """Сохраняет текущую позицию и размер окна."""
        settings = QSettings("YourCompany", "YourApp")
        settings.setValue(f"{self.windowTitle()}_pos", self.pos())
        settings.setValue(f"{self.windowTitle()}_size", self.size())
