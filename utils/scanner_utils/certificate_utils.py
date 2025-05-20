import json
import aiohttp, asyncio
import threading
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QTreeWidgetItem,QFileDialog
from PyQt5.QtGui import QColor
from utils.scanner_utils.async_worker import AsyncWorker

CRT_SH_SEARCH_URL = "https://crt.sh/?q=%.{domain}"
CRT_SH_CERT_URL = "https://crt.sh/?id={cert_id}"

stop_event = threading.Event()

###### PARSER FOR GETTING CERTIFICATES ID FROM DOMAIN/SUBDOMAIN CRT.SH  #############
###### PARSER FOR GETTING CERTIFICATES ID FROM DOMAIN/SUBDOMAIN CRT.SH  #############

async def fetch_certificate_ids(domain, log_callback=None):
    """Асинхронная функция для получения ID сертификатов."""
    try:
        if not isinstance(domain, str):
            raise ValueError("Ожидалась строка, но получен другой тип данных")

        domain = domain.split(" ")[0]  # Удаляем IP-адреса и оставляем только домен

        url = CRT_SH_SEARCH_URL.format(domain=domain)
        if log_callback:
            log_callback(f"URL для запроса сертификатов: {url}", "blue")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"Ошибка при запросе к crt.sh: {response.status}")

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Находим вторую таблицу, содержащую вложенную третью таблицу
                certificates_table = None
                tables = soup.find_all("table")
                if len(tables) >= 2:
                    certificates_table = tables[1].find("table")

                if not certificates_table:
                    if log_callback:
                        log_callback(f"Не удалось найти таблицу сертификатов для домена {domain}", "red")
                    return {}

                cert_ids = []
                rows = certificates_table.find_all("tr")
                if not rows or len(rows) <= 1:
                    if log_callback:
                        log_callback(f"Таблица сертификатов пуста или отсутствует для домена {domain}", "red")
                    return {}

                for row in rows[1:]:  # Пропускаем заголовок таблицы
                    cert_td = row.find("td", style="text-align:center")
                    if cert_td:
                        cert_link = cert_td.find("a")
                        if cert_link:
                            cert_ids.append(cert_link.text.strip())

                if log_callback:
                    log_callback(f"Найдено {len(cert_ids)} сертификатов для домена {domain}", "green")

                return {domain: cert_ids if cert_ids else []}

    except Exception as e:
        if log_callback:
            log_callback(f"Ошибка при получении сертификатов для домена {domain}: {e}", "red")
        return {}

##### PARSING CERTIFICATE FULL INFO FROM JSON FILE TO TREEWIDGET ###########
##### PARSING CERTIFICATE FULL INFO FROM JSON FILE TO TREEWIDGET ###########

async def fetch_certificate_details(cert_id, log_callback=None):
    """Асинхронная функция для получения деталей сертификата."""
    try:
        if not isinstance(cert_id, str):
            raise ValueError("Ожидалась строка, но получен другой тип данных")

        url = CRT_SH_CERT_URL.format(cert_id=cert_id)
        if log_callback:
            log_callback(f"URL для запроса деталей сертификата: {url}", "blue")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"Ошибка при запросе к сертификату: {response.status}")

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                cert_data = soup.find("td", class_="text")

                if not cert_data:
                    if log_callback:
                        log_callback(f"Не удалось найти данные для сертификата {cert_id}", "red")
                    return {}

                certificate_details = cert_data.text.strip()
                if log_callback:
                    log_callback(f"Данные для сертификата {cert_id} успешно получены.", "green")

                return {"id": cert_id, "details": certificate_details}

    except Exception as e:
        if log_callback:
            log_callback(f"Ошибка при получении данных для сертификата {cert_id}: {e}", "red")
        return None # Вместо return {}

###### FUNCTION RESPONSIBLE FOR ANALYZE CERTIFICATE ID #############
###### FUNCTION RESPONSIBLE FOR ANALYZE CERTIFICATE ID #############

async def analyze_certificates_via_crtsh_async(active_subdomains, log_callback=None, progress_callback=None):
    """Асинхронная функция для анализа сертификатов."""
    if not isinstance(active_subdomains, dict):
        raise ValueError("Ожидался словарь поддоменов, но получен другой тип данных")
    
    all_certificates = {}

    total_domains = sum(len(subdomains) for subdomains in active_subdomains.values())
    processed_domains = 0

    for domain, subdomains in active_subdomains.items():
        if not isinstance(subdomains, list):
            if log_callback:
                log_callback(f"Пропущен некорректный формат данных для домена {domain}", "orange")
            continue

        for subdomain in subdomains:
            if stop_event.is_set():
                if log_callback:
                    log_callback("Сканирование остановлено пользователем.", "orange")
                return all_certificates

            if not isinstance(subdomain, str):
                if log_callback:
                    log_callback(f"Пропущен некорректный поддомен: {subdomain}", "orange")
                continue

            subdomain = subdomain.split(" ")[0]  # Удаляем IP-адреса
            cert_ids = await fetch_certificate_ids(subdomain, log_callback=log_callback)
            if cert_ids:
                all_certificates[subdomain] = cert_ids.get(subdomain, [])
            # Обновление прогресса
            processed_domains += 1
            if progress_callback:
                progress = int((processed_domains / total_domains) * 100)
                progress_callback(progress)

    return all_certificates

###### START ASYNCRON SCAN IN SERTIFICATES #######
###### START ASYNCRON SCAN IN SERTIFICATES #######


def analyze_certificates_via_crtsh(active_subdomains, log_callback=None, progress_callback=None):
    """Запускает асинхронное сканирование сертификатов."""
    async def _analyze():
        return await analyze_certificates_via_crtsh_async(active_subdomains, log_callback, progress_callback)

    worker = AsyncWorker(_analyze())
    worker.finished.connect(lambda result: print(result))  # Обработка результата
    worker.error.connect(lambda e: print(f"Ошибка: {e}"))  # Обработка ошибок
    worker.start()


###### LOAD JSON CERTIFICATE FILE FROM pushButtonAllCert TO TREEWIDGETFILES #############
###### LOAD JSON CERTIFICATE FILE FROM pushButtonAllCert TO TREEWIDGETFILES #############

def load_certificate_file(file_path, log_callback=None):
    """Загружает файл сертификатов в формате JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("Файл должен содержать словарь данных")

            if log_callback:
                log_callback(f"Файл {file_path} успешно загружен. Тип данных: Dictionary", "green")

            return data

    except Exception as e:
        if log_callback:
            log_callback(f"Ошибка загрузки файла {file_path}: {e}", "red")
        raise
    

        
##### CHECK IF JSON FILE IS VALID TO SHOW IN TREEWIDGETDOMAIN #######
##### CHECK IF JSON FILE IS VALID TO SHOW IN TREEWIDGETDOMAIN #######
        
def load_and_validate_json(file_path):
    """Загружает и проверяет структуру JSON-файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Проверяем структуру JSON
        required_keys = ["active_subdomains", "inactive_subdomains", "domains"]
        if not isinstance(data.get("active_subdomains"), list) or \
        not isinstance(data.get("inactive_subdomains"), list) or \
        not isinstance(data.get("domains"), list):
            raise ValueError("Структура файла JSON неверная!")

        return data
    except Exception as e:
        raise ValueError(f"Ошибка при обработке JSON: {e}")
    
##### FILL TREEWIDGETDOMAIN WITH DATA FROM JSON #######
##### FILL TREEWIDGETDOMAIN WITH DATA FROM JSON #######

def populate_tree_with_json(data, tree_widget):
    """Заполняет TreeWidget данными из JSON."""
    tree_widget.clear()

    # Обрабатываем активные поддомены
    active_item = QTreeWidgetItem(tree_widget)
    active_item.setText(0, "Active Subdomains")
    active_item.setForeground(0, QColor("green"))

    for sub in data.get("active_subdomains", []):
        sub_item = QTreeWidgetItem(active_item)
        sub_item.setText(0, sub["subdomain"])
        sub_item.setForeground(0, QColor("purple"))

        ip_item = QTreeWidgetItem(sub_item)
        ip_item.setText(0, f"IP: {sub['ip']}")
        ip_item.setForeground(0, QColor("blue"))

        status_item = QTreeWidgetItem(sub_item)
        status_item.setText(0, f"Status Code: {sub['status_code']}")
        status_item.setForeground(0, QColor("darkblue"))

    # Обрабатываем неактивные поддомены
    inactive_item = QTreeWidgetItem(tree_widget)
    inactive_item.setText(0, "Inactive Subdomains")
    inactive_item.setForeground(0, QColor("red"))

    for sub in data.get("inactive_subdomains", []):
        sub_item = QTreeWidgetItem(inactive_item)
        sub_item.setText(0, sub)
        sub_item.setForeground(0, QColor("darkred"))

    # Обрабатываем домены
    domains_item = QTreeWidgetItem(tree_widget)
    domains_item.setText(0, "Domains")
    domains_item.setForeground(0, QColor("purple"))

    for domain in data.get("domains", []):
        domain_item = QTreeWidgetItem(domains_item)
        domain_item.setText(0, domain)
        
        
##### SAVING PARSED CERTIFICATES ID FROM DOMAIN/SUBDOMAIN FOR TREEWIDGETDOMAIN #######
##### SAVING PARSED CERTIFICATES ID FROM DOMAIN/SUBDOMAIN FOR TREEWIDGETDOMAIN #######

def save_certificates_to_treewidget_domain(data, log_callback=None):
    """
    Сохраняет сертификаты в JSON-файл в определённом формате:
    """
    try:
        # Открыть диалог для выбора файла сохранения
        file_path, _ = QFileDialog.getSaveFileName(
            None, "Сохранить сертификаты", "", "JSON Files (*.json)"
        )
        if not file_path:
            if log_callback:
                log_callback("Сохранение отменено пользователем.", "orange")
            return

        # Проверка формата данных
        if not isinstance(data, dict) or not all(isinstance(v, list) and all(isinstance(i, str) for i in v) for v in data.values()):
            raise ValueError("Некорректный формат данных. Ожидался словарь с доменами и списками ID сертификатов.")

        # Сохранение данных в файл
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        if log_callback:
            log_callback(f"Сертификаты успешно сохранены в файл: {file_path}", "green")
    except Exception as e:
        if log_callback:
            log_callback(f"Ошибка при сохранении сертификатов: {e}", "red")
        raise
    
    
###### SET UP COLOR FOR TREEWIDGET #############
###### SET UP COLOR FOR TREEWIDGET #############
   
def set_tree_item_color(item, color):
    """Изменяет цвет текста элемента QTreeWidget и всех его дочерних элементов."""
    item.setForeground(0, color)
    for i in range(item.childCount()):
        child = item.child(i)
        set_tree_item_color(child, color)
    if item is None:
        return
        
          
#### STOP SCAN #######
#### STOP SCAN #######

def stop_scanning():
    """Устанавливает флаг остановки сканирования."""
    stop_event.set()


#### CLEAR LOGS #######
#### CLEAR LOGS #######

def clear_logs(log_widget):
    """Очищает содержимое логов."""
    log_widget.clear()