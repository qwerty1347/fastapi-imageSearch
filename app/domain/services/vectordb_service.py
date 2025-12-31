import uuid

from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import PointStruct

from app.domain.modules.vectordb.qdrant import Qdrant
from config.embedding_model import EmbeddingModel
from common.utils.image import convert_to_static_image_url, create_point_data, detect_confidence_objects
from common.utils.storage import get_fruits_image_path


class VectorDBService:
    def __init__(self):
        self.qdrant = Qdrant()


    async def handle_fruits_images(self):
        point_data = await self.create_points_from_images()
        result = await self.qdrant.upsert_points(collection_name="fruits", points=point_data)
        return result


    async def create_points_from_images(self) -> list:
        fruits_image_path = get_fruits_image_path()
        points = []
        embedding_model = SentenceTransformer(EmbeddingModel.MODELS['hugging_face']['clip']['ViT-L-14']['name'])

        for image_path in fruits_image_path:
            detected_objects = detect_confidence_objects(image_path)
            point_data = create_point_data(image_path, detected_objects)

            if point_data is None:
                print(f"point_data is None: {image_path}")
                continue

            else:
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

        return points