import sys
from PyQt5.QtWidgets import QApplication
from scraper_app import ScraperApp  # ← Импортируем твой новый интерфейс

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScraperApp()
    window.show()
    sys.exit(app.exec_())
