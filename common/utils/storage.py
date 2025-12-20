from pathlib import Path

from config.settings import settings


def get_fruits_image_path() -> list[Path]:
    fruits_dir = Path(settings.IMAGE_PATH) / "fruits"
    images_path = [
        p for p in fruits_dir.glob("*")
        if p.suffix.lower() in ['.jpg', '.jpeg', '.png']
    ]

    return images_path
