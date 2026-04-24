import uuid

from pathlib import Path
from PIL import Image
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer
from ultralytics import YOLO

from app.domain.modules.vectordb.qdrant import Qdrant
from app.infrastructure.storage.fruit import get_fruit_images
from common.utils.image import get_image_ratio
from common.utils.url import convert_to_static_image_url
from config.embedding_model import EmbeddingModel


class FruitPointService():
    def __init__(self):
        self.qdrant = Qdrant()


    def build_points(self):
        fruits_image_path = get_fruit_images()
        points = []

        embedding_model = SentenceTransformer(EmbeddingModel.MODELS['hugging_face']['clip']['ViT-L-14']['name'])
        yolo_model = YOLO("yolov8n-oiv7.pt")

        for image_path in fruits_image_path:
            detected_objects = yolo_model(image_path, conf=0.1)[0]
            point_data = self.create_point_data(image_path, detected_objects)

            if point_data is None:
                print(f"point_data is None: {image_path}")
                continue

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding_model.encode(point_data['crop']),
                    payload={
                        "image": convert_to_static_image_url(image_path),
                        "bbox": point_data['bbox'],
                    }
                )
            )

        self.qdrant.upsert_points(collection_name="fruits", points=points)


    def create_point_data(self, image_path: Path, detected_objects) -> dict | None:
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

        with Image.open(image_path) as img:
            image = img.convert("RGB")

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