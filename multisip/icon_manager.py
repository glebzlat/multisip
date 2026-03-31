from PyQt6.QtGui import QIcon

from .common import ICONS_DIR


class IconNotFound(Exception):
    pass


def get_icon(name: str) -> QIcon:
    icon_path = ICONS_DIR / f"{name}.svg"
    if not icon_path.exists():
        raise IconNotFound(f"Icon {name} not found")
    return QIcon(str(icon_path))
