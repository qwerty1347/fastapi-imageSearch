import asyncio

from fastapi import UploadFile
from http import HTTPStatus

from app.core.exceptions.custom import BusinessException
from app.infrastructure.storage.image import save_image_to_temp
from app.services.fruit.point import FruitPointService


class FruitSearchService():
    def __init__(self, fruit_point_service: FruitPointService):
        self.fruit_point_service = fruit_point_service


    async def get_similarity_images(self, file: UploadFile):
        uploaded_image_path = await save_image_to_temp(file)

        try:
            detected_objects = await asyncio.to_thread(
                self.fruit_point_service.detect_objects_from_image,
                uploaded_image_path
            )

            custom_point_data = await asyncio.to_thread(
                self.fruit_point_service.create_point_data,
                uploaded_image_path,
                detected_objects
            )

            if custom_point_data is None:
                raise BusinessException(code=HTTPStatus.UNPROCESSABLE_ENTITY, message="custom_point_data is None")

            vector = await asyncio.to_thread(
                self.fruit_point_service.embedding_model.encode,
                custom_point_data['crop']
            )

            response = await asyncio.to_thread(
                self.fruit_point_service.qdrant.find_points,
                collection_name="fruits",
                query=vector,
                limit=5,
            )

            return [
                {
                    "id": point.id,
                    "image_path": point.payload["image"],
                    "bbox": point.payload["bbox"],
                    "score": float(point.score)
                }
                for point in response
            ]

        finally:
            uploaded_image_path.unlink(missing_ok=True)