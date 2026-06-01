from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List

from haystack import Document, component


@dataclass(frozen=True)
class RetrievalConfig:
    collection_name: str
    vector_names: list[str]
    top_k: int
    fusion_weights: dict[str, float]
    score_threshold: float | None = None


def load_retrieval_config(
    path: str | Path | None,
    collection_name: str,
    vector_names: Iterable[str],
    top_k: int,
    score_threshold: float | None = None,
) -> RetrievalConfig:
    if not path:
        return RetrievalConfig(
            collection_name=collection_name,
            vector_names=list(vector_names),
            top_k=top_k,
            fusion_weights={f"qdrant:{name}": 1.0 for name in vector_names},
            score_threshold=score_threshold,
        )

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return RetrievalConfig(
        collection_name=collection_name,
        vector_names=list(payload.get("vector_names") or vector_names),
        top_k=int(payload.get("top_k") or top_k),
        fusion_weights={
            str(source): float(weight)
            for source, weight in (payload.get("fusion_weights") or {}).items()
        },
        score_threshold=score_threshold,
    )


@component
class QdrantHybridRetriever:
    def __init__(
        self,
        client: Any,
        collection_name: str,
        vector_names: list[str],
        top_k: int = 5,
        fusion_weights: dict[str, float] | None = None,
        score_threshold: float | None = None,
    ):
        self.client = client
        self.collection_name = collection_name
        self.vector_names = vector_names
        self.top_k = top_k
        self.fusion_weights = fusion_weights or {}
        self.score_threshold = score_threshold

    @component.output_types(documents=List[Document])
    def run(self, query_embedding: List[float]):
        scored: dict[str, dict[str, Any]] = {}
        for vector_name in self.vector_names:
            weight = self.vector_weight(vector_name)
            if weight <= 0:
                continue
            for point in query_points(
                self.client,
                collection_name=self.collection_name,
                vector_name=vector_name,
                query_vector=query_embedding,
                limit=self.top_k,
                score_threshold=self.score_threshold,
            ):
                payload = point_payload(point)
                key = result_key(point, payload)
                row = scored.setdefault(
                    key,
                    {
                        "score": 0.0,
                        "payload": payload,
                        "sources": [],
                    },
                )
                row["score"] += float(getattr(point, "score", 0.0) or 0.0) * weight
                row["sources"].append(
                    {
                        "vector_name": vector_name,
                        "score": float(getattr(point, "score", 0.0) or 0.0),
                        "weight": weight,
                    }
                )

        rows = sorted(scored.values(), key=lambda row: row["score"], reverse=True)
        return {"documents": [document_from_row(row) for row in rows[: self.top_k]]}

    def vector_weight(self, vector_name: str) -> float:
        return float(
            self.fusion_weights.get(f"qdrant:{vector_name}")
            or self.fusion_weights.get(vector_name)
            or self.fusion_weights.get("qdrant")
            or 1.0
        )


def build_qdrant_client(url: str, api_key: str | None = None):
    try:
        from qdrant_client import QdrantClient
    except ImportError as exc:
        raise RuntimeError("Install qdrant-client to use the Qdrant RAG retriever.") from exc
    return QdrantClient(url=url, api_key=api_key)


def query_points(
    client: Any,
    collection_name: str,
    vector_name: str,
    query_vector: list[float],
    limit: int,
    score_threshold: float | None = None,
):
    if hasattr(client, "query_points"):
        response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            using=vector_name,
            limit=limit,
            with_payload=True,
            score_threshold=score_threshold,
        )
        return list(getattr(response, "points", response))
    return client.search(
        collection_name=collection_name,
        query_vector=(vector_name, query_vector),
        limit=limit,
        with_payload=True,
        score_threshold=score_threshold,
    )


def point_payload(point: Any) -> dict[str, Any]:
    payload = getattr(point, "payload", None) or {}
    return payload if isinstance(payload, dict) else {}


def result_key(point: Any, payload: dict[str, Any]) -> str:
    return str(
        payload.get("chunk_id")
        or payload.get("asset_id")
        or payload.get("triple_id")
        or getattr(point, "id", "")
    )


def document_from_row(row: dict[str, Any]) -> Document:
    payload = dict(row["payload"])
    content = document_content(payload)
    meta = {
        key: value
        for key, value in payload.items()
        if key not in {"text", "content", "caption", "ocr_text", "vlm_summary"}
    }
    meta["score"] = row["score"]
    meta["retrieval_sources"] = row["sources"]
    return Document(content=content, meta=meta)


def document_content(payload: dict[str, Any]) -> str:
    parts = [
        payload.get("text"),
        payload.get("content"),
        payload.get("caption"),
        payload.get("ocr_text"),
        payload.get("vlm_summary"),
        payload.get("summary"),
        payload.get("object_text"),
    ]
    if payload.get("subject") and payload.get("predicate") and payload.get("object"):
        parts.append(f"{payload['subject']} {payload['predicate']} {payload['object']}")
    return "\n".join(str(part).strip() for part in parts if str(part or "").strip())
