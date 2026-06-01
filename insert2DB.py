import uuid
from typing import List

from qdrant_client.models import Distance, PointStruct, VectorParams

from config import QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL
from embed_api import get_embed
from qdrant_retriever import build_qdrant_client


def insert_data(summarized: List[str], urls: List[str]):
    if len(summarized) != len(urls):
        raise ValueError("summarized와 urls의 길이가 다릅니다.")

    embeddings = get_embed(summarized)
    if not embeddings:
        return {"inserted": 0}

    client = build_qdrant_client(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    ensure_collection(client, len(embeddings[0]))
    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"ai-router:{url}:{text}")),
            vector={"text_dense": embedding},
            payload={
                "doc_id": "ai-router-crawl",
                "chunk_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"ai-router-chunk:{url}:{text}")),
                "text": text,
                "content": text,
                "source_url": url,
                "source": "naver_crawl",
            },
        )
        for embedding, text, url in zip(embeddings, summarized, urls)
    ]
    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    return {"inserted": len(points)}


def ensure_collection(client, vector_size: int):
    collections = client.get_collections().collections
    if any(collection.name == QDRANT_COLLECTION for collection in collections):
        return
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config={
            "text_dense": VectorParams(size=vector_size, distance=Distance.COSINE),
        },
    )
