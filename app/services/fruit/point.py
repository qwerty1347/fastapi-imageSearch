import uuid

from pathlib import Path
from PIL import Image
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer
from ultralytics import YOLO

from app.core.utils.image import get_image_ratio
from app.core.utils.url import convert_to_static_image_url
from app.infrastructure.storage.image import get_fruit_images
from app.infrastructure.vectordb.qdrant import Qdrant
from config.embedding_model import EmbeddingModel


class FruitPointService():
    def __init__(self, qdrant: Qdrant, embedding_model: SentenceTransformer, yolo_model: YOLO):
        self.qdrant = qdrant
        self.embedding_model = embedding_model
        self.yolo_model = yolo_model


    def embed_fruit_images(self):
        fruits_image_path = get_fruit_images()
        points = []

        for image_path in fruits_image_path:
            detected_objects = self.detect_objects_from_image(image_path)
            custom_point_data = self.create_point_data(image_path, detected_objects)

            if custom_point_data is None:
                continue

            points.append(self.build_points(image_path, custom_point_data))

        self.qdrant.upsert_points(collection_name="fruits", points=points)


    def build_points(self, image_path: Path, custom_point_data):
        return PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, image_path.name)),
            vector=self.embedding_model.encode(custom_point_data['crop']),
            payload={
                "image": convert_to_static_image_url(image_path),
                "bbox": custom_point_data['bbox'],
            }
        )




    def detect_objects_from_image(self, image_path: Path):
        return self.yolo_model(image_path, conf=0.1)[0]


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