from celery import Celery

from app.core.config import config


celery = Celery(
    "fastapi_imageSearch",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)

celery.conf.task_queues = {
    "embedding": {}
}
celery.conf.task_default_queue = "embedding"

celery.conf.update(
    # 워커가 한 번에 미리 가져올 태스크 수. 기본 4 → GPU/무거운 태스크는 한 워커가 선점해
    # 다른 워커가 놀게 되므로 1로 두어 작업이 사용 가능한 워커에 골고루 분배되게 한다.
    worker_prefetch_multiplier=1,

    # 태스크가 끝난 뒤에 ack를 보낸다. 워커가 도중에 죽으면 broker가 같은 태스크를
    # 다른 워커에 재할당해 유실을 막는다. embed_fruit_images는 PointStruct id를
    # uuid5(NAMESPACE_URL, image_path.name)로 결정적으로 생성하므로 재실행되어도
    # 같은 ID로 upsert(덮어쓰기)되어 중복 적재가 발생하지 않는다.
    task_acks_late=True,

    # 워커 프로세스가 비정상 종료(SIGKILL/OOM 등)되면 태스크를 명시적으로 reject 하여
    # broker가 재큐하게 만든다. task_acks_late와 짝으로 쓰며 같은 멱등성 전제를 따른다.
    task_reject_on_worker_lost=True,

    # 태스크 hard time limit (초). 초과 시 워커가 강제 종료. 멈춘 작업이 워커를 영구
    # 점유하는 사고를 방지한다. 데이터셋 규모에 맞춰 조정.
    task_time_limit=60 * 30,

    # soft time limit (초). 초과 시 태스크 안에서 SoftTimeLimitExceeded 예외가 발생해
    # 정리 코드를 실행할 기회를 준다. hard limit보다 약간 짧게 잡는다.
    task_soft_time_limit=60 * 25,

    # 결과 backend(Redis DB 1)에 저장된 결과의 만료 시간(초). 결과를 적극 사용하지 않으면
    # 너무 길게 두면 Redis 메모리만 쌓이므로 1일 정도로 제한.
    result_expires=60 * 60 * 24,

    # 워커가 태스크를 시작하면 STARTED 상태로 표시. Flower나 AsyncResult에서
    # PENDING(대기중) ↔ STARTED(실행중) 구분이 가능해져 모니터링/디버깅에 유리.
    task_track_started=True,

    # 직렬화 포맷. 보안상 pickle은 피하고 json으로 통일.
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # 시간대. 로그/스케줄에 한국 시간이 찍히도록 한다.
    timezone="Asia/Seoul",
    enable_utc=False,

    # 워커가 일정 횟수 태스크를 처리한 뒤 자식 프로세스를 재시작하여 메모리 누수를 방지한다.
    # PaddleOCR/EasyOCR은 모델을 메모리에 들고 있어 장시간 누수 가능성이 있다.
    worker_max_tasks_per_child=200,
)


import app.worker.tasks  # noqa: F401