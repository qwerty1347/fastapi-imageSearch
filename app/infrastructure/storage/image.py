from pathlib import Path
import tempfile

from fastapi import UploadFile

from app.core.config import config


def get_fruit_images() -> list[Path]:
    """
    'images/fruits' 디렉토리에 있는 모든 과일 이미지를 검색합니다.
    '.jpg', '.jpeg', '.png' 확장자를 가진 파일만 검색합니다.

    Returns:
        Path 객체를 나타내는 리스트로, 검색된 이미지 파일입니다.
    """
    fruits_dir = Path(config.STORAGE_PATH) / "images" / "fruits"
    return [
        p for p in fruits_dir.glob("*")
        if p.suffix.lower() in ['.jpg', '.jpeg', '.png']
    ]


def get_sample_image_path() -> Path:
    return Path(config.STORAGE_PATH) / "images" / "apple.jpg"


async def save_image_to_temp(file: UploadFile) -> Path:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        temp_file.write(await file.read())
        temp_file.flush()
        return Path(temp_file.name)