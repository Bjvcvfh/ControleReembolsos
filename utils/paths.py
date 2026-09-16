import os
import sys
from pathlib import Path


APP_NAME = "ControleReembolsos"


def app_data_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    path = base / APP_NAME
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return path
    except OSError:
        if getattr(sys, "frozen", False):
            fallback = Path(sys.executable).resolve().parent / "data"
        else:
            fallback = Path.cwd() / "data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def database_path() -> Path:
    return app_data_dir() / "reembolsos.db"


def downloads_dir() -> Path:
    path = Path.home() / "Downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def resource_path(relative_path: str) -> str:
    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])
    return str(Path(base) / relative_path)
