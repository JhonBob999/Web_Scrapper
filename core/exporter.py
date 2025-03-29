from bs4 import BeautifulSoup
import pandas as pd

# EXTRACT LINK AND TEXT FROM HTML BACK IN LIST
# EXTRACT LINK AND TEXT FROM HTML BACK IN LIST

def extract_link_and_text(html):
    """
    Извлекает чистый текст и ссылку из HTML.
    Возвращает словарь {"title": ..., "link": ..., "description": ...}
    """
    soup = BeautifulSoup(html, 'html.parser')
    a_tag = soup.find('a')

    if a_tag:
        return {
            "title": a_tag.get_text(strip=True),
            "link": a_tag.get('href', None),
            "description": None
        }
    else:
        return {
            "title": soup.get_text(strip=True),
            "link": None,
            "description": None
        }

# CLEAN HTML TAGS AND RETURN CLEAN TEXT
# CLEAN HTML TAGS AND RETURN CLEAN TEXT

def clean_html_tags(html_text):
    """Убирает HTML-теги и возвращает чистый текст"""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator="\n", strip=True)

# SAVING JSON DEFAULT LIST 
# SAVING JSON DEFAULT LIST 

def save_as_default(url, results):
    return {
        "url": url,
        "results": results  # здесь уже словари, не нужно ещё раз чистить
    }

    
    
# 📌 Функция для группировки данных по тегам
# 📌 Функция для группировки данных по тегам

def save_as_dynamic_tags(url, results, selector_input):
    """ Динамически группирует данные по тегам, убирая ненужное """
    selected_tags = [tag.strip() for tag in selector_input.split(",")]  # Получаем теги из input
    grouped_data = {tag: [] for tag in selected_tags}  # Динамически создаем структуру JSON

    for line in results:
        line = line.strip()

        # Фильтруем мусорные строки
        if line.startswith(("Парсим", "✅", "🔹", "❌", "🛑")) or len(line) < 3:
            continue

        # Проверяем ссылки
        if "http" in line or "<a href=" in line:
            text, link = (line.split(" | ") if " | " in line else (line, ""))
            text, link = text.strip(), link.strip()
            if "a" in grouped_data:
                grouped_data["a"].append({"link_text": text, "url": link if link else None})
            continue

        # Определяем, к какому тегу относится контент
        for tag in selected_tags:
            if line.startswith(f"{tag}:"):
                grouped_data[tag].append({"text": line.replace(f"{tag}:", "").strip()})
                break  # Как только нашли тег, переходим к следующему результату
        else:
            continue  # Если строка не начинается с тега, пропускаем её

    return {
        "url": url,
        "data": {tag: grouped_data[tag] for tag in grouped_data if grouped_data[tag]}  # Убираем пустые теги
    }
    
# 📌 Функция для сохранения данных в виде статей
# 📌 Функция для сохранения данных в виде статей

def save_as_articles(url, results):
    articles = []
    current_article = {"title": "", "subtitles": [], "paragraphs": []}

    for line in results:
        if line.startswith("h1:"):
            if current_article["title"]:  # Если уже есть заголовок, сохраняем статью
                articles.append(current_article)
                current_article = {"title": "", "subtitles": [], "paragraphs": []}
            current_article["title"] = line.replace("h1:", "").strip()
        elif line.startswith("h2:"):
            current_article["subtitles"].append(line.replace("h2:", "").strip())
        else:
            current_article["paragraphs"].append(line.strip())

    if current_article["title"]:  # Добавляем последнюю статью
        articles.append(current_article)

    return {
        "url": url,
        "articles": articles
    }

# 📌 Функция для сохранения с привязкой к ссылкам    
# 📌 Функция для сохранения с привязкой к ссылкам

def save_as_with_links(url, results):
    clean_results = [item for item in results if item.get("link")]
    return {
        "url": url,
        "data": clean_results
    }

# DICT WITH RESULTS AND JSON FORMAT FROM COMBOBOX
# DICT WITH RESULTS AND JSON FORMAT FROM COMBOBOX
    
def export_data_to_json(parsed_data, format_type):
    """Обрабатывает словарь с результатами и формирует данные под выбранный формат"""
    result_json = {}

    for url, results in parsed_data.items():
        if format_type == "default":
            result_json[url] = save_as_default(url, results)
        elif format_type == "group_by_tags":
            result_json[url] = save_as_dynamic_tags(url, results, "")
        elif format_type == "articles":
            result_json[url] = save_as_articles(url, results)
        elif format_type == "with_links":
            result_json[url] = save_as_with_links(url, results)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    return result_json

# SAVING TO CSV TABLE
# SAVING TO CSV TABLE

def save_to_csv(parsed_data, file_path):
    """Сохраняет данные в CSV"""
    rows = []
    for url, data in parsed_data.items():
        for item in data:
            if isinstance(item, str):
                item = extract_link_and_text(item)  # 🔥 Конвертируем строку в словарь
            rows.append({
                "URL": url,
                "Title": item.get("title"),
                "Link": item.get("link"),
                "Description": item.get("description")
            })

    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False, encoding='utf-8-sig')

# SAVING TO EXCEL TABLE
# SAVING TO EXCEL TABLE

def save_to_excel(parsed_data, file_path):
    """Сохраняет данные в Excel"""
    rows = []
    for url, data in parsed_data.items():
        for item in data:
            if isinstance(item, str):
                item = extract_link_and_text(item)  # 🔥 Конвертируем строку в словарь
            rows.append({
                "URL": url,
                "Title": item.get("title"),
                "Link": item.get("link"),
                "Description": item.get("description")
            })

    df = pd.DataFrame(rows)
    df.to_excel(file_path, index=False, engine='openpyxl')
