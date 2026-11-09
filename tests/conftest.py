import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANTED = ROOT / "planted"
sys.path.insert(0, str(Path(__file__).parent))
