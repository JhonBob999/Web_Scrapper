from PyQt5.QtWidgets import QMainWindow, QMessageBox, QFileDialog, QTreeWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
from ui.scanner_ui.certificate_window_ui import Ui_certificateWindows
from utils.scanner_utils.certificate_utils import (
    load_certificate_file, clear_logs, stop_scanning,
    fetch_certificate_details, set_tree_item_color,
    load_and_validate_json, populate_tree_with_json,
    fetch_certificate_ids, save_certificates_to_treewidget_domain
)
from utils.scanner_utils.async_worker import AsyncWorker
from ui.scanner_ui.Json_convertor_scanner import JsonConvertor
import json
import os

class CertificateScanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_certificateWindows()
        self.ui.setupUi(self)

        self.certificates = {}
        
        self.worker = None  # Инициализируем атрибут worker

        # Подключение кнопок
        self.ui.pushButtonScanStop.clicked.connect(self.stop_scan)  # Остановка анализа
        self.ui.pushButtonCleanLogs.clicked.connect(self.clear_logs_action)  # Подключаем кнопку Clear logs
        #TREEWIDGETFILES ACTIONS
        self.ui.pushButtonAllCert.clicked.connect(self.load_json_to_tree)  # Кнопка загрузки JSON в TreeWidget
        self.ui.treeWidgetFiles.itemDoubleClicked.connect(self.handle_tree_item_double_click)  # Обработка двойного клика
        #TREEWIDGETDOMAIN ACTIONS
        self.tree_widget_domain = self.ui.treeWidgetDomain  # Подключаем treeWidgetDomain
        self.ui.treeWidgetDomain.itemDoubleClicked.connect(self.handle_domain_item_double_click) # Double click in TreeWidgetDomain to get from domain/subdomain Certificate id 
        self.ui.pushButtonTreeDomain.clicked.connect(self.load_and_display_json) # LOAD JSON TO TREEWIDGETDOMAIN
        #JSON CONVERTOR ACTIONS
        self.ui.actionConvert_json.triggered.connect(self.open_json_convertor) # Open Json convertor window

        
    #### OPEN JSON CONVERTOR    
    def open_json_convertor(self):
        self.convertor_window = JsonConvertor()
        self.convertor_window.show()

###### LOADING JSON CERTIFICATE ID FILE IN TREEWIDGET pushButtonAllCert #############
###### LOADING JSON CERTIFICATE ID FILE IN TREEWIDGET pushButtonAllCert #############

    def load_json_to_tree(self):
        """Загружает JSON-файл в TreeWidget."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите JSON файл", "", "JSON Files (*.json)")
        if not file_path:
            return

        try:
            data = load_certificate_file(file_path)

            self.ui.treeWidgetFiles.clear()  # Очищаем дерево перед загрузкой новых данных

            for domain, cert_ids in data.items():
                domain_item = QTreeWidgetItem(self.ui.treeWidgetFiles)
                domain_item.setText(0, domain)

                # Устанавливаем фиолетовый цвет для домена
                set_tree_item_color(domain_item, QColor("purple"))

                for cert_id in cert_ids:
                    cert_item = QTreeWidgetItem(domain_item)
                    cert_item.setText(0, cert_id)

                    # Устанавливаем зелёный цвет для ID сертификатов
                    set_tree_item_color(cert_item, QColor("green"))

            self.ui.treeWidgetFiles.expandAll()  # Автоматически разворачиваем все узлы

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки файла: {e}")

##### TREEWIDGETFILES RESPONSIBLE FOR PARSING CERTIFICATE FROM CERTIFICATE ID #########
##### TREEWIDGETFILES RESPONSIBLE FOR PARSING CERTIFICATE FROM CERTIFICATE ID #########

    def handle_tree_item_double_click(self, item):
        """Обрабатывает двойной клик по элементу treeWidgetFiles."""
        if item.parent() is None:  # Если это домен, а не ID сертификата
            domain = item.text(0)
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Вы хотите отсканировать все сертификаты для домена {domain}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                async def _scan_domain_certificates():
                    all_certificates = []
                    for i in range(item.childCount()):
                        cert_item = item.child(i)
                        cert_id = cert_item.text(0)

                        try:
                            cert_details = await fetch_certificate_details(cert_id, log_callback=self.update_logs)
                            if cert_details:
                                all_certificates.append(cert_details)
                                self.update_logs(f"Сертификат {cert_id} для домена {domain} успешно отсканирован.", "green")
                        except Exception as e:
                            self.update_logs(f"Ошибка сканирования сертификата {cert_id}: {e}", "red")

                    return all_certificates

                def on_finished(result):
                    # Изменяем цвет домена и его сертификатов на красный
                    set_tree_item_color(item, QColor("red"))

                    # Сохраняем результаты в JSON
                    self.save_certificates_to_json(domain, result)

                def on_error(e):
                    self.update_logs(f"Ошибка сканирования домена {domain}: {e}", "red")

                if self.worker is not None and self.worker.isRunning():
                    self.worker.quit()  # Останавливаем предыдущий worker, если он запущен

                self.worker = AsyncWorker(_scan_domain_certificates())
                self.worker.finished.connect(on_finished)
                self.worker.error.connect(on_error)
                self.worker.start()

        else:  # Если это конкретный ID сертификата
            cert_id = item.text(0)
            domain = item.parent().text(0)  # Получаем домен из родительского узла
            
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Вы хотите отсканировать сертификат с ID {cert_id}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                async def _scan_single_certificate():
                    return await fetch_certificate_details(cert_id, log_callback=self.update_logs)

                def on_finished(cert_details):
                    if cert_details:
                        self.update_logs(f"Сертификат {cert_id} успешно отсканирован.", "green")

                        # Если cert_details уже содержит id и details
                        if isinstance(cert_details, dict) and "id" in cert_details and "details" in cert_details:
                            # Сохраняем напрямую
                            self.save_certificates_to_json(domain, [cert_details])
                        else:
                            # Если cert_details это строка, оборачиваем в объект
                            self.save_certificates_to_json(domain, [{"id": cert_id, "details": cert_details}])

                        # Изменяем цвет сертификата на красный
                        set_tree_item_color(item, QColor("red"))
                    else:
                        self.update_logs(f"Сертификат {cert_id} не найден.", "orange")

                def on_error(e):
                    self.update_logs(f"Ошибка сканирования сертификата {cert_id}: {e}", "red")

                if self.worker is not None and self.worker.isRunning():
                    self.worker.quit()  # Останавливаем предыдущий worker, если он запущен

                self.worker = AsyncWorker(_scan_single_certificate())
                self.worker.finished.connect(on_finished)
                self.worker.error.connect(on_error)
                self.worker.start()

##### SCAN CHOOSEN SUBDOMAIN CERTIFICATES WORKS WITH handle_tree_item_double_click, treeWidgetFiles#########
##### SCAN CHOOSEN SUBDOMAIN CERTIFICATES WORKS WITH handle_tree_item_double_click, treeWidgetFiles#########

    def scan_domain_certificates(self, domain_item):
        """Сканирует все сертификаты для домена."""
        domain = domain_item.text(0)

        async def _scan_certificates():
            all_certificates = {}
            for i in range(domain_item.childCount()):
                cert_item = domain_item.child(i)
                cert_id = cert_item.text(0)

                try:
                    cert_details = await fetch_certificate_details(cert_id, log_callback=self.update_logs)
                    if cert_details:
                        if domain not in all_certificates:
                            all_certificates[domain] = []
                        all_certificates[domain].append(cert_details)

                        # Лог успешного сканирования
                        self.update_logs(f"Сертификат {cert_id} для домена {domain} успешно отсканирован.", "green")
                except Exception as e:
                    self.update_logs(f"Ошибка сканирования сертификата {cert_id}: {e}", "red")

            return all_certificates # Сохранения при сканирование корневого узла

        def on_finished(result):
            # Изменяем цвет домена и его сертификатов на красный
            set_tree_item_color(domain_item, QColor("red"))

            # Сохраняем результаты в JSON
            self.save_certificates_to_json(result)

        def on_error(e):
            self.update_logs(f"Ошибка сканирования домена {domain}: {e}", "red")

        if self.worker and self.worker.isRunning():
            self.worker.quit()  # Останавливаем предыдущий worker, если он запущен

        self.worker = AsyncWorker(_scan_certificates())
        self.worker.finished.connect(on_finished)
        self.worker.error.connect(on_error)
        self.worker.start()

####### SCAN SINGLE CERTIFICATE ID AND SAVE IT treeWidgetFiles ##########
####### SCAN SINGLE CERTIFICATE ID AND SAVE IT treeWidgetFiles ##########

    def scan_single_certificate(self, cert_item):
        """Сканирует один сертификат по ID."""
        domain = cert_item.parent().text(0)
        cert_id = cert_item.text(0)
        
        async def _scan_single_certificate():
            return await fetch_certificate_details(cert_id, log_callback=self.update_logs)

        def on_finished(cert_details):
            if cert_details:
                self.update_logs(f"Сертификат {cert_id} для домена {domain} успешно отсканирован.", "green")

                # Сохраняем в JSON
                self.save_certificates_to_json(domain, [{"id": cert_id, "details": cert_details}])

                # Изменяем цвет сертификата на красный
                set_tree_item_color(cert_item, QColor("red"))
            else:
                self.update_logs(f"Сертификат {cert_id} не найден.", "orange")

        def on_error(e):
            self.update_logs(f"Ошибка сканирования сертификата {cert_id}: {e}", "red")

        if self.worker and self.worker.isRunning():
            self.worker.quit()  # Останавливаем предыдущий worker, если он запущен

        self.worker = AsyncWorker(_scan_single_certificate())
        self.worker.finished.connect(on_finished)
        self.worker.error.connect(on_error)
        self.worker.start()

####### SAVING CERTIFICATE BY SUBDOMAIN OR CHOOSEN CERTIFICATE ID treeWidgetFiles ##########
####### SAVING CERTIFICATE BY SUBDOMAIN OR CHOOSEN CERTIFICATE ID treeWidgetFiles ##########

    def save_certificates_to_json(self, domain, data):
        """Сохраняет данные сертификатов в JSON файл."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчет", "", "JSON Files (*.json)")
        if not file_path:
            return

        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    existing_data = json.load(file)
            else:
                existing_data = {}

            # Обновляем данные
            if domain not in existing_data:
                existing_data[domain] = []
            existing_data[domain].extend(data)

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(existing_data, file, indent=4, ensure_ascii=False)

            self.update_logs(f"Результаты сканирования сохранены в {file_path}", "blue")
        except Exception as e:
            self.update_logs(f"Ошибка сохранения данных в JSON: {e}", "red")



##### LOAD DOMAIN,SUBDOMAIN JSON FILE IN TREEWIDGETDOMAIN ######
##### LOAD DOMAIN,SUBDOMAIN JSON FILE IN TREEWIDGETDOMAIN ######

    def load_and_display_json(self):
        """Загружает JSON-файл и отображает его содержимое в treeWidgetDomain."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите JSON файл", "", "JSON Files (*.json)")
        if not file_path:
            QMessageBox.warning(self, "Ошибка", "Файл не выбран!")
            return

        try:
            # Загрузка и проверка JSON
            data = load_and_validate_json(file_path)

            # Заполнение TreeWidget
            populate_tree_with_json(data, self.ui.treeWidgetDomain)

            self.update_logs("Данные успешно загружены в дерево.", "green")
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            
##### DOUBLE CLICK FOR TREEWIDGETDOMAIN FOR GETING DOMAIN/SUBDOMAIN CERTIFICATE ID #######
##### DOUBLE CLICK FOR TREEWIDGETDOMAIN FOR GETING DOMAIN/SUBDOMAIN CERTIFICATE ID #######
            
    def handle_domain_item_double_click(self, item):
        """
        Обрабатывает двойной клик на элементе treeWidgetDomain.
        """
        parent = item.parent()

        # Проверяем, если это один из корневых элементов (Active Subdomains, Inactive Subdomains, Domains)
        if parent is None:
            category = item.text(0)
            domains_or_subdomains = [item.child(i).text(0) for i in range(item.childCount())]

            if not domains_or_subdomains:
                QMessageBox.information(self, "Информация", f"В категории {category} нет элементов для сканирования.")
                return

            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Вы хотите получить ID сертификатов для всех элементов категории {category}?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                all_cert_ids = {}

                async def _fetch_cert_ids():
                    for entry in domains_or_subdomains:
                        cert_ids = await fetch_certificate_ids(entry, log_callback=self.update_logs)
                        if cert_ids and entry in cert_ids:
                            all_cert_ids[entry] = cert_ids[entry]
                    return all_cert_ids

                def on_finished(result):
                    if result:
                        self.update_logs(f"Найдено сертификатов: {sum(len(v) for v in result.values())} в категории {category}.", "green")
                        try:
                            save_certificates_to_treewidget_domain(result, log_callback=self.update_logs)
                        except Exception as e:
                            self.update_logs(f"Ошибка при сохранении сертификатов для {category}: {e}", "red")
                    else:
                        self.update_logs(f"Сертификаты для категории {category} не найдены.", "orange")

                def on_error(e):
                    self.update_logs(f"Ошибка при получении сертификатов для {category}: {e}", "red")

                if self.worker is not None and self.worker.isRunning():
                    self.worker.quit()  # Останавливаем предыдущий worker, если он запущен

                self.worker = AsyncWorker(_fetch_cert_ids())
                self.worker.finished.connect(on_finished)
                self.worker.error.connect(on_error)
                self.worker.start()

            return

        # Если элемент находится внутри категорий (обычный домен или поддомен)
        if parent.text(0) in ["Active Subdomains", "Inactive Subdomains"]:
            subdomain = item.text(0)
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Вы хотите получить ID сертификатов для поддомена {subdomain}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                async def _fetch_cert_ids():
                    return await fetch_certificate_ids(subdomain, log_callback=self.update_logs)

                def on_finished(cert_ids):
                    if cert_ids and subdomain in cert_ids:
                        self.update_logs(f"Найдено {len(cert_ids[subdomain])} сертификатов для поддомена {subdomain}.", "green")
                        try:
                            save_certificates_to_treewidget_domain({subdomain: cert_ids[subdomain]}, log_callback=self.update_logs)
                        except Exception as e:
                            self.update_logs(f"Ошибка при сохранении сертификатов для {subdomain}: {e}", "red")
                    else:
                        self.update_logs(f"Сертификаты для поддомена {subdomain} не найдены.", "orange")

                def on_error(e):
                    self.update_logs(f"Ошибка при получении сертификатов для {subdomain}: {e}", "red")

                if self.worker is not None and self.worker.isRunning():
                    self.worker.quit()  # Останавливаем предыдущий worker, если он запущен

                self.worker = AsyncWorker(_fetch_cert_ids())
                self.worker.finished.connect(on_finished)
                self.worker.error.connect(on_error)
                self.worker.start()

        elif parent.text(0) == "Domains":
            domain = item.text(0)
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Вы хотите получить ID сертификатов для домена {domain}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                async def _fetch_cert_ids():
                    return await fetch_certificate_ids(domain, log_callback=self.update_logs)

                def on_finished(cert_ids):
                    if cert_ids and domain in cert_ids:
                        self.update_logs(f"Найдено {len(cert_ids[domain])} сертификатов для домена {domain}.", "green")
                        try:
                            save_certificates_to_treewidget_domain({domain: cert_ids[domain]}, log_callback=self.update_logs)
                        except Exception as e:
                            self.update_logs(f"Ошибка при сохранении сертификатов для {domain}: {e}", "red")
                    else:
                        self.update_logs(f"Сертификаты для домена {domain} не найдены.", "orange")

                def on_error(e):
                    self.update_logs(f"Ошибка при получении сертификатов для {domain}: {e}", "red")

                if self.worker is not None and self.worker.isRunning():
                    self.worker.quit()  # Останавливаем предыдущий worker, если он запущен

                self.worker = AsyncWorker(_fetch_cert_ids())
                self.worker.finished.connect(on_finished)
                self.worker.error.connect(on_error)
                self.worker.start()



 ####### STOP SCANING ############### STOP SCANING ############### STOP SCANING ########
 ####### STOP SCANING ############### STOP SCANING ############### STOP SCANING ########

    def stop_scan(self):
        """Останавливает процесс анализа сертификатов и потоки."""
        # Старый код для остановки анализа
        try:
            stop_scanning()
            self.update_logs("Процесс анализа сертификатов остановлен.", "orange")
        except Exception as e:
            self.update_logs(f"Ошибка остановки процесса: {e}", "red")

####### CLEAR LOGS  ############### CLEAR LOGS  ############### CLEAR LOGS  ########
####### CLEAR LOGS  ############### CLEAR LOGS  ############### CLEAR LOGS  ########

    def clear_logs_action(self):
        """Очищает содержимое логов."""
        clear_logs(self.ui.plainTextEditCertificateLogs)

##### UPDATE LOGS WITH COLORS ########### UPDATE LOGS WITH COLORS ########### UPDATE LOGS WITH COLORS ######
##### UPDATE LOGS WITH COLORS ########### UPDATE LOGS WITH COLORS ########### UPDATE LOGS WITH COLORS ######

    def update_logs(self, message, color):
        """Обновление логов с цветами. Метод вызывается из асинхронного потока."""
        # Форматируем сообщение с цветом
        formatted_message = f'<span style="color:{color};">{message}</span>'

        # Используем QMetaObject.invokeMethod для безопасного обновления GUI
        QMetaObject.invokeMethod(
            self.ui.plainTextEditCertificateLogs,  # Объект, метод которого вызываем
            "append",                             # Метод, который нужно вызвать (append для добавления текста)
            Qt.QueuedConnection,                  # Тип соединения (асинхронный вызов)
            Q_ARG(str, formatted_message)         # Аргументы для метода append
        )

        


