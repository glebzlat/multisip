from tempfile import TemporaryDirectory
from pathlib import Path

from PySide6.QtCore import QResource


class Config:

    def __init__(self):
        self._config_src = QResource(":/baresip.conf")

        self._tmpdir = TemporaryDirectory()

        self._tmpdir_path = Path(self._tmpdir.name)
        self._config_out_file = self._tmpdir_path / "config"
        print(self._tmpdir_path)

        with open(self._config_out_file, "w") as fout:
            raw_data = self._config_src.uncompressedData()
            text = raw_data.data().decode("UTF-8")
            fout.write(text)
            fout.flush()

    def __del__(self):
        self._tmpdir.cleanup()

    @property
    def config_file(self) -> str:
        return self._config_out_file
