from pathlib import Path

from PyQt6.QtGui import QIcon

_module_path = Path(__file__).absolute()
_resources_dir = _module_path.parent / "resources" / "icons"


class IconNotFound(Exception):
    pass


def get_icon(name: str) -> QIcon:
    icon_path = _resources_dir / f"{name}.svg"
    if not icon_path.exists():
        raise IconNotFound(f"Icon {name} not found")
    return QIcon(str(icon_path))
