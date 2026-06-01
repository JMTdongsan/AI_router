from config import QDRANT_VECTOR_NAMES
from embed_api import get_embed
from vector_db import retriever


question = "도로 정비 사업이 뭐지?"
embedding = get_embed(question)[0]
result = retriever.run(query_embedding=embedding)

print("Qdrant vectors:", QDRANT_VECTOR_NAMES)
for document in result["documents"]:
    print(document.meta.get("score"), document.content[:200])
