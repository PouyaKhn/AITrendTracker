import sys
from pathlib import Path
import importlib.util

_parent_dir = Path(__file__).parent.parent

if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

_config_file_path = _parent_dir / "config.py"
_spec = importlib.util.spec_from_file_location("config_module", _config_file_path)
_config_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_config_module)

load_config = _config_module.load_config
