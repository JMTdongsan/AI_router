# 시스템 아키텍처 다이어그램

```mermaid
flowchart TB
    subgraph Client["클라이언트"]
        USER[("사용자")]
    end

    subgraph API["Flask API Server (router.py)"]
        ASK_RAG["/api/ask_rag<br/>RAG 질의응답"]
        CRAWL["/api/crawl<br/>크롤링+저장"]
    end

    subgraph Core["핵심 파이프라인"]
        RAG["RAG Pipeline<br/>(ragpipeline.py)"]
        CRAWLER["Crawler<br/>(crawler.py)"]
    end

    subgraph Components["핵심 컴포넌트"]
        EMBEDDER["Embedder<br/>(embed_api.py)"]
        VECTOR_DB["Vector DB<br/>(vector_db.py)"]
        QDRANT_RETRIEVER["Qdrant Retriever<br/>(qdrant_retriever.py)"]
        LLM_CLIENT["LLM Client<br/>(send_llm.py)"]
        TOOLS["Tools<br/>(llm_tool.py)"]
    end

    subgraph External["외부 서비스"]
        TEI[("TEI Server<br/>:8080")]
        QDRANT[("Qdrant<br/>:6333")]
        VLLM[("vLLM<br/>:8000")]
        NAVER[("네이버 검색")]
        MOLIT[("국토교통부<br/>용어사전")]
    end

    USER --> ASK_RAG
    USER --> CRAWL

    ASK_RAG --> RAG
    CRAWL --> CRAWLER

    RAG --> EMBEDDER
    RAG --> VECTOR_DB
    VECTOR_DB --> QDRANT_RETRIEVER
    RAG --> LLM_CLIENT

    CRAWLER --> LLM_CLIENT
    CRAWLER --> EMBEDDER
    CRAWLER --> VECTOR_DB

    TOOLS --> LLM_CLIENT
    TOOLS --> NAVER
    TOOLS --> MOLIT

    EMBEDDER --> TEI
    QDRANT_RETRIEVER --> QDRANT
    LLM_CLIENT --> VLLM

    style Client fill:#e1f5fe
    style API fill:#fff3e0
    style Core fill:#f3e5f5
    style Components fill:#e8f5e9
    style External fill:#fce4ec
```
