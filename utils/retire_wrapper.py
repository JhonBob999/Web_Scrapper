import subprocess
import json
import os

def analyze_with_retirejs(file_path: str) -> dict:
    try:
        abs_path = os.path.abspath(file_path)
        print("[RETIRE] Checking file:", abs_path)
        print("[RETIRE] Exists:", os.path.exists(abs_path))

        cmd = f'npx retire "{abs_path}" --outputformat json'
        print("[RETIRE] CMD:", cmd)

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            shell=True,
            text=True
        )

        print("[RETIRE] Exit code:", result.returncode)
        print("[RETIRE] STDERR:", result.stderr)

        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}

