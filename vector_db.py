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


def retrieval_status():
    return {
        "qdrant": {
            "url": QDRANT_URL,
            "api_key_configured": bool(QDRANT_API_KEY),
            "collection_name": retrieval_config.collection_name,
        },
        "retrieval_config": {
            "path": QDRANT_RETRIEVAL_CONFIG or None,
            "package_dir": CHUNKING_DOCS_PACKAGE_DIR or retrieval_config.package_dir,
            "exported_package_dir": retrieval_config.package_dir,
            "bm25_tokens_path": retrieval_config.bm25_tokens_path,
        },
        "vectors": {
            "active": retrieval_config.vector_names,
            "skipped": retrieval_config.skipped_vector_names,
            "query_encoders": retrieval_config.query_encoders,
            "active_query_encoder": retrieval_config.active_query_encoder,
        },
        "retrieval": {
            "top_k": retrieval_config.top_k,
            "score_threshold": retrieval_config.score_threshold,
            "fusion_weights": retrieval_config.fusion_weights,
        },
        "bm25": {
            "enabled": bm25_index is not None,
            "path": str(bm25_tokens_path) if bm25_tokens_path else None,
            "doc_count": bm25_index.doc_count if bm25_index else 0,
            "avg_doc_length": bm25_index.avg_doc_length if bm25_index else 0.0,
            "tokenizer": retrieval_config.lexical_tokenizer,
        },
    }
