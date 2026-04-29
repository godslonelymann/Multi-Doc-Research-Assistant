from pathlib import Path
import sys

server_dir = Path(__file__).resolve().parents[1] / "server"
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

from app.main import app
