from .base_dialog import BaseDialog
import json
from PyQt5.QtWidgets import (QLineEdit, QLabel, QTextEdit, QSpinBox, QMessageBox, QDialog)

class ParamsDialog(BaseDialog):
    def __init__(self, parent=None, existing_params=None):
        super().__init__(parent, title="Настроить параметры запроса")

        existing_params = existing_params or {}

        # Proxy
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:8080")
        self.proxy_input.setText(existing_params.get("proxy", ""))
        self.add_widget(QLabel("🔗 Proxy"))
        self.add_widget(self.proxy_input)

        # User-Agent
        self.ua_input = QLineEdit()
        self.ua_input.setPlaceholderText("Mozilla/5.0 ...")
        self.ua_input.setText(existing_params.get("user_agent", ""))
        self.add_widget(QLabel("🕶️ User-Agent"))
        self.add_widget(self.ua_input)

        # Headers
        self.headers_input = QTextEdit()
        headers_text = json.dumps(existing_params.get("headers", {}), indent=4, ensure_ascii=False)
        self.headers_input.setPlainText(headers_text)
        self.add_widget(QLabel("📦 Headers (в формате JSON)"))
        self.add_widget(self.headers_input)

        # Timeout
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(1, 60)
        self.timeout_input.setValue(existing_params.get("timeout", 10))
        self.add_widget(QLabel("⏱️ Таймаут (сек)"))
        self.add_widget(self.timeout_input)

    def accept(self):
        try:
            headers = json.loads(self.headers_input.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "Ошибка формата JSON", f"Проверьте JSON:\n{e}")
            return

        self.accepted_data = {
            "proxy": self.proxy_input.text().strip(),
            "user_agent": self.ua_input.text().strip(),
            "headers": headers,
            "timeout": self.timeout_input.value()
        }
        super().accept()

def show_params_dialog(parent, existing_params=None):
    dialog = ParamsDialog(parent, existing_params)
    if dialog.exec_() == QDialog.Accepted:
        return dialog.accepted_data
