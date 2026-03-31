from pathlib import Path

_module_path = Path(__file__).absolute()

ROOT_DIR = _module_path.parent
RESOURCES_DIR = ROOT_DIR / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
