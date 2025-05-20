from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from utils.scanner_utils.tree_widget_context_menu import TreeWidgetWithContextMenu
from utils.scanner_utils.Json_convertor_utils import load_json_file, parse_json_to_tree, tree_to_json
from ui.scanner_ui.json_convertor_ui import Ui_JsonConvertor
import json, os

class JsonConvertor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_JsonConvertor()
        self.ui.setupUi(self)

        # Замена стандартного TreeWidget на TreeWidgetWithContextMenu
        self.TreeWidgetWithContextMenu = TreeWidgetWithContextMenu()
        self.ui.treeWidgetLoadJson.setParent(None)  # Удаляем стандартный виджет
        self.ui.horizontalLayout.addWidget(self.TreeWidgetWithContextMenu)  # Добавляем новый
        

        # Подключение действий меню
        self.ui.actionAdd_json_file.triggered.connect(self.load_json_into_tree)
        self.ui.actionSave_json_file.triggered.connect(self.save_tree_to_json)


    def load_json_into_tree(self):
        """Загружает JSON-файл и отображает его в TreeWidgetWithContextMenu."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите JSON файл", "", "JSON Files (*.json)")
        self.ui.label_File_Name.setText(f"Loaded file: {os.path.basename(file_path)}")
        if not file_path:
            return

        try:
            data = load_json_file(file_path)  # Загружаем JSON
            self.TreeWidgetWithContextMenu.clear()  # Очищаем дерево перед загрузкой

            # Новый вызов
            parse_json_to_tree(data, None, self.TreeWidgetWithContextMenu)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки JSON: {e}")


    def save_tree_to_json(self):
        """
        Сохраняет содержимое TreeWidgetWithContextMenu в JSON-файл.
        """
        # Открыть диалог для выбора пути сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить JSON файл", "", "JSON Files (*.json)")
        if not file_path:
            QMessageBox.warning(self, "Предупреждение", "Сохранение отменено пользователем.")
            return

        try:
            # Преобразуем содержимое дерева в JSON
            data = tree_to_json(self.TreeWidgetWithContextMenu)

            # Сохраняем данные в файл
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "Успех", f"JSON-файл успешно сохранён: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении файла: {e}")
            

