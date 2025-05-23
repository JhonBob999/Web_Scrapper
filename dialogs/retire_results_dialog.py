from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
import json
import os
import webbrowser
from datetime import datetime

class RetireResultsDialog(QDialog):
    def __init__(self, file_path, vulnerabilities, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Retire.js Report")
        self.resize(800, 500)

        self.file_path = file_path
        self.vulnerabilities = vulnerabilities

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Analyzed File: {file_path}"))

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Library", "Version", "CVE", "Severity", "Info URL"])
        self.table.setColumnWidth(4, 300)
        layout.addWidget(self.table)

        self.populate_table()

        self.save_button = QPushButton("Save Report")
        self.save_button.clicked.connect(self.save_report)
        layout.addWidget(self.save_button)

    def populate_table(self):
        rows = []

        for file_entry in self.vulnerabilities:
            for result in file_entry.get("results", []):
                component = result.get("component", "")
                version = result.get("version", "")
                for vuln in result.get("vulnerabilities", []):
                    cve_list = vuln.get("identifiers", {}).get("CVE", ["N/A"])
                    cve = cve_list[0] if isinstance(cve_list, list) else str(cve_list)
                    severity = vuln.get("severity", "Unknown")
                    info_urls = vuln.get("info", [])
                    url = info_urls[0] if info_urls else ""
                    rows.append((component, version, cve, severity, url))

        self.table.setRowCount(len(rows))
        for row_idx, (lib, ver, cve, sev, url) in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(lib))
            self.table.setItem(row_idx, 1, QTableWidgetItem(ver))
            self.table.setItem(row_idx, 2, QTableWidgetItem(cve))
            self.table.setItem(row_idx, 3, QTableWidgetItem(sev))
            self.table.setItem(row_idx, 4, QTableWidgetItem(url))

    def save_report(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.basename(self.file_path).replace(".", "_")
        default_name = f"retire_report_{base_name}_{timestamp}"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            default_name,
            "JSON Report (*.json);;HTML Report (*.html)"
        )

        if path.endswith(".json"):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.vulnerabilities, f, indent=2)
            QMessageBox.information(self, "Saved", f"JSON saved to:\n{path}")

        elif path.endswith(".html"):
            html = self.generate_html_report()
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            QMessageBox.information(self, "Saved", f"HTML saved to:\n{path}")
            webbrowser.open(f"file:///{path}")

    def generate_html_report(self):
        html = "<html><head><meta charset='UTF-8'><title>Retire.js Report</title></head><body>"
        html += f"<h2>Retire.js Analysis Result</h2><p><b>File:</b> {self.file_path}</p><table border='1' cellpadding='4' cellspacing='0'>"
        html += "<tr><th>Library</th><th>Version</th><th>CVE</th><th>Severity</th><th>Info URL</th></tr>"

        for file_entry in self.vulnerabilities:
            for result in file_entry.get("results", []):
                component = result.get("component", "")
                version = result.get("version", "")
                for vuln in result.get("vulnerabilities", []):
                    cve_list = vuln.get("identifiers", {}).get("CVE", ["N/A"])
                    cve = cve_list[0] if isinstance(cve_list, list) else str(cve_list)
                    severity = vuln.get("severity", "Unknown")
                    info_urls = vuln.get("info", [])
                    url = info_urls[0] if info_urls else ""
                    html += f"<tr><td>{component}</td><td>{version}</td><td>{cve}</td><td>{severity}</td><td><a href='{url}'>{url}</a></td></tr>"

        html += "</table></body></html>"
        return html

