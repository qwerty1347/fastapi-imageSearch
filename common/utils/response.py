from http import HTTPStatus
from fastapi.responses import JSONResponse

from common.constants.http_code import HttpCodeConstants


def success_response(data: dict = None, code: int = HTTPStatus.OK) -> JSONResponse:
    """
    성공 응답을 생성하는 함수

    매개변수:
    - data (dict): 응답 데이터 (기본값: None)
    - code (int): HTTP 상태 코드 (기본값: 200)

    반환값:
    - JSONResponse: FastAPI의 JSON 응답 객체로, 성공 정보를 담고 있습니다.
    """
    if data is None:
        data = {}

    return JSONResponse(
        status_code=code,
        content={
            "result": True,
            "code": code,
            "data": data
        }
    )


def error_response(code: int = HttpCodeConstants.UNKNOWN_ERROR, message: str = "Unknown Server Error") -> JSONResponse:
    """
    에러 응답을 생성하는 함수

    매개변수:
    - code (int): HTTP 상태 코드 (기본값: 520)
    - message (str): 에러 메시지 (기본값: "Unknown Server Error")

    반환값:
    - JSONResponse: FastAPI의 JSON 응답 객체로, 에러 정보를 담고 있습니다.
    """
    return JSONResponse(
        status_code=code,
        content={
            "result": False,
            "code": code,
            "data": None
        }
    )