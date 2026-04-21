#!/bin/sh
set -e

# SERVICE_TYPE 환경변수로 서비스 역할 분기
# docker-compose.yml의 각 서비스에서 environment로 지정
case "$SERVICE_TYPE" in
    app)
        # FastAPI (uvicorn) + JupyterLab 동시 실행
        uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        exec uv run jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser --notebook-dir=/app/notebooks
        ;;
    worker)
        # Celery 워커 (embedding 큐 전용)
        exec uv run celery -A app.worker.celery_app worker --loglevel=info -Q embedding --concurrency=2
        ;;
    flower)
        # Celery Flower 모니터링 UI
        exec uv run celery -A app.worker.celery_app flower --port=5555
        ;;
    beat)
        # Celery 주기 작업 스케줄러 (필요 시 사용)
        exec uv run celery -A app.worker.celery_app beat --loglevel=info
        ;;
    *)
        echo "ERROR: SERVICE_TYPE is not set or invalid: '$SERVICE_TYPE'"
        echo "Valid values: app | worker | flower | beat"
        exit 1
        ;;
esac