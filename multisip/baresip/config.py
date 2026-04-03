from pathlib import Path

from PySide6.QtCore import QResource


def create_config(tmpdir: Path) -> None:
    config_src = QResource(":/baresip.conf")
    config_outfile = tmpdir / "config"
    with open(config_outfile, "w") as fout:
        raw_data = config_src.uncompressedData()
        text = raw_data.data().decode("UTF-8")
        fout.write(text)
        fout.flush()
