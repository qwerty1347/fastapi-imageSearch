import importlib
import pkgutil

from fastapi import APIRouter


def auto_include_domain_routers(parent_router: APIRouter, base_package: str):
    """
    base_package 하위 모든 router.py 파일에서 router 객체를 찾아 parent_router에 include
    Args:
        parent_router (APIRouter): 최상위 버전 API 라우터
        base_package (str): 예) "app.api.v1"
    """
    package = importlib.import_module(base_package)

    for finder, name, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if name.endswith(".router"):
            module = importlib.import_module(name)
            if hasattr(module, "router"):
                parent_router.include_router(module.router)