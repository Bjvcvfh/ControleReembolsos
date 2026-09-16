import re
import unicodedata
from pathlib import Path


INVALID_WINDOWS_CHARS = r'<>:"/\|?*'


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def safe_filename_part(value: str, max_length: int = 120) -> str:
    clean = strip_accents(value or "").strip()
    clean = "".join("_" if ch in INVALID_WINDOWS_CHARS else ch for ch in clean)
    clean = re.sub(r"\s+", "_", clean)
    clean = re.sub(r"[^A-Za-z0-9_.-]", "", clean)
    clean = clean.strip("._ ")
    return (clean or "Sem_nome")[:max_length]


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    i = 2
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1
