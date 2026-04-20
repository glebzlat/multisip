import sys
import shutil

import multisip.resources

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase

from .widgets.main_window import MainWindow
from .worker import Worker
from .config import Config
from .log import configure_logging, clear_log_file


def ensure_baresip() -> Optional[QWidget]:
    baresip_path = shutil.which("baresip")
    if baresip_path is not None:
        return None

    window = QWidget()
    window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
    window.setWindowTitle("MultiSIP")

    layout = QVBoxLayout(window)
    message = QLabel(
        "MultiSIP requires BareSIP to work. "
        "Ensure it is installed and is in your PATH.", window)
    message.setWordWrap(True)
    layout.addWidget(message)

    window.destroyed.connect(lambda: QApplication.instance().quit())
    window.show()
    return window


def main() -> int:
    app = QApplication(sys.argv)
    app.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont))

    error_window = ensure_baresip()
    if error_window is not None:
        return app.exec()

    app_config = Config(
        domain="10.10.2.4",
    )

    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        root_logger, log_bridge, tail_handler, file_handler = configure_logging(tmpdir_path, app_config)

        root_logger.setLevel(app_config.log_level.value)

        try:
            loop = Worker(app_config, tmpdir_path)

            def clear_logs() -> None:
                clear_log_file(root_logger)
                tail_handler.clear()

            def export_logs(outfile: str) -> None:
                shutil.copy(file_handler.baseFilename, outfile)

            window = MainWindow(loop, app_config, tail_handler)

            window.setLogLevel.connect(lambda level: root_logger.setLevel(level))
            window.clearLogs.connect(clear_logs)
            window.exportLogs.connect(export_logs)

            log_bridge.lineAdded.connect(
                window.handle_log_line_added,
                Qt.ConnectionType.QueuedConnection
            )

            window.show()
            return app.exec()
        except Exception as e:
            root_logger.error("error occured: %s", e)
            raise


if __name__ == "__main__":
    sys.exit(main())
