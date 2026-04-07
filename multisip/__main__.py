import sys
import logging

from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import multisip.resources

from .widgets.main_window import MainWindow
from .worker import Worker
from .config import Config
from .log import configure_logging, clear_log_file


def main():
    app = QApplication(sys.argv)
    app_config = Config(
        domain="10.10.2.4",
    )

    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        root_logger, log_bridge, tail_handler = configure_logging(tmpdir_path, app_config)

        loop = Worker(app_config, tmpdir_path)

        def clear_logs():
            clear_log_file(root_logger)
            tail_handler.clear()

        window = MainWindow(loop, app_config, tail_handler)
        window.setLogLevel.connect(lambda level: root_logger.setLevel(level))
        window.clearLogs.connect(clear_logs)
        log_bridge.lineAdded.connect(
            window.handle_log_line_added,
            Qt.ConnectionType.QueuedConnection
        )

        window.show()
        return app.exec()


if __name__ == "__main__":
    sys.exit(main())
