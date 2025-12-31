from pathlib import Path
from ultralytics import YOLO
from PIL import Image

from config.settings import settings


def convert_to_static_image_url(image_path: Path) -> str:
    relative = image_path.relative_to(settings.STORAGE_PATH)
    return f"/static/{relative.as_posix()}"


def detect_confidence_objects(image_path: Path):
    yolo = YOLO("yolov8n-oiv7.pt")
    return yolo(image_path, conf=0.1)[0]


def get_image_ratio(image, w, h):
    image_x, image_y = image.size
    bbox_area = w * h
    image_area = image_x * image_y

    return bbox_area / image_area


def create_point_data(image_path: Path, detected_objects) -> None | dict:
    boxes = detected_objects.boxes.xyxy
    confs = detected_objects.boxes.conf
    clss = detected_objects.boxes.cls

    if len(boxes) == 0:
        return None

    idx = confs.argmax().item()
    x1, y1, x2, y2 = map(int, boxes[idx])

    # bounding_box 크기
    w = x2- x1
    h = y2 - y1
    min_size = 10

    if w < min_size or h < min_size:
        return None

    image = Image.open(image_path).convert("RGB")
    bbox_ratio = get_image_ratio(image, w, h)
    min_ratio = 0.01

    if bbox_ratio < min_ratio:
        return None

    return {
        "bbox": [x1, y1, x2, y2],
        "crop": image.crop((x1, y1, x2, y2)),
        "confidence": float(confs[idx]),
        "class_id": int(clss[idx]),
        "class_name": detected_objects.names[int(clss[idx])],
        "bbox_ratio": bbox_ratio
    }