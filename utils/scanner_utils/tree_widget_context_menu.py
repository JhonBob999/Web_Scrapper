from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QApplication, QFileDialog, QColorDialog, QInputDialog
from utils.scanner_utils.Json_convertor_utils import tree_to_json
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
import sys, json


class TreeWidgetWithContextMenu(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderLabel("Load Json File")  # Устанавливаем заголовок
        self.setContextMenuPolicy(Qt.CustomContextMenu)  # Разрешаем контекстное меню
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Пример узлов
        root = QTreeWidgetItem(self, ["Корневой узел"])
        child = QTreeWidgetItem(root, ["Дочерний узел"])
        self.addTopLevelItem(root)

    def show_context_menu(self, position):
        """Обработка контекстного меню."""
        selected_item = self.itemAt(position)  # Получаем узел под курсором
        context_menu = QMenu(self)

        # Подменю "Управление узлами"
        manage_nodes_menu = context_menu.addMenu("Управление узлами")

        # Опции подменю
        add_action = manage_nodes_menu.addAction("Добавить узел")
        delete_action = manage_nodes_menu.addAction("Удалить узел")
        edit_action = manage_nodes_menu.addAction("Редактировать узел")
        clone_action = manage_nodes_menu.addAction("Клонировать узел")
        # Подменю для подменю
        advanced_menu = manage_nodes_menu.addMenu("Изменения структуры узлов")
        # Опции для дополнительного подменю
        
        # Подключаем обработчики опций
        add_action.triggered.connect(lambda: self.add_node(selected_item))
        delete_action.triggered.connect(lambda: self.delete_node(selected_item))
        edit_action.triggered.connect(lambda: self.edit_node(selected_item))
        clone_action.triggered.connect(lambda: self.clone_node(selected_item))
        
        # Универсальное действие "Разделить узел"
        manage_split_nodes = context_menu.addMenu("Разделить по узлам")
        
        # Опции подменю
        split_action = manage_split_nodes.addAction("Разделить по тексту")
        
        # Подключаем обработчики опций
        split_action.triggered.connect(lambda: self.split_node_by_text(selected_item))
        
        # Подменю "Управление структурой"
        manage_structure_menu = context_menu.addMenu("Управление структурой")
        
        # Опции подменю
        expand_all_action = manage_structure_menu.addAction("Развернуть все узлы")
        collapse_all_action = manage_structure_menu.addAction("Свернуть все узлы")
        expand_current_action = manage_structure_menu.addAction("Развернуть текущий узел")
        collapse_current_action = manage_structure_menu.addAction("Свернуть текущий узел")

        # Подключаем обработчики опций
        expand_all_action.triggered.connect(self.expandAll)
        collapse_all_action.triggered.connect(self.collapseAll)
        expand_current_action.triggered.connect(lambda: self.expand_current_node(selected_item))
        collapse_current_action.triggered.connect(lambda: self.collapse_current_node(selected_item))
        
        # Подменю Работа с данными
        manage_data_menu = context_menu.addMenu("Работа с данными")
        
        # Опции подменю
        export_action  = manage_data_menu.addAction("Экспорт узла или всего дерева")
        import_action   = manage_data_menu.addAction("Импорт данных в выбранный узел")
        clear_action = manage_data_menu.addAction("Очистки узла или дерева")
        
        # Подключение действий к обработчикам
        export_action.triggered.connect(lambda: self.export_to_json(selected_item))
        import_action.triggered.connect(lambda: self.import_to_node(selected_item))
        clear_action.triggered.connect(lambda: self.clear_node_or_tree(selected_item))
        
         # Подменю "Визуальные настройки"
        visual_menu = context_menu.addMenu("Визуальные настройки")
        
         # Опции подменю
        change_color_action = visual_menu.addAction("Изменить цвет узла")
        mark_important_action = visual_menu.addAction("Отметить как важный")
        
        # Подключаем обработчики опций
        change_color_action.triggered.connect(lambda: self.change_node_color(selected_item))
        mark_important_action.triggered.connect(lambda: self.mark_node_as_important(selected_item))
        
        # Подменю "Логические действия"
        logical_menu = context_menu.addMenu("Логические действия для списков")
        
        # Опции подменю
        search_action = logical_menu.addAction("Поиск значений в массиве")
        filter_action = logical_menu.addAction("Фильтрация узлов по критерию")
        highlight_action = logical_menu.addAction("Подсветка узлов по критерию")
        
        # Подключаем обработчики опций
        search_action.triggered.connect(lambda: self.search_nodes(selected_item))
        filter_action.triggered.connect(lambda: self.filter_nodes(selected_item))
        highlight_action.triggered.connect(lambda: self.highlight_nodes(selected_item))

        # Отображаем меню
        context_menu.exec_(self.viewport().mapToGlobal(position))
        
####### WORKING WITH NODE IN TREEWIDGETLOADJSON #########
####### WORKING WITH NODE IN TREEWIDGETLOADJSON #########

    def add_node(self, parent_item):
        """Добавляет дочерний узел."""
        if parent_item is None:
            # Если узел не выбран, добавляем на верхний уровень
            new_item = QTreeWidgetItem(self)
            new_item.setText(0, "Новый узел")
            self.addTopLevelItem(new_item)
        else:
            # Добавляем как дочерний узел
            new_item = QTreeWidgetItem(parent_item)
            new_item.setText(0, "Новый узел")
            parent_item.setExpanded(True)

    def delete_node(self, item):
        """Удаляет выбранный узел."""
        if item is None:
            return  # Ничего не делать, если узел не выбран

        parent = item.parent()
        if parent:
            # Удаляем узел из дочерних
            parent.removeChild(item)
        else:
            # Удаляем узел верхнего уровня
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))

    def edit_node(self, item):
        """Редактирует текст узла."""
        if item is not None:
             # Разрешаем редактирование узла
            item.setFlags(item.flags() | Qt.ItemIsEditable)  # Устанавливаем флаг редактируемости
            self.editItem(item, 0)  # Позволяет редактировать текст в колонке 0
        else:
            print("Редактирование не удалось: узел не выбран")  # Сообщение об ошибке
            
    def clone_node(self, item):
        """Клонирует выбранный узел и добавляет его как дочерний к тому же родителю."""
        if item is None:
            print("Клонирование невозможно: узел не выбран")
            return

        def clone_item(src_item):
            """Клонирует один узел."""
            cloned = QTreeWidgetItem()
            cloned.setText(0, src_item.text(0))  # Копируем текст узла

            # Копируем дополнительные свойства (если есть)
            cloned.setFlags(src_item.flags())  # Копируем флаги (например, редактируемость)
            return cloned

        def clone_children(src_item, dest_item):
            """Рекурсивно копирует дочерние узлы."""
            for i in range(src_item.childCount()):
                child = src_item.child(i)
                cloned_child = clone_item(child)  # Клонируем дочерний узел
                dest_item.addChild(cloned_child)  # Добавляем в родительский узел
                clone_children(child, cloned_child)  # Рекурсивно копируем дочерние элементы

        # Создаём копию текущего узла
        cloned_item = clone_item(item)

        # Копируем дочерние узлы
        clone_children(item, cloned_item)

        # Добавляем клонированный узел к родителю
        parent = item.parent()
        if parent:
            parent.addChild(cloned_item)
        else:
            self.addTopLevelItem(cloned_item)

        print(f"Узел '{item.text(0)}' успешно клонирован")
        
####### WORKING WITH COLORS IN TREEWIDGETLOADJSON #######
####### WORKING WITH COLORS IN TREEWIDGETLOADJSON #######

    def change_node_color(self, item):
        """Изменяет цвет узла через палитру цветов."""
        if item:
            color = QColorDialog.getColor()
            if color.isValid():
                item.setForeground(0, QBrush(color))

    def mark_node_as_important(self, item):
        """Отмечает узел как важный с выбором символа."""
        if item:
            # Список доступных символов
            symbols = ["★", "✔", "⚠", "❗", "❄", "✠", "†"]
            
            # Диалог выбора символа
            symbol, ok = QInputDialog.getItem(
                self, 
                "Выбор символа", 
                "Выберите символ для отметки важности:", 
                symbols, 
                0, 
                False
            )
            
            if ok and symbol:
                item.setText(0, f"{symbol} [Важно] {item.text(0)}")
                item.setForeground(0, QBrush(QColor("red")))
          
####### WORKING WITH TREEWIDGETLOADJSON STRUCTURE ########        
####### WORKING WITH TREEWIDGETLOADJSON STRUCTURE ########
        
    def expand_current_node(self, item):
        """Разворачивает текущий узел."""
        if item:
            item.setExpanded(True)  # Разворачивает только указанный узел
        else:
            print("Развернуть невозможно: узел не выбран")
            
    def collapse_current_node(self, item):
        """Сворачивает текущий узел."""
        if item:
            item.setExpanded(False)  # Сворачивает только указанный узел
        else:
            print("Свернуть невозможно: узел не выбран")
            
####### METHODS WORKING WITH DATA ##########            
####### METHODS WORKING WITH DATA ##########
            
    def export_to_json(self, item):
        """Экспортирует выбранный узел или всё дерево в JSON."""
        try:
            # Если выбран узел, оборачиваем его во временное дерево
            if isinstance(item, QTreeWidgetItem):
                temp_tree = QTreeWidget()  # Создаём временное дерево
                temp_root = QTreeWidgetItem(temp_tree)  # Добавляем корневой узел
                temp_root.setText(0, item.text(0))  # Копируем текст узла
                self._clone_subtree(item, temp_root)  # Копируем дочерние узлы

                # Передаём временное дерево в `tree_to_json`
                data = tree_to_json(temp_tree)

            # Если узел не выбран, передаём всё дерево
            else:
                data = tree_to_json(self)

            # Сохранение в JSON-файл
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить JSON", "", "JSON Files (*.json)")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при экспорте в JSON: {e}")

    def _clone_subtree(self, source_item, target_item):
        """Рекурсивно копирует узлы из одного дерева в другое."""
        for i in range(source_item.childCount()):
            source_child = source_item.child(i)
            target_child = QTreeWidgetItem(target_item)
            target_child.setText(0, source_child.text(0))
            self._clone_subtree(source_child, target_child)

    def import_to_node(self, item):
        """Импортирует данные из JSON-файла в текущий узел."""
        if not item:  # Узел не выбран
            print("Импорт невозможен: узел не выбран")
            return

        # Открыть JSON-файл
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть JSON", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                self.add_data_to_node(item, data)
            except Exception as e:
                print(f"Ошибка при загрузке файла: {e}")

    def clear_node_or_tree(self, item):
        """Очищает выбранный узел или всё дерево."""
        if item:  # Если выбран узел, удаляем его
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.takeTopLevelItem(self.indexOfTopLevelItem(item))
        else:  # Если узел не выбран, очищаем всё дерево
            self.clear()

    def add_data_to_node(self, parent_item, data):
        """Добавляет данные из словаря в узел."""
        def recurse(parent, data):
            for item_data in data.get("children", []):
                child = QTreeWidgetItem(parent)
                child.setText(0, item_data["name"])
                recurse(child, item_data)

        recurse(parent_item, data)        

####### LOGIC ACTIONS IN TREEWIDGETLOADJSON ######
####### LOGIC ACTIONS IN TREEWIDGETLOADJSON ######

    def search_nodes(self, item):
            """Поиск подузлов или значений."""
            if item:
                query, ok = QInputDialog.getText(self, "Поиск узлов", "Введите текст для поиска:")
                if ok and query:
                    for i in range(item.childCount()):
                        child = item.child(i)
                        if query.lower() in child.text(0).lower():
                            child.setForeground(0, QBrush(QColor("blue")))

    def filter_nodes(self, item):
        """Фильтрация узлов по критерию с выделением несоответствующих узлов."""
        if item:
            query, ok = QInputDialog.getText(self, "Фильтрация узлов", "Введите текст для фильтрации:")
            if ok and query:
                for i in range(item.childCount()):
                    child = item.child(i)
                    if query.lower() not in child.text(0).lower():
                        child.setForeground(0, QBrush(QColor("gray")))  # Помечаем узлы, не соответствующие критерию
                    else:
                        child.setForeground(0, QBrush(QColor("black")))  # Восстанавливаем цвет для соответствующих узлов


    def highlight_nodes(self, item):
        """Подсветка узлов по критерию."""
        if item:
            query, ok = QInputDialog.getText(self, "Подсветка узлов", "Введите текст для подсветки:")
            if ok and query:
                for i in range(item.childCount()):
                    child = item.child(i)
                    if query.lower() in child.text(0).lower():
                        child.setBackground(0, QBrush(QColor("yellow")))


####### SPLIT NODES AND MAKE NEW NODE ########
####### SPLIT NODES AND MAKE NEW NODE ########

    def split_node_by_text(self, item):
        """Разделяет значение узла по выбранному тексту."""
        if item is None:
            return

        # Получаем текст узла
        value = item.text(0)
        if not value.strip():
            return

        # Запрашиваем текст для разделения
        split_text, ok = QInputDialog.getText(self, "Разделить узел", "Введите текст для разделения:")
        if not ok or not split_text.strip() or split_text not in value:
            return

        # Разделяем значение
        before, match, after = value.partition(split_text)

        # Обновляем текущий узел, оставляя текст до выделенного слова
        item.setText(0, before.strip())

        # Определяем родителя узла для добавления нового узла
        parent = item.parent().parent() if item.parent() else self

        # Создаем новый узел на уровне родителя
        new_item = QTreeWidgetItem(parent)
        new_item.setText(0, match.strip())

        # Если есть текст после выделенного слова, добавляем его как дочерний узел нового узла
        if after.strip():
            child_item = QTreeWidgetItem(new_item)
            child_item.setText(0, after.strip())

        # Раскрываем родителя для отображения изменений
        if parent != self:
            parent.setExpanded(True)


####### CALL MAIN METHOD #######
####### CALL MAIN METHOD #######


if __name__ == "__main__":
    app = QApplication(sys.argv)
    tree = TreeWidgetWithContextMenu()
    tree.resize(400, 300)
    tree.show()
    sys.exit(app.exec_())
