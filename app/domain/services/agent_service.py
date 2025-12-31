import tempfile

from http import HTTPStatus
from pathlib import Path
from fastapi import UploadFile
from fastapi.encoders import jsonable_encoder
from sentence_transformers import SentenceTransformer

from app.domain.services.vectordb_service import VectorDBService
from config.embedding_model import EmbeddingModel
from common.utils.image import create_point_data, detect_confidence_objects
from common.utils.response import error_response, success_response


class AgentService():
    def __init__(self):
        self.vectordb_service = VectorDBService()


    async def handle_image(self, file: UploadFile):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file.write(await file.read())
            temp_file.flush()
            image_path = Path(temp_file.name)

        try:
            detected_objects = detect_confidence_objects(image_path)
            point_data = create_point_data(image_path, detected_objects)

            if point_data is None:
                return error_response(HTTPStatus.UNPROCESSABLE_ENTITY, "point_data is None")

            embedding_model = SentenceTransformer(EmbeddingModel.MODELS['hugging_face']['clip']['ViT-L-14']['name'])
            embedded = embedding_model.encode(point_data['crop'])
            response = await self.vectordb_service.qdrant.find_points(collection_name="fruits", query=embedded, limit=5)
            result = self.parse_data_from_points(response)

            return success_response(jsonable_encoder(result))

        finally:
            image_path.unlink(missing_ok=True)


    def parse_data_from_points(self, points):
        return [
            {
                "id": point.id,
                "image_path": point.payload["image"],
                "bbox": point.payload["bbox"],
                "score": float(point.score),
            }
            for point in points
        ]