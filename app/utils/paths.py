from pathlib import Path
import sys

def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent

BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
MAPPING_DIR = DATA_DIR / "mapping_templates"

for folder in [DATA_DIR, OUTPUT_DIR, MAPPING_DIR]:
    folder.mkdir(parents=True, exist_ok=True)