from http import HTTPStatus
from fastapi import UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.utils.response import error_response, success_response
from app.infrastructure.storage.image import save_image_to_temp
from app.services.fruit.point import FruitPointService


class FruitSearchService():
    def __init__(self):
        self.fruit_point_service = FruitPointService()


    async def get_similarity_images(self, file: UploadFile) -> JSONResponse:
        uploaded_image_path = await save_image_to_temp(file)

        try:
            detected_objects = self.fruit_point_service.detect_objects_from_image(uploaded_image_path)
            custom_point_data = self.fruit_point_service.create_point_data(uploaded_image_path, detected_objects)

            if custom_point_data is None:
                return error_response(code=HTTPStatus.UNPROCESSABLE_ENTITY, message="point data is None")

            vector = self.fruit_point_service.embedding_model.encode(custom_point_data['crop'])
            response = self.fruit_point_service.qdrant.find_points(collection_name="fruits", query=vector, limit=5)

            result = [
                {
                    "id": point.id,
                    "image_path": point.payload["image"],
                    "bbox": point.payload["bbox"],
                    "score": float(point.score)
                }
                for point in response
            ]

            return success_response(jsonable_encoder(result))

        finally:
            uploaded_image_path.unlink(missing_ok=True)