import os
from openai import OpenAI

VLLM_URL = os.getenv("VLLM_URL", "http://localhost:8000/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "token-abc123")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct"))

EMBED_URL = os.getenv("EMBED_URL", "http://localhost:8080/embed")
MILVUS = os.getenv("MILVUS", "localhost")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))

client = OpenAI(base_url=VLLM_URL, api_key=VLLM_API_KEY)
model_name = DEFAULT_MODEL
