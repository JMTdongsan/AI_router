from config import (
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_RETRIEVAL_CONFIG,
    QDRANT_URL,
    QDRANT_VECTOR_NAMES,
    RAG_SCORE_THRESHOLD,
    RAG_TOP_K,
)
from qdrant_retriever import (
    QdrantHybridRetriever,
    build_qdrant_client,
    load_retrieval_config,
)


retrieval_config = load_retrieval_config(
    path=QDRANT_RETRIEVAL_CONFIG,
    collection_name=QDRANT_COLLECTION,
    vector_names=QDRANT_VECTOR_NAMES,
    top_k=RAG_TOP_K,
    score_threshold=RAG_SCORE_THRESHOLD,
)

document_store = build_qdrant_client(url=QDRANT_URL, api_key=QDRANT_API_KEY)
retriever = QdrantHybridRetriever(
    client=document_store,
    collection_name=retrieval_config.collection_name,
    vector_names=retrieval_config.vector_names,
    top_k=retrieval_config.top_k,
    fusion_weights=retrieval_config.fusion_weights,
    score_threshold=retrieval_config.score_threshold,
)
