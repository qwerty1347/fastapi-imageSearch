# 유사 이미지 검색 API

FastAPI 기반 유사 이미지 검색 서비스. 사용자가 업로드한 이미지에서 객체를 검출하고, CLIP 으로 임베딩한 뒤 Qdrant 에서 코사인 유사도 상위 5개 이미지를 반환합니다.

> YOLOv8 객체 검출 → CLIP `ViT-L-14` 768차원 임베딩 → Qdrant 유사도 검색을 단일 API 로 묶었습니다. 무거운 모델은 `lru_cache` + lifespan 워밍업으로 프로세스당 1회만 로드하고, 동기 추론은 `asyncio.to_thread()` 로 워커 스레드에 격리해 이벤트 루프 블로킹을 방지합니다. 데이터셋 적재는 Celery 워커가 백그라운드에서 처리하며, `uuid5` 결정적 ID 로 중복 적재를 막아 재실행에 안전합니다.

---

## 목차

1. [핵심 특징](#핵심-특징)
2. [아키텍처](#아키텍처)
3. [기술 스택](#기술-스택)
4. [프로젝트 구조](#프로젝트-구조)
5. [API 명세](#api-명세)
6. [도메인 상세](#도메인-상세)
7. [임베딩 파이프라인 (Celery)](#임베딩-파이프라인-celery)
8. [Celery 워커 정책](#celery-워커-정책)
9. [남은 제한 사항 & 다음 단계](#남은-제한-사항--다음-단계)

---

## 핵심 특징

| 영역 | 내용 |
|---|---|
| **객체 검출** | YOLOv8(`yolov8n-oiv7.pt`, Open Images v7 사전학습)로 입력 이미지에서 가장 신뢰도 높은 객체 1개를 추출하고 bounding box 산출 |
| **이미지 임베딩** | SentenceTransformer CLIP `ViT-L-14` (768차원, Cosine 거리)로 크롭된 객체를 벡터화 |
| **벡터 검색** | Qdrant 벡터 DB의 `fruits` 컬렉션에서 코사인 유사도 상위 5개 이미지 반환 |
| **백그라운드 임베딩** | Celery + Redis 로 데이터셋 이미지의 대량 임베딩을 비동기 처리 (`embed_fruit_images` 태스크) |
| **의존성 주입 / 모델 싱글톤** | `@lru_cache`로 Qdrant·CLIP·YOLO 를 프로세스당 1회만 로드. FastAPI 는 `Depends` 로, Celery 워커는 동일 캐시 함수 직접 호출 |
| **lifespan 워밍업** | 앱 부팅 시 모델/클라이언트 미리 로드 → 첫 요청 지연 제거. 종료 시 Qdrant 클라이언트 graceful close |

---

## 아키텍처
![Architecture](storage/screenshots/architecture.png)

---

### 유사 이미지 검색 흐름 (`POST /api/v1/image/`)

```
[Client]        [FastAPI]              [Storage]         [Qdrant]
   │               │                      │                 │
   │ POST /image   │                      │                 │
   ├──────────────►│                      │                 │
   │               │ validate file        │                 │
   │               │ save temp            ├───────────────► │
   │               │                      │                 │
   │               │ asyncio.to_thread()  │                 │
   │               │   ├─ YOLO detect     │                 │
   │               │   │   → bbox         │                 │
   │               │   ├─ size/ratio 검증 │                 │
   │               │   └─ CLIP encode     │                 │
   │               │       → 768-dim      │                 │
   │               │                      │                 │
   │               │ Qdrant search        ├───────────────► │
   │               │ (top_k=5, cosine)    │                 │
   │               │                      │ ◄───────────────┤
   │               │ delete temp          │                 │
   │               │                      │                 │
   │ {images[...]} │                      │                 │
   │◄──────────────┤
```

> YOLO · CLIP · Qdrant 호출은 모두 sync. async 라우터에서 그대로 부르면 이벤트 루프가 멈추므로 **각 단계마다 `asyncio.to_thread()` 로 격리**해 동시 요청 처리 능력을 유지합니다.

---

### 데이터셋 임베딩 흐름 (Celery 백그라운드)

```
[Celery Worker]          [Storage]            [Qdrant]
       │                    │                    │
       │ embed_fruit_       │                    │
       │  images()          │                    │
       │ ──────────────────►                     │
       │  scan images       │                    │
       │  (storage/images/  │                    │
       │   fruits/)         │                    │
       │                    │                    │
       │ for each image:    │                    │
       │   YOLO detect → bbox                    │
       │   size/ratio 검증                       │
       │   CLIP encode → 768-dim                 │
       │   PointStruct(                          │
       │     id=uuid5(NAMESPACE_URL,             │
       │              image_path.name),          │
       │     vector=[...],                       │
       │     payload={image_url, bbox}           │
       │   )                                     │
       │                                         │
       │ qdrant.upsert_points(                   │
       │   collection_name="fruits",             │
       │   points=[...]                          │
       │ ) ─────────────────────────────────────►│
       │                                         │
```

> `uuid5` 결정적 ID 덕분에 같은 파일이 재실행되어도 같은 row 를 upsert 하므로 **중복 적재 없이 멱등**. Celery 의 `acks_late` + `reject_on_worker_lost` 와 정합.

---

### 모델 싱글톤 패턴 (`lru_cache`)

```
   app/core/dependencies/common.py
        ┌────────────────────────────────────┐
        │  @lru_cache(maxsize=1)             │
        │  def get_qdrant_client()           │
        │  def get_embedding_model()         │
        │  def get_yolo_model()              │
        └────────┬───────────────────────────┘
                 │
       ┌─────────┴───────────────────────────┐
       ▼                                     ▼
   [FastAPI 라우터]                    [Celery 워커]
   Depends(get_fruit_search_service)   직접 호출
       │                                     │
       ▼                                     ▼
   서비스 인스턴스 ◄────────────── 같은 모델 인스턴스 공유
   (요청마다 new but 모델은 공유)         (프로세스당 1회 로드)
```

`@lru_cache(maxsize=1)` 으로 무거운 모델(CLIP/YOLO)과 클라이언트(Qdrant)를 **프로세스당 단 1회만 로드**. FastAPI 라우터와 Celery 워커가 같은 캐시 함수를 호출해 일관성 확보.

---

## 기술 스택

### Runtime
- **Python** 3.11+
- **FastAPI** 0.136.0
- **Uvicorn[standard]** 0.44.0 (uvloop, httptools, watchfiles)
- **Pydantic** 2.13.2 / **pydantic-settings** 2.13.1
- **python-multipart** (multipart/form-data)

### 머신러닝
- **YOLOv8** (객체 검출, `yolov8n-oiv7.pt` Open Images v7 사전학습)
- **ultralytics** 8.4.40 (YOLOv8 추론 엔진)
- **SentenceTransformer** 5.4.1 + **CLIP ViT-L-14** (768차원 임베딩)
- **torch** 2.11.0 (YOLO/CLIP 백엔드)

### 벡터 검색
- **qdrant-client** 1.17.1 (gRPC/HTTP)
- **Qdrant** 서버 v1.15.4 (Cosine distance)

### 작업 큐
- **Celery** 5.6.3
- **Redis** 7.4.0 (broker + result backend)
- **Flower** 2.0.1 (포트 5555, 모니터링 대시보드)

### 이미지 처리
- **Pillow** 12.2.0 (crop, RGB 변환)
- **NumPy** 2.4.4

### Dev / 노트북
- **Jupyter Notebook** 7.5.5 + **ipywidgets** 8.1.8
- **pytest** + **pytest-asyncio**
- **uv** (`uv.lock` 기반 재현 가능한 설치)

---

## 프로젝트 구조

```text
fastapi-imageSearch/
├── app/
│   ├── api/
│   │   ├── __init__.py                 # /api 루트 + pkgutil 자동 수집
│   │   └── v1/
│   │       ├── __init__.py             # /v1 + 하위 라우터 자동 등록
│   │       └── image_search/
│   │           ├── __init__.py
│   │           └── router.py           # POST /api/v1/image/
│   ├── core/
│   │   ├── config.py                   # pydantic-settings 환경 설정
│   │   ├── logging.py                  # setup_logging
│   │   ├── dependencies/
│   │   │   ├── common.py               # get_qdrant_client / get_embedding_model / get_yolo_model (lru_cache)
│   │   │   └── image_search.py         # FruitPointService / FruitSearchService 팩토리
│   │   ├── exceptions/
│   │   │   ├── custom.py               # BusinessException
│   │   │   └── handler.py              # 전역 예외 → 통일 응답 봉투
│   │   └── utils/
│   │       ├── image.py                # 이미지 비율 계산 (get_image_ratio)
│   │       ├── response.py             # success_response / error_response
│   │       └── url.py                  # 정적 이미지 URL 변환 (convert_to_static_image_url)
│   ├── infrastructure/
│   │   ├── storage/
│   │   │   └── image.py                # save_image_to_temp / get_fruit_images
│   │   └── vectordb/
│   │       └── qdrant.py               # Qdrant 클라이언트 래퍼 (client 주입형)
│   ├── schemas/
│   │   ├── common.py                   # SuccessResponse / ErrorResponse 제네릭
│   │   └── image_search/
│   │       └── response.py             # ImageSearchResponse
│   ├── services/
│   │   └── fruit/
│   │       ├── point.py                # FruitPointService (YOLO 검출 / CLIP 임베딩 / PointStruct 생성)
│   │       └── search.py               # FruitSearchService (유사 이미지 검색 흐름, asyncio.to_thread)
│   ├── worker/
│   │   ├── celery_app.py               # Celery 앱 (queue: embedding)
│   │   └── tasks/
│   │       ├── __init__.py
│   │       ├── add.py                  # 샘플 태스크
│   │       └── embedding.py            # embed_fruit_images (lru_cache 캐시 함수 직접 호출)
│   └── main.py                         # FastAPI 진입점 (lifespan 워밍업, CORS, 예외 등록)
├── config/
│   └── embedding_model.py              # CLIP 모델 메타 (ViT-B/32, ViT-L/14)
├── storage/
│   ├── images/fruits/                  # 임베딩 대상 데이터셋
│   └── screenshots/                    # README 스크린샷
├── notebooks/                          # Jupyter 탐색 노트북
├── tests/                              # (현재 비어 있음)
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── yolov8n-oiv7.pt                     # YOLO 가중치 (Open Images v7)
└── README.md
```

---

## API 명세

모든 엔드포인트는 `/api/v1` 프리픽스 아래에 있습니다.

### 이미지 검색

| Method | Path | 설명 |
|---|---|---|
| `POST` | `/api/v1/image/` | 업로드 이미지 → YOLO 검출 → CLIP 임베딩 → Qdrant 검색 |

**요청** (`multipart/form-data`):
- `file` — 이미지 파일 (필수)

**응답** (성공 200):
```json
{
  "code": 200,
  "data": [
    {
      "id": "8f1d-uuid5...",
      "image_path": "/static/images/fruits/apple_01.jpg",
      "bbox": [12, 34, 220, 240],
      "score": 0.8721
    },
    {
      "id": "...",
      "image_path": "/static/images/fruits/apple_07.jpg",
      "bbox": [...],
      "score": 0.8412
    }
  ]
}
```

**에러 응답** (422 UNPROCESSABLE_ENTITY):

- 검출된 객체가 없음
- bounding box 가 너무 작음 (`min_size=10px`, `min_ratio=0.01`)
- 파일 형식 오류

```json
{
  "code": 422,
  "message": "Validation Error",
  "errors": [
    { "detail": "custom_point_data is None" }
  ]
}
```

---

## 도메인 상세

### 1) 검색 서비스 (`FruitSearchService.get_similarity_images`)

업로드 → 임시 저장 → YOLO → 검증 → CLIP → Qdrant → 응답 흐름을 담당. 모든 동기 호출이 `asyncio.to_thread()` 로 격리됨:

```python
async def get_similarity_images(self, file: UploadFile):
    uploaded_image_path = await save_image_to_temp(file)
    try:
        detected_objects = await asyncio.to_thread(
            self.fruit_point_service.detect_objects_from_image,
            uploaded_image_path
        )
        custom_point_data = await asyncio.to_thread(
            self.fruit_point_service.create_point_data,
            uploaded_image_path, detected_objects
        )
        if custom_point_data is None:
            raise BusinessException(code=422, message="custom_point_data is None")

        vector = await asyncio.to_thread(
            self.fruit_point_service.embedding_model.encode,
            custom_point_data['crop']
        )
        response = await asyncio.to_thread(
            self.fruit_point_service.qdrant.find_points,
            collection_name="fruits", query=vector, limit=5,
        )
        return [{"id": p.id, "image_path": ..., "bbox": ..., "score": float(p.score)} for p in response]
    finally:
        uploaded_image_path.unlink(missing_ok=True)
```

핵심:

- **`finally` 의 임시 파일 정리** — 예외가 나도 업로드 임시 파일이 누적되지 않음
- **`asyncio.to_thread()` 4번** — YOLO / point_data 생성 / CLIP encode / Qdrant query 각각 격리

### 2) 포인트 서비스 (`FruitPointService`)

YOLO 검출 결과를 검증·크롭하고 CLIP 임베딩으로 `PointStruct` 를 만드는 책임:

- **`detect_objects_from_image(image_path)`** — `YOLO(image_path, conf=0.1)[0]` 결과 반환
- **`create_point_data(image_path, detected_objects)`** — 가장 신뢰도 높은 객체 1개 선택, 크기·비율 검증, crop 반환
  - `min_size=10px` / `min_ratio=0.01` 미달 → `None` 반환 (검색 거부)
- **`build_points(image_path, custom_point_data)`** — `uuid5` 로 결정적 ID 생성, vector / payload 조립
- **`embed_fruit_images()`** — 데이터셋 디렉터리 전체를 순회하며 위 흐름으로 적재

### 3) Qdrant 래퍼 (`infrastructure/vectordb/qdrant.py`)

`Qdrant(client: QdrantClient)` 시그니처. 내부에서 `config` 를 직접 참조하지 않고 **클라이언트를 주입** 받음 → 테스트 시 mock 주입 용이.

`get_qdrant(client = Depends(get_qdrant_client))` 형태로 의존성 트리에서 자연스럽게 조립됨.

### 4) lifespan 워밍업 (`app/main.py`)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    get_qdrant_client()     # ← lru_cache 첫 호출 (Qdrant client 연결)
    get_embedding_model()   # ← CLIP ViT-L-14 모델 메모리 로드
    get_yolo_model()        # ← YOLOv8 가중치 로드
    yield
    get_qdrant_client().close()
```

앱 부팅 시점에 무거운 자원을 모두 적재 → 첫 요청부터 즉시 응답. 종료 시 Qdrant 클라이언트 명시적 close.

### 5) 객체 크기 검증의 의도

너무 작은 객체(점·반점 수준)는 CLIP 임베딩에서 노이즈가 되어 무관한 이미지를 매칭하기 쉽습니다. `min_size=10px` + `min_ratio=0.01` 로 사전 거부 → 검색 결과 품질 보호.

---

## 임베딩 파이프라인 (Celery)

`app/worker/tasks/embedding.py` 의 `embed_fruit_images` 태스크가 `storage/images/fruits/` 디렉터리를 일괄 임베딩합니다.

### 처리 흐름

1. **이미지 스캔**: `get_fruit_images()` 로 디렉터리 내 모든 이미지 경로 수집
2. **YOLO 객체 검출**: 가장 신뢰도 높은 객체 1개 선택 (`conf=0.1`)
3. **크기·비율 검증**: 임계치 미달 시 skip
4. **CLIP 임베딩**: 크롭한 영역을 768차원 벡터로 변환
5. **PointStruct 생성**:
   ```python
   PointStruct(
       id=str(uuid.uuid5(uuid.NAMESPACE_URL, image_path.name)),
       vector=[...],
       payload={
           "image": convert_to_static_image_url(image_path),
           "bbox": [x1, y1, x2, y2],
       }
   )
   ```
6. **Qdrant 적재**: `fruits` 컬렉션에 `upsert_points`

### 멱등성 — `uuid5` 결정적 ID

`uuid.uuid5(NAMESPACE_URL, image_path.name)` 으로 ID 를 만들면 같은 파일은 항상 같은 UUID 가 나옵니다. → 재실행해도 같은 row 를 upsert(덮어쓰기) 하므로 중복 적재 없음.

이 멱등성이 Celery 의 `acks_late` + `reject_on_worker_lost` 정책과 정합해, 워커 장애로 잡이 재할당되어도 안전합니다.

### 실행 (Flower 또는 CLI)

```bash
# Flower 웹 UI 에서 태스크 호출
# http://localhost:5555

# 또는 CLI
celery -A app.worker.celery_app call app.worker.tasks.embedding.embed_fruit_images
```

> **사전 조건**: Qdrant `fruits` 컬렉션은 다음 설정으로 사전 생성되어야 합니다.
> ```python
> vectors_config={"size": 768, "distance": "Cosine"}
> ```

---

## Celery 워커 정책

`app/worker/celery_app.py` 의 핵심 설정:

```python
celery.conf.update(
    worker_prefetch_multiplier=1,            # GPU/무거운 추론은 한 번에 1개만 선점
    task_acks_late=True,                     # 잡 끝난 뒤 ack → 워커 장애 시 재할당
    task_reject_on_worker_lost=True,         # 워커 사망 시 명시적 reject
    task_time_limit=60 * 30,                 # hard 30분
    task_soft_time_limit=60 * 25,            # soft 25분 (cleanup 기회)
    worker_max_tasks_per_child=200,          # 200 잡마다 자식 재시작 (모델 메모리 누수 방어)
    task_track_started=True,                 # PENDING ↔ STARTED 구분
    task_serializer="json",
    result_serializer="json",
    timezone="Asia/Seoul",
)
```

### 정책별 의도

| 정책 | 왜 이렇게 |
|---|---|
| `worker_prefetch_multiplier=1` | YOLO·CLIP 추론은 GPU/CPU bound. 기본 4 는 한 워커가 4개를 선점해 다른 워커가 놀게 됨. 1로 두면 사용 가능한 워커에 골고루 분배 |
| `acks_late` + `reject_on_worker_lost` | 멱등 임베딩(uuid5 결정적 ID) 전제로 안전. 워커가 SIGKILL/OOM 되면 broker 가 같은 잡 재할당 |
| `task_time_limit=30min` | 데이터셋 일괄 임베딩이 오래 걸릴 수 있어 30분 여유. 멈춘 잡이 워커를 영구 점유하는 사고 차단 |
| `task_soft_time_limit=25min` | hard 보다 5분 짧게. soft 초과 시 `SoftTimeLimitExceeded` 예외 → cleanup 가능 |
| `worker_max_tasks_per_child=200` | CLIP/YOLO 모델 메모리가 누적되는 것을 200 잡마다 자식 프로세스 재시작으로 방어 |
| `task_track_started=True` | Flower 에서 PENDING(대기) ↔ STARTED(실행중) 구분 가능 |

---

## 남은 제한 사항 & 다음 단계

### 현재 제한 사항

| 항목 | 상태 | 설명 |
|---|---|---|
| **Qdrant 컬렉션 자동 생성** | ❌ | `fruits` 컬렉션을 사전 생성해야 함. lifespan 에서 `collection_exists` 확인 + `create_collection` 호출 보강 필요 |
| **응답 스키마 일치성** | ⚠️ | `response_model=ImageSearchResponse` 와 실제 반환값(`list[dict]`) 타입 불일치 |
| **검색 도메인이 `fruits` 컬렉션 고정** | ⚠️ | 서비스명·컬렉션 키가 "fruit" 으로 하드코딩. 다른 도메인 확장 시 추상화 필요 |
| **테스트 커버리지** | ❌ | `tests/` 디렉터리 비어 있음 |
| **Qdrant 래퍼 추상화** | ⚠️ | 현재는 얇은 래퍼. 도메인 리포지토리로 승격하거나 직접 사용으로 단순화 검토 |
| **모델 가중치 관리** | ⚠️ | `yolov8n-oiv7.pt` 가 repo 에 함께 커밋. 대용량 가중치는 외부 스토리지/Volume 분리 권장 |
| **객체 검출 정책** | ⚠️ | `conf=0.1`, `min_size=10`, `min_ratio=0.01` 같은 임계치가 코드에 하드코딩 |

### 권장 다음 단계

1. **lifespan 보강**: `client.collection_exists("fruits")` → 없으면 `create_collection(size=768, distance="Cosine")` 자동 생성
2. **검색 도메인 추상화**: `FruitSearchService` → `ImageSearchService(collection: str)` 식으로 컬렉션을 인자화. 신규 도메인(예: `cars`) 추가가 클래스 1개로 끝나게
3. **응답 스키마 정정**: `ImageSearchResponse` 타입 정렬, 라우터 응답이 스키마와 정확히 일치하도록
4. **테스트 작성**: 라우터·서비스 단위 테스트 (`app.dependency_overrides` 활용). 모델은 mock 으로 대체해 외부 자원 없이 실행
5. **임계치 설정 외부화**: `min_size` · `min_ratio` · `conf` · `top_k` 를 `pydantic-settings` 환경변수로 분리
6. **모델 가중치 분리**: `yolov8n-oiv7.pt` 를 git LFS / S3 / 마운트 볼륨으로 옮겨 repo 경량화
7. **Celery retry 정책 정교화**: Qdrant 5xx / 네트워크 타임아웃만 선별 재시도 (`autoretry_for` + 지수 백오프 + 지터)

---

## 실행 화면

### 샘플 이미지

![샘플 이미지](storage/screenshots/image_search.png)

![샘플 이미지](storage/screenshots/image_search2.png)