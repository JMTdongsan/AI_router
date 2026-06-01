from config import (
    BM25_TOKENS_PATH,
    CHUNKING_DOCS_PACKAGE_DIR,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_RETRIEVAL_CONFIG,
    QDRANT_URL,
    QDRANT_VECTOR_NAMES,
    RAG_QUERY_ENCODER,
    RAG_SCORE_THRESHOLD,
    RAG_TOP_K,
)
from qdrant_retriever import (
    BM25ManifestIndex,
    QdrantHybridRetriever,
    build_qdrant_client,
    default_bm25_tokens_path,
    load_retrieval_config,
)


retrieval_config = load_retrieval_config(
    path=QDRANT_RETRIEVAL_CONFIG,
    collection_name=QDRANT_COLLECTION,
    vector_names=QDRANT_VECTOR_NAMES,
    top_k=RAG_TOP_K,
    score_threshold=RAG_SCORE_THRESHOLD,
    query_encoder=RAG_QUERY_ENCODER,
)

document_store = build_qdrant_client(url=QDRANT_URL, api_key=QDRANT_API_KEY)
bm25_tokens_path = default_bm25_tokens_path(
    explicit_path=BM25_TOKENS_PATH or retrieval_config.bm25_tokens_path,
    package_dir=CHUNKING_DOCS_PACKAGE_DIR or retrieval_config.package_dir,
    retrieval_config_path=QDRANT_RETRIEVAL_CONFIG,
)
bm25_index = (
    BM25ManifestIndex(
        bm25_tokens_path,
        tokenizer_config=retrieval_config.lexical_tokenizer,
    )
    if bm25_tokens_path
    else None
)
retriever = QdrantHybridRetriever(
    client=document_store,
    collection_name=retrieval_config.collection_name,
    vector_names=retrieval_config.vector_names,
    top_k=retrieval_config.top_k,
    fusion_weights=retrieval_config.fusion_weights,
    score_threshold=retrieval_config.score_threshold,
    bm25_index=bm25_index,
)
