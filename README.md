# 유사 이미지 검색 API

이 프로젝트는 FastAPI를 기반으로 한 유사 이미지 검색 API로, 사용자가 업로드한 이미지와 유사한 이미지를 벡터 데이터베이스에서 검색하여 제공합니다.

YOLO 객체 검출 모델과 Qdrant 벡터 데이터베이스를 활용하여 정확하고 빠른 이미지 검색이 가능하며, 다양한 이미지 형식을 지원합니다.

## 🚀 프로젝트 개요

- **이미지 분석 파이프라인**:
  - **객체 검출**: YOLO 모델을 사용한 정확한 객체 인식 및 위치 파악
  - **이미지 전처리**: 검출된 객체를 기반으로 한 정확한 크롭 및 정규화
  - **특징 추출**: 크롭된 이미지에서 고유한 특징을 추출하는 임베딩 생성
- **이미지 검색 시스템**:
  - **벡터 검색**: Qdrant 벡터 데이터베이스를 활용한 고속 유사도 검색
  - **실시간 처리**: 대규모 이미지 데이터셋에서도 빠른 검색 성능 보장
- **모듈식 아키텍처**: 확장 가능한 구조로 다양한 AI 기능을 쉽게 추가할 수 있는 유연한 설계
- **실시간 API**: 비동기 처리를 통한 고성능 API 엔드포인트 제공
- **개발자 친화적 환경**: Jupyter 노트북을 활용한 실험 환경과 자동화된 API 문서 제공


## 🛠️ 기술 스택

- **Python**: 3.11
- **FastAPI**: 0.110.0
- **데이터베이스**:
  - Qdrant
- **개발 도구**:
  - Jupyter Notebook


## 📸 실행 화면
### 샘플 이미지
![샘플 이미지](storage/screenshots/image_search.png)
![샘플 이미지](storage/screenshots/image_search2.png)


## 🏗️ 프로젝트 구조

```text
fastapi-agent/
├── app/                           # 애플리케이션 핵심 코드
│   ├── api/                       # API 라우터 정의
│   │   ├── v1/                    # API 버전 1
│   │   ├── __init__.py            # API 패키지 초기화
│   │   └── router_collector.py    # 라우터 자동 수집 및 등록
│   └── domain/                    # 도메인 로직
│       ├── agent/                 # 에이전트 관련 로직
│       ├── modules/               # 도메인 모듈
│       ├── services/              # 비즈니스 로직 서비스
│       └── state/                 # 애플리케이션 상태 관리
│
├── common/                        # 공통 유틸리티
│   ├── constants/                 # 상수 정의
│   │   └── http_code.py           # HTTP 상태 코드
│   ├── exceptions/                # 예외 처리
│   │   └── handlers.py            # 예외 핸들러
│   └── utils/                     # 유틸리티 함수
│       ├── image.py               # 이미지 처리 유틸리티
│       ├── response.py            # API 응답 포맷팅
│       ├── router.py              # 라우터 유틸리티
│       └── storage.py             # 파일 저장소 유틸리티
│
├── config/                        # 설정 파일
│   ├── __init__.py
│   ├── embedding_model.py         # 임베딩 모델 설정
│   └── settings.py               # 애플리케이션 설정
│
├── notebooks/                     # Jupyter 노트북
│   └── ...                       # 실험 및 분석용 노트북
│
├── storage/                      # 정적 파일 저장소
│   ├── images/                   # 이미지 저장소
│   │   └── fruits/               # 예제 이미지 (과일)
│   └── screenshots/              # 스크린샷 저장소
│
├── .env                          # 환경 변수 설정
├── docker-compose.yml            # Docker Compose 설정
├── main.py                      # 애플리케이션 진입점
├── requirements.txt             # 파이썬 의존성 목록
└── README.md                    # 프로젝트 문서