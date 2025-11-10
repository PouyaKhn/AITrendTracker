# Re-export load_config from parent config.py to avoid import conflicts
# This allows "from config import load_config" to work even when config/ directory exists
import sys
from pathlib import Path

# Get the parent directory (where config.py is located)
_parent_dir = Path(__file__).parent.parent

# Add parent directory to path if not already there
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

# Import from config.py (the file, not this directory)
import importlib.util
_config_file_path = _parent_dir / "config.py"
_spec = importlib.util.spec_from_file_location("config_module", _config_file_path)
_config_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_config_module)

# Re-export load_config so it can be imported as "from config import load_config"
load_config = _config_module.load_config
