import os
from openai import OpenAI

VLLM_URL = os.getenv("VLLM_URL", "http://localhost:8000/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "token-abc123")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct"))

EMBED_URL = os.getenv("EMBED_URL", "http://localhost:8080/embed")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "seoul_plan")
CHUNKING_DOCS_PACKAGE_DIR = os.getenv("CHUNKING_DOCS_PACKAGE_DIR", "")
BM25_TOKENS_PATH = os.getenv("BM25_TOKENS_PATH", "")
QDRANT_VECTOR_NAMES = [
    name.strip()
    for name in os.getenv("QDRANT_VECTOR_NAMES", "text_dense").split(",")
    if name.strip()
]
QDRANT_RETRIEVAL_CONFIG = os.getenv("QDRANT_RETRIEVAL_CONFIG", "")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_SCORE_THRESHOLD = os.getenv("RAG_SCORE_THRESHOLD")
RAG_SCORE_THRESHOLD = float(RAG_SCORE_THRESHOLD) if RAG_SCORE_THRESHOLD else None
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))

client = OpenAI(base_url=VLLM_URL, api_key=VLLM_API_KEY)
model_name = DEFAULT_MODEL
