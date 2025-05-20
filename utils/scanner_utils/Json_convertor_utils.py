from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtGui import QColor
import json

def load_json_file(file_path):
    """Загружает JSON-файл и возвращает его как объект Python."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except Exception as e:
        raise ValueError(f"Ошибка загрузки JSON-файла: {e}")


def parse_json_to_tree(data, parent_item=None, treeWidgetLoadJson=None):
    """Определяет корневой уровень JSON и добавляет его в TreeWidget."""
    if parent_item is None and isinstance(data, dict) and treeWidgetLoadJson is not None:
        # Обработка только корневого уровня
        for key, value in data.items():
            root_item = QTreeWidgetItem(treeWidgetLoadJson)  # Создаём узел на верхнем уровне
            root_item.setText(0, key)  # Добавляем ключ в столбец 0
            root_item.setForeground(0, QColor("red"))

            # Проверка: является ли значение массивом
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):  # Проверяем, является ли элемент массива объектом (словарём)
                        # Первый уровень — первый ключ в объекте
                        iterator = iter(item.items())  # Создаём итератор для перебора ключей
                        first_key, first_value = next(iterator)  # Получаем первый ключ и значение
                        first_item = QTreeWidgetItem(root_item)  # Узел для первого ключа
                        first_item.setText(0, first_key)  # Первый ключ записывается в столбец 0
                        first_item.setForeground(0, QColor("blue"))

                        value_item = QTreeWidgetItem(first_item)  # Узел для значения первого ключа
                        value_item.setText(0, str(first_value))  # Значение записывается в столбец 0
                        value_item.setForeground(0, QColor("green"))

                        # Остальные ключи становятся дочерними элементами первого
                        for sub_key, sub_value in iterator:
                            sub_key_item = QTreeWidgetItem(first_item)  # Узел для следующего ключа
                            sub_key_item.setText(0, sub_key)  # Ключ записывается в столбец 0
                            sub_key_item.setForeground(0, QColor("blue"))

                            sub_value_item = QTreeWidgetItem(sub_key_item)  # Узел для значения
                            sub_value_item.setText(0, str(sub_value))  # Значение записывается в столбец 0
                            sub_value_item.setForeground(0, QColor("green"))
                    else:
                        # Если элемент массива не является объектом
                        primitive_item = QTreeWidgetItem(root_item)  # Узел для примитивного значения
                        primitive_item.setText(0, str(item))  # Значение записывается в столбец 0
                        primitive_item.setForeground(0, QColor("green"))


def tree_to_json(tree_widget):
    """Преобразует содержимое QTreeWidget в JSON-объект, начиная с проверки корневого уровня."""
    def parse_object(item):
        """Обрабатывает узел, добавляя ключ, значение и дочерние элементы узла.        """
        obj = {}
        key = item.text(0)  # Ключ из текущего узла

        # Проверяем, есть ли значение для ключа
        if item.childCount() > 0:
            value = item.child(0).text(0)  # Значение из следующего узла
            obj[key] = value

            # Добавляем дочерние элементы узла первого ключа:значения
            for j in range(item.childCount()):
                child_key = item.child(j).text(0)  # Ключ из текущего дочернего узла
                if item.child(j).childCount() > 0:
                    # Проверяем дочерние элементы текущего узла
                    child_value = item.child(j).child(0).text(0)  # Текст первого дочернего узла
                    obj[child_key] = child_value
                elif j > 0:
                    # Если нет дочерних элементов, добавляем только ключ
                    obj[child_key] = None
            return obj


    # Проверяем наличие корневых узлов
    root = tree_widget.invisibleRootItem()
    if root.childCount() == 0:
        raise ValueError("Дерево пустое, нет корневых узлов для сохранения.")

    # Инициализация JSON-объекта
    json_data = {}

    # Обход корневых узлов
    for i in range(root.childCount()):
        root_item = root.child(i)
        key = root_item.text(0)  # Получаем текст корневого узла

        # Проверка типа данных значения
        if root_item.childCount() > 0:
            first_child = root_item.child(0)
            if first_child.childCount() == 0:
                # Если значение - массив, собираем примитивные значения
                json_data[key] = [
                    root_item.child(j).text(0) for j in range(root_item.childCount())
                ]
            else:
                # Если значение - объект, добавляем ключ, значение и дочерние элементы
                json_data[key] = []
                for j in range(root_item.childCount()):
                    obj = parse_object(root_item.child(j))
                    json_data[key].append(obj)
        else:
            # Если у корневого узла нет дочерних элементов
            json_data[key] = None

    return json_data



















