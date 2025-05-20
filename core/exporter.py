import json
import pandas as pd

def save_to_json(parsed_data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)

def save_to_csv(parsed_data, file_path):
    rows = []
    for url, data in parsed_data.items():
        for item in data:
            if isinstance(item, dict):
                rows.append({
                    "URL": url,
                    "Title": item.get("title") or item.get("text"),
                    "Link": item.get("link"),
                    "Description": item.get("description", "")
                })
            elif isinstance(item, str):
                rows.append({
                    "URL": url,
                    "Title": item,
                    "Link": "",
                    "Description": ""
                })
    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False, encoding='utf-8-sig')

def save_to_excel(parsed_data, file_path):
    rows = []
    for url, data in parsed_data.items():
        for item in data:
            if isinstance(item, dict):
                rows.append({
                    "URL": url,
                    "Title": item.get("title") or item.get("text"),
                    "Link": item.get("link"),
                    "Description": item.get("description", "")
                })
            elif isinstance(item, str):
                rows.append({
                    "URL": url,
                    "Title": item,
                    "Link": "",
                    "Description": ""
                })
    df = pd.DataFrame(rows)
    df.to_excel(file_path, index=False, engine='openpyxl')

def save_flat_table(parsed_data, file_path, filetype="csv"):
    rows = []
    for row_id, task in parsed_data.items():
        row = {
            "Row": row_id,
            "URL": task.get("url", ""),
            "Status": task.get("status", ""),
            "Last Run": task.get("last_run", ""),
            "Message": task.get("message", "")
        }
        results = task.get("results", [])
        if isinstance(results, list) and results:
            preview = results[0] if isinstance(results[0], str) else json.dumps(results[0], ensure_ascii=False)
        else:
            preview = "No results"
        row["Results"] = preview
        rows.append(row)

    df = pd.DataFrame(rows)
    if filetype == "csv":
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
    elif filetype == "xlsx":
        df.to_excel(file_path, index=False, engine='openpyxl')

def export_results(parsed_data, file_path, is_flat=False):
    if is_flat:
        if file_path.endswith(".csv"):
            save_flat_table(parsed_data, file_path, filetype="csv")
        elif file_path.endswith(".xlsx"):
            save_flat_table(parsed_data, file_path, filetype="xlsx")
        else:
            raise ValueError("Flat export supports only CSV and XLSX formats")
    else:
        if file_path.endswith(".json"):
            save_to_json(parsed_data, file_path)
        elif file_path.endswith(".csv"):
            save_to_csv(parsed_data, file_path)
        elif file_path.endswith(".xlsx"):
            save_to_excel(parsed_data, file_path)
        else:
            raise ValueError("Unsupported file extension")
