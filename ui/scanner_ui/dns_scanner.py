from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from ui.scanner_ui.dns_windows_ui import Ui_dnsWindows
from utils.scanner_utils.dns_utils import (
    find_nameservers, perform_dns_zone_transfer,
    get_a_records, get_aaaa_records, get_mx_records,
    get_txt_records, get_cname_records, save_all_logs_to_file
)
import os

class DnsScanWorker(QThread):
    log_signal = pyqtSignal(str, str)  # Первый аргумент - сообщение, второй - цвет
    progress_signal = pyqtSignal(int)  # Для обновления прогресса

    def __init__(self, domain, output_folder, scan_options):
        super().__init__()
        self.domain = domain
        self.output_folder = output_folder
        self.scan_options = scan_options  # {'ipv4': True, 'ipv6': True, 'mx': True, 'txt': True, 'cname': True}
        self.running = True

    def run(self):
        try:
            # Логи для NS-записей
            self.log_signal.emit("Поиск NS-записей...", "blue")
            nameservers_generator = find_nameservers(self.domain, progress_callback=self.update_progress)
            nameservers = [ns for ns, color in nameservers_generator]  # Извлекаем только имена серверов
            self.log_signal.emit(f"Найдено серверов имен: {len(nameservers)}", "green")

            # Попытка передачи зоны
            self.log_signal.emit("Попытка передачи зоны...", "blue")
            for record, color in perform_dns_zone_transfer(self.domain, nameservers, self.output_folder, progress_callback=self.update_progress):
                self.log_signal.emit(record, color)

            # Логи для IPv4
            if self.scan_options.get('ipv4'):
                self.log_signal.emit("Запрос A-записей (IPv4)...", "blue")
                for record, color in get_a_records(self.domain):
                    self.log_signal.emit(record, color)

            # Логи для IPv6
            if self.scan_options.get('ipv6'):
                self.log_signal.emit("Запрос AAAA-записей (IPv6)...", "blue")
                for record, color in get_aaaa_records(self.domain):
                    self.log_signal.emit(record, color)

            # Логи для MX
            if self.scan_options.get('mx'):
                self.log_signal.emit("Запрос MX-записей...", "blue")
                for record, color in get_mx_records(self.domain):
                    self.log_signal.emit(record, color)

            # Логи для TXT
            if self.scan_options.get('txt'):
                self.log_signal.emit("Запрос TXT-записей...", "blue")
                for record, color in get_txt_records(self.domain):
                    self.log_signal.emit(record, color)

            # Логи для CNAME
            if self.scan_options.get('cname'):
                self.log_signal.emit("Запрос CNAME-записей...", "blue")
                for record, color in get_cname_records(self.domain):
                    self.log_signal.emit(record, color)

            self.log_signal.emit("Сканирование завершено.", "green")
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {e}", "red")

    def stop(self):
        """Прерывает выполнение сканирования."""
        self.running = False

    def update_progress(self, progress):
        """Передает прогресс выполнения через сигнал."""
        self.progress_signal.emit(progress)

class DnsScanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_dnsWindows()
        self.ui.setupUi(self)
        self.worker = None

        # Подключение кнопок
        self.ui.pushButtonScan.clicked.connect(self.start_scan)
        self.ui.pushButtonStop.clicked.connect(self.stop_scan)
        self.ui.pushButtonLogs.clicked.connect(self.clear_logs)
        self.ui.pushButtonSave.clicked.connect(self.save_logs)

    def start_scan(self):
        # Получение данных от пользователя
        domain = self.ui.lineEditDomain.text().strip()
        output_folder = self.ui.lineEditOutput.text().strip()

        if not domain or not output_folder:
            QMessageBox.warning(self, "Ошибка", "Введите домен и имя папки для сохранения!")
            return

        self.ui.textBrowserLog.clear()
        self.ui.progressBarDns.setValue(0)

        # Чтение состояния чекбоксов
        scan_options = {
            'ipv4': self.ui.checkBoxIpv4.isChecked(),
            'ipv6': self.ui.checkBoxIpv6.isChecked(),
            'mx': self.ui.checkBoxMxEmail.isChecked(),
            'txt': self.ui.checkBoxTxt.isChecked(),
            'cname': self.ui.checkBoxCname.isChecked()
        }

        # Запуск рабочего потока
        self.worker = DnsScanWorker(domain, output_folder, scan_options)
        self.worker.log_signal.connect(self.update_logs)
        self.worker.progress_signal.connect(self.update_progress_bar)
        self.worker.start()

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        # Извлечение текста из textBrowserLog
        logs = self.ui.textBrowserLog.toPlainText()

        # Сохранение текста в файл
        output_folder = self.ui.lineEditOutput.text().strip()
        if not output_folder:
            QMessageBox.warning(self, "Ошибка", "Имя папки для сохранения логов не указано!")
            return

        base_log_path = "C:/Users/rusla/Desktop/Web_Scrapper/data/dns"
        os.makedirs(base_log_path, exist_ok=True)
        output_path = os.path.join(base_log_path, output_folder)
        os.makedirs(output_path, exist_ok=True)
        output_file = os.path.join(output_path, f"{output_folder}.txt")

        try:
            with open(output_file, 'w', encoding="utf-8") as file:
                file.write(logs)
            message = f"Логи сохранены в {output_file}"
        except IOError as e:
            message = f"Ошибка сохранения логов: {e}"

        # Обновление логов в интерфейсе
        self.update_logs(message, "orange")

    def save_logs(self):
        """Сохраняет всё содержимое textBrowserLog в save_all_results_<lineEditOutput>.txt."""
        logs = self.ui.textBrowserLog.toPlainText()
        suffix = self.ui.lineEditOutput.text().strip()
        message = save_all_logs_to_file(logs, suffix=suffix)
        self.update_logs(message, "orange")

    def clear_logs(self):
        self.ui.textBrowserLog.clear()

    def update_logs(self, message, color):
        """Обновление логов с использованием цвета."""
        formatted_message = f'<span style="color:{color};">{message}</span>'
        self.ui.textBrowserLog.append(formatted_message)

    def update_progress_bar(self, progress):
        """Обновление прогресс-бара."""
        self.ui.progressBarDns.setValue(progress)
