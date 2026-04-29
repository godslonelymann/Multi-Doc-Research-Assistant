from pathlib import Path

from app.core.config import settings


def ensure_local_runtime() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    _ensure_sqlite_parent()


def _ensure_sqlite_parent() -> None:
    if not settings.database_url.startswith("sqlite:///"):
        return

    database_path = settings.database_url.replace("sqlite:///", "", 1)
    if database_path == ":memory:":
        return

    Path(database_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
