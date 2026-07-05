from pathlib import Path
import sys


def ensure_project_root_on_path() -> Path:
    root_dir = Path(__file__).resolve().parents[1]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    return root_dir
