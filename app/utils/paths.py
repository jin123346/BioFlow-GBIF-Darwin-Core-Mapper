from pathlib import Path
import sys

def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent

def get_resource_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return get_base_dir()

BASE_DIR = get_base_dir()
RESOURCE_DIR = get_resource_dir()
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
MAPPING_DIR = DATA_DIR / "mapping_templates"
CACHE_DIR = DATA_DIR / "cache"
LOGO_PATH = RESOURCE_DIR / "bioflow_logo.png"

for folder in [DATA_DIR, OUTPUT_DIR, MAPPING_DIR, CACHE_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
