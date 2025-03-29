from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox

class BaseDialog(QDialog):
    def __init__(self, parent=None, title="Диалог"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.layout = QVBoxLayout(self)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def add_widget(self, widget):
        self.layout.insertWidget(self.layout.count() - 1, widget)
