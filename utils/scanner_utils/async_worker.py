from PyQt5.QtCore import QThread, pyqtSignal
import asyncio

class AsyncWorker(QThread):
    finished = pyqtSignal(object)  # Сигнал для передачи результата
    error = pyqtSignal(Exception)  # Сигнал для передачи ошибки
    progress = pyqtSignal(int)     # Сигнал для передачи прогресса

    def __init__(self, coroutine):
        super().__init__()
        self.coroutine = coroutine

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.coroutine)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)
        finally:
            loop.close()