# AI Router

AI Router는 RAG(Retrieval Augmented Generation) 기반 질의응답 시스템이다.
Flask API를 통해 질의를 받고, Milvus 벡터 데이터베이스와 vLLM을 사용해 문서를 검색하고 응답을 생성한다.
또한 네이버 검색 크롤링과 국토교통부 용어 검색 도구를 통해 런타임 정보를 보강할 수 있다.

이 브랜치는 다음 운영 목표를 기준으로 정리되어 있다.

- Docker Compose 기반 배포
- vLLM 모델명 환경변수화
- Milvus 데이터 경로 분리
- Prometheus + Grafana 모니터링 기본 구성

## 주요 기능

- `/api/ask_rag`: 벡터 검색 기반 RAG 질의응답
- `/api/ask`: Function Calling 기반 질의응답 경로(현재 로직 추가 정리가 필요함)
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
- `vector_db.py`: Milvus 연결 및 설정
- `crawler.py`: 네이버 검색 크롤링 및 요약
- `llm_tool.py`: LLM tool 정의

### Docker Compose 구성

- `api`: Flask + Gunicorn API 서버
- `vllm`: OpenAI-compatible vLLM 서버
- `etcd`: Milvus 메타데이터 저장소
- `minio`: Milvus 오브젝트 스토리지
- `milvus`: 벡터 데이터베이스
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

#### Milvus / Storage

- `MILVUS_PORT`: Milvus gRPC 포트
- `MILVUS_HTTP_PORT`: Milvus HTTP 포트
- `MILVUS_DATA_PATH`: Milvus 데이터 저장 경로
- `ETCD_DATA_PATH`: etcd 데이터 저장 경로
- `MINIO_DATA_PATH`: MinIO 데이터 저장 경로
- `MINIO_ROOT_USER`: MinIO 계정
- `MINIO_ROOT_PASSWORD`: MinIO 비밀번호

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
docker compose logs -f milvus
```

### 3. DB 초기화

Milvus 컬렉션이 아직 생성되지 않았다면 다음 명령으로 초기화한다.

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
  - Milvus `/metrics`
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

### 1. `/api/ask` 경로

현재 `/api/ask` 경로는 구조상 추가 정리가 필요한 상태다.
Docker 구성은 포함되어 있지만, Function Calling 파이프라인 자체는 별도 보완이 필요하다.

### 2. 임베딩 서버

이번 Docker 스택에는 임베딩 서버를 포함하지 않았다.
따라서 `.env`의 `EMBED_URL`이 실제 접근 가능한 서버를 가리키도록 설정해야 한다.

### 3. vLLM GPU 환경

vLLM 컨테이너는 GPU 환경이 준비되지 않으면 정상 기동하지 않을 수 있다.
특히 다음을 반드시 확인해야 한다.

- NVIDIA 드라이버 설치 여부
- NVIDIA Container Toolkit 설치 여부
- 모델 다운로드 권한 및 Hugging Face 토큰 설정 여부

### 4. 메트릭 이름 차이

Grafana 대시보드는 기본적인 메트릭 구성을 기준으로 작성했다.
실제 vLLM / Milvus 이미지 버전에 따라 일부 메트릭 이름이 다를 수 있으므로, 운영 환경 기동 후 대시보드 쿼리 튜닝이 필요할 수 있다.

## 트러블슈팅

### API가 기동하지 않는 경우

```bash
docker compose logs -f api
```

다음을 우선 확인한다.

- `EMBED_URL` 접근 가능 여부
- `VLLM_URL` 또는 `vllm` 서비스 상태
- `MILVUS` 연결 가능 여부

### vLLM이 기동하지 않는 경우

```bash
docker compose logs -f vllm
```

다음을 확인한다.

- GPU 장치 노출 여부
- 모델명 오타 여부
- Hugging Face token 필요 여부
- 메모리 부족 여부

### Milvus가 준비되지 않는 경우

```bash
docker compose logs -f milvus
docker compose logs -f etcd
docker compose logs -f minio
```

Milvus는 etcd / minio 의존성이 정상이어야 한다.

## 향후 개선 과제

- `/api/ask` 엔드포인트 정합성 보정
- DB 초기화 자동화 여부 결정
- embedding server compose 포함 여부 검토
- Grafana 대시보드 쿼리 튜닝
- Alert rule 추가
- README 운영 가이드 추가 고도화
