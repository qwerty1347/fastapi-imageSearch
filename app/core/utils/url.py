from pathlib import Path

from app.core.config import config


def convert_to_static_image_url(image_path: Path) -> str:
    relative = image_path.relative_to(config.STORAGE_PATH)
    return f"/static/{relative.as_posix()}"