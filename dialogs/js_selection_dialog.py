from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from utils.js_analyzer import analyze_js_files

class JsSelectionDialog(QDialog):
    def __init__(self, domain: str, js_urls: list[str], base_url: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"JS Files for {domain}")
        self.resize(700, 500)

        self.js_urls = js_urls
        self.base_url = base_url

        layout = QVBoxLayout(self)

        # Список с чекбоксами
        self.list_widget = QListWidget()
        for url in js_urls:
            item = QListWidgetItem(url)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        # Кнопки выбора всех / очистки
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.unselect_all_btn = QPushButton("Unselect All")
        self.select_all_btn.clicked.connect(self.select_all)
        self.unselect_all_btn.clicked.connect(self.unselect_all)
        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.unselect_all_btn)
        layout.addLayout(btn_layout)

        # Кнопки анализа и закрытия
        self.button_box = QDialogButtonBox()
        self.analyze_button = self.button_box.addButton("Analyze", QDialogButtonBox.ActionRole)
        self.close_button = self.button_box.addButton(QDialogButtonBox.Close)
        self.retire_button = self.button_box.addButton("Analyze with Retire.js", QDialogButtonBox.ActionRole)
        self.retire_button.clicked.connect(self.run_retire_analysis)
        self.analyze_button.clicked.connect(self.run_analysis)
        self.close_button.clicked.connect(self.reject)
        layout.addWidget(self.button_box)

    def select_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)

    def unselect_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def run_analysis(self):
        selected_urls = [self.list_widget.item(i).text()
                         for i in range(self.list_widget.count())
                         if self.list_widget.item(i).checkState() == Qt.Checked]

        if not selected_urls:
            return

        results = analyze_js_files(selected_urls, self.base_url)
        lines = ["JS Analysis Results:\n"]
        for res in results:
            lines.append(f"{res['library']} {res['version']} → {res['url']}")

        from dialogs.page_parse_dialog import PageParseDialog
        dialog = PageParseDialog("JS Analysis", "\n".join(lines), self)
        dialog.exec_()

    def run_retire_analysis(self):
        from utils.js_downloader import download_js_file
        from utils.retire_wrapper import analyze_with_retirejs
        from dialogs.page_parse_dialog import PageParseDialog

        save_dir = "data/js_downloads"

        selected_urls = [self.list_widget.item(i).text()
                        for i in range(self.list_widget.count())
                        if self.list_widget.item(i).checkState() == Qt.Checked]
        if not selected_urls:
            return

        results = []
        for url in selected_urls:
            file_path = download_js_file(url, save_dir)
            if not file_path:
                results.append(f"[FAIL] {url} → download failed")
                continue

            res = analyze_with_retirejs(file_path)
            if "error" in res:
                results.append(f"[FAIL] {url} → {res['error']}")
                continue

            if not res.get("data"):
                results.append(f"[OK] {url} → No vulnerabilities found")
                continue

            for entry in res["data"]:
                lib = entry["results"][0]
                results.append(f"{entry['file']}")
                results.append(f"↳ {lib['component']} {lib['version']}")
                for vuln in lib["vulnerabilities"]:
                    cves = ", ".join(vuln.get("identifiers", {}).get("CVE", [])) or "-"
                    severity = vuln.get("severity", "-")
                    info = vuln.get("info", [])[0] if vuln.get("info") else "-"
                    results.append(f"  - {cves} | {severity}")
                    results.append(f"    ↪ {info}")
                results.append("")

        msg = "\n".join(results)
        dialog = PageParseDialog("Retire.js Results", msg, self)
        dialog.exec_()

