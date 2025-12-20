import importlib
import pkgutil

from fastapi.routing import APIRouter


def get_api_routers() -> list[APIRouter]:
    """
    주어진 패키지에서 버전별 APIRouter를 수집하여 반환하는 함수

    반환값:
    - list[APIRouter]: 수집된 APIRouter 객체들의 리스트
    """
    routers = []

    package_name = "app.api"
    package = importlib.import_module(package_name)

    if not hasattr(package, "__path__"):
        return routers

    for finder, name, ispkg in pkgutil.iter_modules(package.__path__):
        if ispkg and name.startswith("v"):
            module_name = f"{package_name}.{name}"
            module = importlib.import_module(module_name)
            router_attr = f"api_{name}_router"

            router = getattr(module, router_attr, None)
            if router:
                routers.append(router)

    return routers