# AI Router

AI Router는 RAG(Retrieval Augmented Generation) 기반 질의응답 시스템이다.
Flask API를 통해 질의를 받고, Qdrant 벡터 데이터베이스와 vLLM을 사용해 문서를 검색하고 응답을 생성한다.
또한 네이버 검색 크롤링과 국토교통부 용어 검색 도구를 통해 런타임 정보를 보강할 수 있다.

이 브랜치는 다음 운영 목표를 기준으로 정리되어 있다.

- Docker Compose 기반 배포
- vLLM 모델명 환경변수화
- Qdrant 데이터 경로 분리
- Prometheus + Grafana 모니터링 기본 구성

## 역할 경계

이 디렉터리는 RAG 시스템만 담당한다.
웹 백엔드와 프론트엔드는 상위 디렉터리의 `backend/`, `frontend/`에서 분리해 관리한다.

## 주요 기능

- `/api/ask_rag`: 벡터 검색 기반 RAG 질의응답
- `/api/rag/config`: 현재 로드된 Qdrant, BM25, retrieval config 설정 확인
- `/api/crawl`: 키워드 기반 네이버 검색/크롤링 및 요약
- `/healthz`: API 헬스체크
- `/metrics`: Prometheus 메트릭 엔드포인트

## 시스템 구성

### 애플리케이션 구성

- `router.py`: Flask API 진입점
- `ragpipeline.py`: Haystack 기반 RAG 파이프라인
- `func_rag_pipeline.py`: Function Calling 기반 질의응답 관련 모듈
- `embed_api.py`: 외부 임베딩 서버 호출
- `send_llm.py`: vLLM OpenAI-compatible API 호출
- `vector_db.py`: Qdrant 연결 및 검색 설정
- `qdrant_retriever.py`: Qdrant named-vector 검색과 fusion score 결합
- `crawler.py`: 네이버 검색 크롤링 및 요약
- `llm_tool.py`: LLM tool 정의

### Docker Compose 구성

- `api`: Flask + Gunicorn API 서버
- `vllm`: OpenAI-compatible vLLM 서버
- `qdrant`: 벡터 데이터베이스
- `prometheus`: 메트릭 수집
- `grafana`: 대시보드 시각화
- `node-exporter`: 호스트 메트릭 수집
- `cadvisor`: 컨테이너 메트릭 수집

## 프로젝트 구조

```text
AI_router/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── config.py
├── router.py
├── ragpipeline.py
├── func_rag_pipeline.py
├── vector_db.py
├── qdrant_retriever.py
├── embed_api.py
├── send_llm.py
├── llm_tool.py
├── crawler.py
├── insert2DB.py
├── DB_create.py
├── token_calc.py
├── word_definition.py
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       └── provisioning/
├── assets/
└── TEST/
```

## 사전 준비 사항

### 필수 요구사항

- Docker Engine
- Docker Compose
- NVIDIA GPU 환경(vLLM 사용 시)
- NVIDIA Container Toolkit(vLLM 컨테이너에서 GPU 사용 시)
- 외부 임베딩 서버 또는 별도 임베딩 서비스

### 권장 확인 사항

```bash
docker compose version
docker info
nvidia-smi
```

## 환경 설정

`.env.example`을 기준으로 `.env` 파일을 생성한다.

```bash
cp .env.example .env
```

### 주요 환경 변수

#### API

- `APP_PORT`: API 포트
- `MAX_TOKENS`: 입력 truncate 기준 토큰 수

#### vLLM

- `VLLM_MODEL_NAME`: vLLM이 서빙할 모델명
- `VLLM_IMAGE`: 사용할 vLLM 이미지
- `VLLM_PORT`: vLLM 포트
- `VLLM_GPU_MEMORY_UTILIZATION`: GPU 메모리 사용 비율
- `VLLM_MAX_MODEL_LEN`: 최대 컨텍스트 길이
- `VLLM_API_KEY`: OpenAI-compatible API key
- `DEFAULT_MODEL`: 애플리케이션이 호출할 기본 모델명
- `HUGGING_FACE_HUB_TOKEN`: Hugging Face 모델 다운로드 토큰

#### Embedding

- `EMBED_URL`: 외부 임베딩 서버 엔드포인트
- `RAG_QUERY_ENCODER`: 현재 임베딩 서버가 제공하는 query encoder 이름. 비워두면 retrieval config의 `text_dense` query encoder를 기준으로 삼는다.

#### Qdrant / Storage

- `QDRANT_URL`: API 컨테이너가 접근할 Qdrant URL
- `QDRANT_HTTP_PORT`: 호스트에 노출할 Qdrant HTTP 포트
- `QDRANT_GRPC_PORT`: 호스트에 노출할 Qdrant gRPC 포트
- `QDRANT_DATA_PATH`: Qdrant 데이터 저장 경로
- `QDRANT_COLLECTION`: RAG 검색에 사용할 컬렉션명. `QDRANT_RETRIEVAL_CONFIG`에 `collection_name`이 있으면 그 값이 우선된다.
- `QDRANT_VECTOR_NAMES`: 검색할 named vector 목록
- `QDRANT_RETRIEVAL_CONFIG`: `chunking_docs`가 export한 retrieval config JSON 경로
- `CHUNKING_DOCS_PACKAGE_DIR`: `bm25_tokens.json`을 포함한 `chunking_docs` package 경로
- `BM25_TOKENS_PATH`: package 경로와 별도로 지정할 BM25 token manifest 경로
- `RAG_TOP_K`: 검색 결과 개수
- `RAG_SCORE_THRESHOLD`: Qdrant score threshold

#### Monitoring

- `PROMETHEUS_PORT`: Prometheus 포트
- `PROMETHEUS_DATA_PATH`: Prometheus 데이터 경로
- `GRAFANA_PORT`: Grafana 포트
- `GRAFANA_DATA_PATH`: Grafana 데이터 경로
- `GRAFANA_ADMIN_USER`: Grafana 관리자 계정
- `GRAFANA_ADMIN_PASSWORD`: Grafana 관리자 비밀번호
- `NODE_EXPORTER_PORT`: node-exporter 포트
- `CADVISOR_PORT`: cAdvisor 포트

## 실행 방법

### 1. Compose 빌드 및 실행

```bash
docker compose up --build -d
```

### 2. 로그 확인

```bash
docker compose logs -f api
docker compose logs -f vllm
docker compose logs -f qdrant
```

### 3. Qdrant 컬렉션 확인

Qdrant 컬렉션은 `chunking_docs qdrant-upsert-package`로 생성하고 업서트한다.
BM25 lexical 검색은 `QDRANT_RETRIEVAL_CONFIG`의 `bm25_tokens_path` 또는 같은 디렉터리의 `bm25_tokens.json`을 자동으로 사용하며, 다른 위치를 써야 하면 `CHUNKING_DOCS_PACKAGE_DIR` 또는 `BM25_TOKENS_PATH`로 지정한다. BM25 결과는 Qdrant named-vector 결과와 reciprocal rank fusion으로 결합된다.
Config에 `query_encoders`가 있으면 AI_router는 현재 `RAG_QUERY_ENCODER`와 다른 encoder를 요구하는 vector를 건너뛴다. 예를 들어 텍스트 임베딩 서버만 연결된 상태에서는 `image_dense`가 자동 제외되고, `text_dense`, `caption_dense`, `object_dense`처럼 같은 텍스트 query encoder를 쓰는 vector만 조회된다.
AI_router에서는 다음 명령으로 현재 설정된 컬렉션이 준비되어 있는지만 확인한다.

```bash
docker compose exec api python DB_create.py
```

## API 사용 예시

### Health check

```bash
curl http://localhost:5000/healthz
```

### RAG 질의응답

```bash
curl "http://localhost:5000/api/ask_rag?question=도로정비사업이란?"
```

### RAG 설정 확인

```bash
curl http://localhost:5000/api/rag/config
```

### 크롤링 및 저장

```bash
curl "http://localhost:5000/api/crawl?keyword=도로정비사업"
```

## 모니터링

### Prometheus

- URL: `http://localhost:9090`
- 수집 대상:
  - API `/metrics`
  - vLLM `/metrics`
  - Qdrant `/metrics`
  - node-exporter
  - cAdvisor

### Grafana

- URL: `http://localhost:3000`
- 기본 계정: `.env`의 `GRAFANA_ADMIN_USER`
- 기본 비밀번호: `.env`의 `GRAFANA_ADMIN_PASSWORD`

Grafana는 기동 시 다음 항목을 자동 적용한다.

- Prometheus datasource
- `AI Router Overview` 대시보드

### 기본 대시보드 포함 항목

- API request rate
- API p95 latency
- API 5xx rate
- route별 request rate
- route별 latency
- container CPU usage
- container memory usage
- host CPU / memory utilization
- host network throughput
- vLLM GPU cache usage
- vLLM token throughput

## 운영 시 주의 사항

### 1. 임베딩 서버

이번 Docker 스택에는 임베딩 서버를 포함하지 않았다.
따라서 `.env`의 `EMBED_URL`이 실제 접근 가능한 서버를 가리키도록 설정해야 한다.

### 2. vLLM GPU 환경

vLLM 컨테이너는 GPU 환경이 준비되지 않으면 정상 기동하지 않을 수 있다.
특히 다음을 반드시 확인해야 한다.

- NVIDIA 드라이버 설치 여부
- NVIDIA Container Toolkit 설치 여부
- 모델 다운로드 권한 및 Hugging Face 토큰 설정 여부

### 3. 메트릭 이름 차이

Grafana 대시보드는 기본적인 메트릭 구성을 기준으로 작성했다.
실제 vLLM / Qdrant 이미지 버전에 따라 일부 메트릭 이름이 다를 수 있으므로, 운영 환경 기동 후 대시보드 쿼리 튜닝이 필요할 수 있다.

## 트러블슈팅

### API가 기동하지 않는 경우

```bash
docker compose logs -f api
```

다음을 우선 확인한다.

- `EMBED_URL` 접근 가능 여부
- `VLLM_URL` 또는 `vllm` 서비스 상태
- `QDRANT_URL` 연결 가능 여부

### vLLM이 기동하지 않는 경우

```bash
docker compose logs -f vllm
```

다음을 확인한다.

- GPU 장치 노출 여부
- 모델명 오타 여부
- Hugging Face token 필요 여부
- 메모리 부족 여부

### Qdrant가 준비되지 않는 경우

```bash
docker compose logs -f qdrant
```

Qdrant collection이 없으면 `chunking_docs qdrant-upsert-package`로 패키지 산출물을 먼저 업서트한다.

## 향후 개선 과제

- retrieval config 파일을 컨테이너에 mount하는 운영 방식 확정
- embedding server compose 포함 여부 검토
- Grafana 대시보드 쿼리 튜닝
- Alert rule 추가
- README 운영 가이드 추가 고도화
