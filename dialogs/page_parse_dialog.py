from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox

class PageParseDialog(QDialog):
    def __init__(self, domain: str, parsed_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Parsed Content from {domain}")
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(parsed_text)

        layout.addWidget(self.text_edit)

        # Кнопка закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
