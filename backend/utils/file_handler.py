import uuid
from pathlib import Path

from backend.config import settings

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def generate_file_id() -> str:
    return str(uuid.uuid4())


def get_upload_path(file_id: str, original_filename: str) -> Path:
    ext = Path(original_filename).suffix.lower()
    return settings.UPLOAD_DIR / f"{file_id}{ext}"


def validate_extension(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def resolve_upload_path(file_id: str) -> Path | None:
    for ext in ALLOWED_EXTENSIONS:
        path = settings.UPLOAD_DIR / f"{file_id}{ext}"
        if path.exists():
            return path
    return None
