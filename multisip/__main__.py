import sys
import logging

from PyQt6.QtWidgets import QApplication

from .widgets.main_window import MainWindow
from .worker import Worker
from .config import Config

if __name__ == "__main__":
    logging.basicConfig(style="{", level=logging.DEBUG)
    app = QApplication(sys.argv)
    config = Config(
        domain="10.10.2.4"
    )
    loop = Worker()
    form = MainWindow(loop, config)
    form.show()
    sys.exit(app.exec())
