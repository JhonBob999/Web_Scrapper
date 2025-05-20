import requests
import socket
import os
import time
import random
import json
from bs4 import BeautifulSoup
from functools import lru_cache

def validate_inputs(domain, request_count, timeout, interval, output_folder):
    """Проверяет корректность входных данных."""
    if not domain or "." not in domain:
        raise ValueError("Некорректный домен.")
    if not isinstance(request_count, int) or request_count <= 0:
        raise ValueError("Количество запросов должно быть положительным числом.")
    if not isinstance(timeout, int) or timeout <= 0:
        raise ValueError("Таймаут должен быть положительным числом.")
    if not isinstance(interval, int) or interval < 0:
        raise ValueError("Интервал должен быть положительным числом.")
    if not output_folder.strip():
        raise ValueError("Имя папки для сохранения не может быть пустым.")


def clear_logs(plain_text_widget):
    """Очищает поле логов."""
    plain_text_widget.clear()


def generate_random_values(mode):
    """Генерирует случайные значения для настроек сканирования в зависимости от режима."""
    modes = {
        "sneaky": {
            "request_count": random.randint(3, 7),
            "timeout": random.randint(5, 8),
            "interval": random.randint(2, 5),
            "request_limit": random.randint(50, 100)
        },
        "moderate": {
            "request_count": random.randint(20, 50),
            "timeout": random.randint(3, 8),
            "interval": random.randint(2, 5),
            "request_limit": random.randint(100, 200)
        },
        "aggressive": {
            "request_count": random.randint(50, 100),
            "timeout": random.randint(1, 5),
            "interval": random.randint(1, 2),
            "request_limit": random.randint(100, 200)
        }
    }
    if mode not in modes:
        raise ValueError("Неизвестный режим сканирования.")
    return modes[mode]

#### SAVE DATA ABOUT DOMAINS AND SUBDOMAINS IN STRUCTURE FORMAT ####

def save_logs_to_file(structured_data, file_name, format_type):
    """Сохраняет данные о доменах и поддоменах в структурированном формате."""

    # Новый путь
    base_dir = os.path.join("data", "subdomains", file_name)
    os.makedirs(base_dir, exist_ok=True)

    file_path = os.path.join(base_dir, f"{file_name}.{format_type}")

    if format_type == "json":
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(structured_data, file, indent=4, ensure_ascii=False)

    return f"Логи сохранены в файл: {file_path}"



#### CHECK ACTIVE SUBDOMAIN AND RESPONSE STATUS ####
 
def resolve_subdomain(subdomain, timeout=5):
    """Проверяет активность поддомена и возвращает IP и HTTP/HTTPS-статус."""
    try:
        response = requests.get(f"https://{subdomain}", timeout=timeout)
        ip = socket.gethostbyname(subdomain)
        return ip, response.status_code
    except:
        try:
            response = requests.get(f"http://{subdomain}", timeout=timeout)
            ip = socket.gethostbyname(subdomain)
            return ip, response.status_code
        except:
            return None, None



#### FIND AND CHECK SUBDOMAINS AND SAVE RESULTS TXT FILE ####


def find_and_check_subdomains(domain, request_count, timeout, interval, show_requests, output_folder, progress_callback):
    """Ищет поддомены через crt.sh, проверяет их активность и сохраняет результаты."""
    base_path = os.path.join("/home/kali/Desktop/Python/Qt5_Designer/Log_Files", output_folder)
    os.makedirs(base_path, exist_ok=True)

    registered_path = os.path.join(base_path, f"REGISTERED_{output_folder}.txt")
    active_path = os.path.join(base_path, f"ACTIVE_{output_folder}.txt")

    registered_subdomains = set()
    active_subdomains = []

    try:
        with open(registered_path, 'w') as reg_file, open(active_path, 'w') as act_file:
            for i in range(request_count):
                progress_callback(int((i + 1) / request_count * 100))

                url = f'https://crt.sh/?q=%.{domain}'
                if show_requests:
                    yield (f"Запрос: GET {url}", "blue")

                try:
                    response = requests.get(url, timeout=timeout)
                    if response.status_code == 200:
                        # Парсинг HTML-ответа с помощью parse_common_names
                        common_names = parse_common_names(response.text)

                        for subdomain in common_names:
                            if subdomain not in registered_subdomains:
                                registered_subdomains.add(subdomain)
                                reg_file.write(f"{subdomain}\n")
                                yield (f"Найден поддомен: {subdomain}", "purple")

                                # Проверка активности поддомена
                                ip, status_code = resolve_subdomain(subdomain)
                                if ip and status_code and {"subdomain": subdomain, "ip": ip, "status_code": status_code} not in active_subdomains:
                                    active_subdomains.append({"subdomain": subdomain,
                                    "ip": ip,
                                    "status_code": status_code
                                    })
                                    act_file.write(f"{subdomain}\n")
                                    act_file.write(f"-{ip}\n")
                                    act_file.write(f"--status: {status_code}\n")
                                    yield (f"Активный поддомен: {subdomain} ({ip}, status: {status_code})", "green")
                                else:
                                    yield (f"Поддомен недоступен: {subdomain}", "red")

                except requests.RequestException as e:
                    yield (f"Ошибка при запросе: {e}", "red")

                time.sleep(interval)

            yield (f"Всего найдено зарегистрированных поддоменов: {len(registered_subdomains)}", "purple")
            yield (f"Всего найдено активных поддоменов: {len(active_subdomains)}", "green")

    except IOError as e:
        yield (f"Ошибка при сохранении результатов: {e}", "red")


#### STOP SCAN ####

def stop_scan(current_results, output_folder):
    """Сохраняет промежуточные результаты при остановке."""
    base_path = os.path.join("/home/kali/Desktop/Python/Qt5_Designer/Log_Files", output_folder)
    os.makedirs(base_path, exist_ok=True)

    registered_path = os.path.join(base_path, f"REGISTERED_{output_folder}_PARTIAL.txt")
    active_path = os.path.join(base_path, f"ACTIVE_{output_folder}_PARTIAL.txt")

    try:
        with open(registered_path, 'w') as reg_file:
            for subdomain in current_results.get("registered", []):
                reg_file.write(f"{subdomain}\n")

        with open(active_path, 'w') as act_file:
            for subdomain, ip in current_results.get("active_subdomains", []):
                act_file.write(f"{subdomain} ({ip})\n")

        return f"Промежуточные результаты сохранены в папке: {base_path}"
    except IOError as e:
        return f"Ошибка при сохранении промежуточных результатов: {e}"
    
#### LOAD JSON FILE AND ADD TO TREEWIDGET ####    
    
def load_json_to_tree(json_file_path):
    """Загружает JSON-файл и преобразует данные для отображения в QTreeWidget."""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("JSON файл должен содержать объект (dict) на верхнем уровне.")
    except Exception as e:
        raise ValueError(f"Ошибка загрузки JSON-файла: {e}")

    tree_data = parse_dict_to_tree(data)

    # Проверка, что tree_data корректен
    if not tree_data or not isinstance(tree_data, list):
        raise ValueError("Данные JSON не могут быть преобразованы в дерево.")

    return tree_data

#### REKURSIVE DATA TO TREEWIDGET ####

def parse_dict_to_tree(data_dict):
    """Рекурсивно преобразует данные в формат для QTreeWidget."""
    def process_subdomain(sub_value):
        """Обрабатывает поддомен и создаёт его структуру для Tree Widget."""
        return {
            "name": sub_value.get("subdomain", "Unknown"),
            "children": [
                {"name": f"IP: {sub_value.get('ip', 'N/A')}", "value": ""},
                {"name": f"Status: {str(sub_value.get('status_code', 'N/A'))}", "value": ""}
        ]
    }

    items = []
    for key, value in data_dict.items():
        # Обработка active_subdomains
        if key == "active_subdomains" and isinstance(value, list):
            active_item = {
                "name": key,
                "children": [process_subdomain(sub) for sub in value if isinstance(sub, dict)]
            }
            items.append(active_item)

        # Обработка других словарей
        elif isinstance(value, dict):
            items.append({"name": key, "children": parse_dict_to_tree(value)})
        # Обработка списков строк
        elif isinstance(value, list):
            children = [{"name": str(sub_value)} for sub_value in value]
            items.append({"name": key, "children": children})
        # Обработка строк и других значений
        else:
            items.append({"name": key, "value": str(value)})
    return items


#### FILTER AND STRUCTURE LOGS IN CATEGORY PLAIN TEXT EDIT ####

def filter_and_structure_logs(logs):
    """Фильтрует и структурирует логи в категории."""
    if isinstance(logs, str):
        logs = logs.splitlines()
    
    structured_data = {
        "active_subdomains": [],
        "inactive_subdomains": [],
        "domains": []
    }

    for log in logs:
        log = log.strip()

        if log.startswith("Активный поддомен:"):
            print(f"Обрабатываем строку:{log}")
            
            # Извлекаем часть после "Активный поддомен:"
            parts = log.split(": ", 1)[1]
            print(f"Log from PARTS1:{parts}")
            
            # Извлекаем поддомен
            subdomain = parts.split(" (", 1)[0]
            print(f"Subdomain: {subdomain}")
            
            # Извлекаем IP и статус
            details = parts.split(" (", 1)[1]
            ip, status_code = details.rsplit(", status: ", 1)
            ip = ip.strip(" ,")
            status_code = status_code.strip(" )")
            print(f"IP: {ip}, Status Code: {status_code}")
            
            structured_data["active_subdomains"].append({
                "subdomain": subdomain,
                "ip": ip,
                "status_code": int(status_code)
            })

        elif log.startswith("Поддомен недоступен:"):
            subdomains = log.split(": ")[1].split()
            structured_data["inactive_subdomains"].extend(subdomains)

        elif log.startswith("Найден поддомен:"):
            subdomains = log.split(": ")[1].split()
            structured_data["domains"].extend(subdomains)

    # Удаление дубликатов
    structured_data["active_subdomains"] = list({frozenset(sorted(item.items())): item for item in structured_data["active_subdomains"]}.values())
    structured_data["inactive_subdomains"] = list(set(structured_data["inactive_subdomains"]))
    structured_data["domains"] = list(set(structured_data["domains"]))

    return structured_data

######## PARSER Matching Identities #########

def parse_common_names(html):
    """Парсит поддомены из столбца Matching Identities."""
    soup = BeautifulSoup(html, 'html.parser')

    # Найти все таблицы
    tables = soup.find_all('table')

    # Проверить, существует ли третья таблица
    if len(tables) < 3:
        raise ValueError("Третья таблица не найдена в HTML")

    # Выбрать третью таблицу
    table = tables[2]  # Индекс начинается с 0

    # Найти строку с <th>Matching Identities</th>
    header_row = table.find('tr')
    headers = header_row.find_all('th')
    common_name_index = -1

    for idx, header in enumerate(headers):
        if header.get_text(strip=True) == "Matching Identities":
            common_name_index = idx
            break

    if common_name_index == -1:
        raise ValueError("Столбец 'Matching Identities' не найден в таблице")

    # Найти все строки с данными
    rows = table.find_all('tr')[1:]  # Пропустить заголовок таблицы
    common_names = []

    for row in rows:
        # Найти все ячейки (td)
        cells = [td for td in row.find_all('td') if not td.attrs]

        if len(cells) > 1:
            common_name_cell = cells[1]
            common_name = common_name_cell.get_text(separator=" ", strip=True)

            # Разделить по пробелам и фильтровать от *. и пустых
            split_names = [name.strip() for name in common_name.split() if name.strip()]
            for name in split_names:
                if not name.startswith("*.") and len(name) > 3:
                    common_names.append(name)

    return common_names
