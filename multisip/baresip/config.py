from tempfile import TemporaryDirectory
from pathlib import Path

from ..common import RESOURCES_DIR


class Config:

    def __init__(self):
        self._tmpdir = TemporaryDirectory()
        self._config_file = RESOURCES_DIR / "baresip.conf"

        self._tmpdir_path = Path(self._tmpdir.name)
        self._config_out_file = self._tmpdir_path / "config"

        with (open(self._config_file, "r") as fin,
              open(self._config_out_file, "w") as fout):
            print(fin.read(), file=fout)

    def __del__(self):
        self._tmpdir.cleanup()

    @property
    def config_file(self) -> str:
        return self._config_out_file
