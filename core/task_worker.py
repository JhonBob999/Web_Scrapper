from PyQt5.QtCore import QThread, pyqtSignal
from core.scraper import scrape_website

class TaskWorker(QThread):
    # 🔄 Добавили cookies в сигнал
    task_finished = pyqtSignal(int, str, str, list, dict)  # row_index, status, message, results, cookies

    def __init__(self, row_index, url, selector, method, params=None, cookies=None):
        super().__init__()
        self.row_index = row_index
        self.url = url
        self.selector = selector
        self.method = method
        self.params = params or {}
        self.cookies = cookies or {}

    def run(self):
        try:
            use_xpath = self.method.lower() == "xpath"

            # 🔽 Парсим сайт, получаем результат + session.cookies
            results, final_cookies = scrape_website(
                url=self.url,
                selector=self.selector,
                use_xpath=use_xpath,
                proxy=self.params.get("proxy"),
                headers=self.params.get("headers"),
                user_agent=self.params.get("user_agent"),
                timeout=self.params.get("timeout", 10),
                cookies=self.cookies
            )

            # 🔼 Передаём всё: статус, сообщение, данные, cookies
            if results:
                self.task_finished.emit(
                    self.row_index,
                    "✅ Успешно",
                    f"Найдено элементов: {len(results)}",
                    results,
                    final_cookies
                )
            else:
                self.task_finished.emit(
                    self.row_index,
                    "✅ Успешно",
                    "Элементов не найдено",
                    results,
                    final_cookies
                )

        except Exception as e:
            # ⛔ В случае ошибки — пустые результаты, куки не обновляем
            self.task_finished.emit(
                self.row_index,
                "❌ Ошибка",
                str(e),
                [],
                self.cookies
            )
