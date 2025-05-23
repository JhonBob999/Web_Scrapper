import os
import subprocess
import json
from PyQt5.QtWidgets import QMessageBox
from dialogs.retire_results_dialog import RetireResultsDialog

def analyze_with_retire(file_path, parent=None):
    abs_path = os.path.abspath(file_path)
    print(f"[RETIRE] Checking file: {abs_path}")

    command = f'npx retire "{abs_path}" --outputformat json'
    print(f"[RETIRE] CMD: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )

        print(f"[RETIRE] Exit code: {result.returncode}")
        if result.stderr:
            print(f"[RETIRE] STDERR: {result.stderr.strip()}")

        if result.returncode == 13:
            try:
                data = json.loads(result.stdout)
                vulnerabilities = data.get("data", [])
                if vulnerabilities:
                    dialog = RetireResultsDialog(file_path, vulnerabilities, parent)
                    dialog.exec_()
                    return {"status": "ok", "vulnerabilities": vulnerabilities}
                else:
                    QMessageBox.information(parent, "No CVEs", "No CVEs found in output.")
                    return {"status": "no_cve"}
            except json.JSONDecodeError:
                QMessageBox.warning(parent, "JSON Error", "Could not parse Retire.js output.")
                return {"status": "error", "msg": "JSON decode error"}
        elif result.returncode == 0:
            QMessageBox.information(parent, "No Vulnerabilities", "No known vulnerabilities found.")
            return {"status": "no_vuln"}
        else:
            QMessageBox.critical(parent, "Retire.js Error", f"Unexpected exit code: {result.returncode}")
            return {"status": "error", "msg": f"Exit code: {result.returncode}"}

    except Exception as e:
        QMessageBox.critical(parent, "Execution Error", f"Failed to run Retire.js:\n{str(e)}")
        return {"status": "error", "msg": str(e)}



