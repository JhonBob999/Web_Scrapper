from PyQt5.QtWidgets import QLineEdit, QLabel, QTextEdit, QSpinBox, QMessageBox
from dialogs.base_dialog import BaseDialog
import json

def show_params_dialog(parent, existing_params=None):
    existing_params = existing_params or {}

    dialog = BaseDialog(parent, title="Настроить параметры запроса")

    # Proxy
    proxy_input = QLineEdit()
    proxy_input.setPlaceholderText("http://127.0.0.1:8080")
    proxy_input.setText(existing_params.get("proxy", ""))
    dialog.add_widget(QLabel("🔌 Proxy"))
    dialog.add_widget(proxy_input)

    # User-Agent
    ua_input = QLineEdit()
    ua_input.setPlaceholderText("Mozilla/5.0 ...")
    ua_input.setText(existing_params.get("user_agent", ""))
    dialog.add_widget(QLabel("🧠 User-Agent"))
    dialog.add_widget(ua_input)

    # Headers (JSON)
    headers_input = QTextEdit()
    headers_text = json.dumps(existing_params.get("headers", {}), indent=4, ensure_ascii=False)
    headers_input.setPlainText(headers_text)
    dialog.add_widget(QLabel("📦 Headers (в формате JSON)"))
    dialog.add_widget(headers_input)

    # Timeout
    timeout_input = QSpinBox()
    timeout_input.setRange(1, 60)
    timeout_input.setValue(existing_params.get("timeout", 10))
    dialog.add_widget(QLabel("⏱ Таймаут (сек)"))
    dialog.add_widget(timeout_input)

    def on_accept():
        try:
            headers = json.loads(headers_input.toPlainText())
        except Exception as e:
            QMessageBox.warning(dialog, "Ошибка JSON", f"Неверный формат Headers:\n{e}")
            return

        dialog.accepted_data = {
            "proxy": proxy_input.text().strip(),
            "user_agent": ua_input.text().strip(),
            "headers": headers,
            "timeout": timeout_input.value()
        }
        dialog.accept()

    dialog.buttons.accepted.disconnect()
    dialog.buttons.accepted.connect(on_accept)

    result = dialog.exec_()
    return dialog.accepted_data if result == dialog.Accepted else None
