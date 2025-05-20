import os
import dns.resolver
import subprocess

def find_nameservers(domain, progress_callback=None):
    """Находит NS-записи для указанного домена."""
    try:
        result = dns.resolver.resolve(domain, 'NS')
        total = len(result)  # Общее количество серверов имен
        for i, ns in enumerate(result):
            ns_text = ns.to_text()
            if progress_callback:
                progress = int((i + 1) / total * 50)  # Прогресс: 0-50%
                progress_callback(progress)
            yield (ns_text, "green")
    except Exception as e:
        if progress_callback:
            progress_callback(0)  # Обнуление прогресса в случае ошибки
        yield (f"Ошибка при получении NS-записей: {e}", "red")

def perform_dns_zone_transfer(domain, nameservers, output_folder, progress_callback=None):
    """Выполняет передачу зоны и сохраняет логи в указанную папку."""
    base_log_path = "C:/Users/rusla/Desktop/Web_Scrapper/data/dns"
    os.makedirs(base_log_path, exist_ok=True)  # Создаем основную папку, если ее нет
    output_folder = os.path.join(base_log_path, output_folder)
    os.makedirs(output_folder, exist_ok=True)  # Создаем подкаталог для логов

    output_file = os.path.join(output_folder, f"{os.path.basename(output_folder)}.txt")
    try:
        with open(output_file, 'w') as f:
            total = len(nameservers)  # Общее количество серверов имен
            for i, ns in enumerate(nameservers):
                ns_name = ns[0] if isinstance(ns, tuple) else ns  # Извлекаем только имя, если это кортеж
                f.write(f"Проверка передачи зоны на сервере: {ns_name}\n")
                if progress_callback:
                    progress = 50 + int((i + 1) / total * 50)  # Прогресс: 50-100%
                    progress_callback(progress)
                yield (f"Проверка передачи зоны на сервере: {ns_name}", "blue")
                try:
                    result = subprocess.run(['dig', 'axfr', domain, f'@{ns_name}'], stdout=subprocess.PIPE, text=True)
                    if result.returncode == 0:
                        f.write(result.stdout)
                        yield (f"Передача зоны успешна для {ns_name}", "green")
                    else:
                        f.write(f"Передача зоны не удалась для {ns_name}.\n")
                        yield (f"Передача зоны не удалась для {ns_name}", "red")
                except subprocess.CalledProcessError as e:
                    f.write(f"Ошибка при выполнении передачи зоны для {ns_name}: {e}\n")
                    yield (f"Ошибка при выполнении передачи зоны для {ns_name}: {e}", "red")
    except Exception as e:
        yield (f"Ошибка записи результатов: {e}", "red")

def save_all_logs_to_file(logs, suffix=None):
    """Сохраняет все логи в файл save_all_results_<suffix>.txt в Log_Files."""
    base_log_path = "C:/Users/rusla/Desktop/Web_Scrapper/data/dns"
    os.makedirs(base_log_path, exist_ok=True)

    # Формируем имя файла
    suffix = f"_{suffix}" if suffix else ""
    output_file = os.path.join(base_log_path, f"save_all_results{suffix}.txt")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(logs) # Сохраняем переданный текст логов
        return f"Логи сохранены в {output_file}"
    except IOError as e:
        return f"Ошибка сохранения логов: {e}"

def get_a_records(domain):
    """Запрашивает A-записи (IPv4) для домена."""
    try:
        result = dns.resolver.resolve(domain, 'A')
        return [(record.to_text(), "green") for record in result]
    except Exception as e:
        return [(f"Ошибка при запросе A-записей: {e}", "red")]

def get_aaaa_records(domain):
    """Запрашивает AAAA-записи (IPv6) для домена."""
    try:
        result = dns.resolver.resolve(domain, 'AAAA')
        return [(record.to_text(), "green") for record in result]
    except Exception as e:
        return [(f"Ошибка при запросе AAAA-записей: {e}", "red")]

def get_mx_records(domain):
    """Запрашивает MX-записи (почтовые серверы) для домена."""
    try:
        result = dns.resolver.resolve(domain, 'MX')
        return [(record.exchange.to_text(), "green") for record in result]
    except Exception as e:
        return [(f"Ошибка при запросе MX-записей: {e}", "red")]

def get_txt_records(domain):
    """Запрашивает TXT-записи для домена."""
    try:
        result = dns.resolver.resolve(domain, 'TXT')
        return [(record.to_text(), "green") for record in result]
    except Exception as e:
        return [(f"Ошибка при запросе TXT-записей: {e}", "red")]

def get_cname_records(domain):
    """Запрашивает CNAME-записи для домена."""
    try:
        result = dns.resolver.resolve(domain, 'CNAME')
        return [(record.to_text(), "green") for record in result]
    except Exception as e:
        return [(f"Ошибка при запросе CNAME-записей: {e}", "red")]

def get_nameservers_and_length(domain):
    """Возвращает список серверов имен и их количество."""
    nameservers_generator = find_nameservers(domain)
    nameservers = [ns for ns, _ in nameservers_generator]  # Извлекаем только имена серверов
    return nameservers, len(nameservers)
