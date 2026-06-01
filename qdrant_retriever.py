from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List

from haystack import Document, component

TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9_]+")
CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")


@dataclass(frozen=True)
class RetrievalConfig:
    collection_name: str
    package_dir: str | None
    bm25_tokens_path: str | None
    vector_names: list[str]
    top_k: int
    fusion_weights: dict[str, float]
    lexical_tokenizer: dict[str, Any]
    score_threshold: float | None = None


@dataclass(frozen=True)
class RankedHit:
    item_id: str
    rank: int
    score: float
    source: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class BM25Record:
    chunk_id: str
    tokens: list[str]


class BM25ManifestIndex:
    def __init__(self, path: str | Path, tokenizer_config: dict[str, Any] | None = None):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        self.tokenizer_config = dict(tokenizer_config or payload.get("tokenizer") or {})
        self.records = [
            BM25Record(
                chunk_id=str(row["chunk_id"]),
                tokens=[str(token) for token in row.get("tokens", [])],
            )
            for row in payload.get("chunks", [])
            if row.get("chunk_id")
        ]
        self.doc_count = len(self.records)
        self.doc_lengths = [len(record.tokens) for record in self.records]
        self.avg_doc_length = (
            sum(self.doc_lengths) / self.doc_count if self.doc_count else 0.0
        )
        self.term_frequencies = [Counter(record.tokens) for record in self.records]
        document_frequencies: Counter[str] = Counter()
        for record in self.records:
            document_frequencies.update(set(record.tokens))
        self.idf = {
            term: max(
                0.0,
                math.log((self.doc_count - frequency + 0.5) / (frequency + 0.5) + 1.0),
            )
            for term, frequency in document_frequencies.items()
        }

    def search(self, query: str, top_k: int) -> list[RankedHit]:
        query_tokens = lexical_tokenize(query, self.tokenizer_config)
        if not query_tokens or not self.records:
            return []
        query_token_set = set(query_tokens)
        scored = []
        for index, record in enumerate(self.records):
            score = self.score(query_tokens, index)
            score += lexical_overlap(query_token_set, record.tokens)
            if score > 0:
                scored.append((index, score))
        ranked = sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]
        return [
            RankedHit(
                item_id=self.records[index].chunk_id,
                rank=rank,
                score=float(score),
                source="bm25",
                payload={"chunk_id": self.records[index].chunk_id},
            )
            for rank, (index, score) in enumerate(ranked, start=1)
        ]

    def score(self, query_tokens: list[str], record_index: int) -> float:
        k1 = 1.5
        b = 0.75
        frequencies = self.term_frequencies[record_index]
        doc_length = self.doc_lengths[record_index]
        score = 0.0
        for term in query_tokens:
            frequency = frequencies.get(term, 0)
            if frequency <= 0:
                continue
            denominator = frequency + k1 * (
                1.0 - b + b * doc_length / max(self.avg_doc_length, 1.0)
            )
            score += self.idf.get(term, 0.0) * frequency * (k1 + 1.0) / denominator
        return score


class NullBM25Index:
    def search(self, query: str, top_k: int) -> list[RankedHit]:
        return []


def load_retrieval_config(
    path: str | Path | None,
    collection_name: str,
    vector_names: Iterable[str],
    top_k: int,
    score_threshold: float | None = None,
) -> RetrievalConfig:
    if not path:
        vector_name_list = list(vector_names)
        return RetrievalConfig(
            collection_name=collection_name,
            package_dir=None,
            bm25_tokens_path=None,
            vector_names=vector_name_list,
            top_k=top_k,
            fusion_weights={f"qdrant:{name}": 1.0 for name in vector_name_list},
            lexical_tokenizer={},
            score_threshold=score_threshold,
        )

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return RetrievalConfig(
        collection_name=str(payload.get("collection_name") or collection_name),
        package_dir=optional_string(payload.get("package_dir")),
        bm25_tokens_path=optional_string(payload.get("bm25_tokens_path")),
        vector_names=list(payload.get("vector_names") or vector_names),
        top_k=int(payload.get("top_k") or top_k),
        fusion_weights={
            str(source): float(weight)
            for source, weight in (payload.get("fusion_weights") or {}).items()
        },
        lexical_tokenizer=dict(payload.get("lexical_tokenizer") or {}),
        score_threshold=score_threshold,
    )


def optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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
        bm25_index: BM25ManifestIndex | None = None,
    ):
        self.client = client
        self.collection_name = collection_name
        self.vector_names = vector_names
        self.top_k = top_k
        self.fusion_weights = fusion_weights or {}
        self.score_threshold = score_threshold
        self.bm25_index = bm25_index or NullBM25Index()

    @component.output_types(documents=List[Document])
    def run(self, query_embedding: List[float], query: str = ""):
        candidate_k = max(self.top_k * 3, 20)
        result_sets: list[list[RankedHit]] = []
        payloads: dict[str, dict[str, Any]] = {}
        for vector_name in self.vector_names:
            hits = self.qdrant_hits(
                vector_name=vector_name,
                query_embedding=query_embedding,
                top_k=candidate_k,
            )
            result_sets.append(hits)
            for hit in hits:
                payloads.setdefault(hit.item_id, hit.payload)

        bm25_hits = self.bm25_index.search(query, top_k=candidate_k) if query else []
        result_sets.append(bm25_hits)
        for item_id, payload in fetch_payloads_by_chunk_ids(
            self.client,
            self.collection_name,
            [hit.item_id for hit in bm25_hits if hit.item_id not in payloads],
        ).items():
            payloads[item_id] = payload

        fused = reciprocal_rank_fusion(
            result_sets,
            top_k=self.top_k,
            source_weights=self.fusion_weights,
        )
        return {
            "documents": [
                document_from_fused(item_id, score, sources, payloads.get(item_id, {}))
                for item_id, score, sources in fused
            ]
        }

    def qdrant_hits(
        self,
        vector_name: str,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RankedHit]:
        hits = []
        for rank, point in enumerate(
            query_points(
                self.client,
                collection_name=self.collection_name,
                vector_name=vector_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=self.score_threshold,
            ),
            start=1,
        ):
            payload = point_payload(point)
            item_id = result_key(point, payload)
            if not item_id:
                continue
            hits.append(
                RankedHit(
                    item_id=item_id,
                    rank=rank,
                    score=float(getattr(point, "score", 0.0) or 0.0),
                    source=f"qdrant:{vector_name}",
                    payload=payload,
                )
            )
        return hits


def reciprocal_rank_fusion(
    result_sets: list[list[RankedHit]],
    top_k: int,
    source_weights: dict[str, float] | None = None,
    k: int = 60,
) -> list[tuple[str, float, list[str]]]:
    scores: dict[str, float] = defaultdict(float)
    sources: dict[str, set[str]] = defaultdict(set)
    source_weights = source_weights or {}
    for hits in result_sets:
        for hit in hits:
            weight = fusion_source_weight(hit.source, source_weights)
            if weight <= 0:
                continue
            scores[hit.item_id] += weight / (k + max(hit.rank, 1))
            sources[hit.item_id].add(hit.source)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
    return [(item_id, score, sorted(sources[item_id])) for item_id, score in ranked]


def fusion_source_weight(source: str, source_weights: dict[str, float]) -> float:
    if source in source_weights:
        return source_weights[source]
    family = source.split(":", 1)[0]
    if family in source_weights:
        return source_weights[family]
    return 1.0


def build_qdrant_client(url: str, api_key: str | None = None):
    try:
        from qdrant_client import QdrantClient
    except ImportError as exc:
        raise RuntimeError("Install qdrant-client to use the Qdrant RAG retriever.") from exc
    return QdrantClient(url=url, api_key=api_key)


def default_bm25_tokens_path(
    explicit_path: str | Path | None = None,
    package_dir: str | Path | None = None,
    retrieval_config_path: str | Path | None = None,
) -> Path | None:
    if explicit_path:
        return Path(explicit_path)
    if retrieval_config_path and package_dir is None:
        try:
            config = json.loads(Path(retrieval_config_path).read_text(encoding="utf-8"))
        except OSError:
            config = {}
        config_bm25_path = optional_string(config.get("bm25_tokens_path"))
        if config_bm25_path:
            path = Path(config_bm25_path)
            if not path.is_absolute():
                path = Path(retrieval_config_path).resolve().parent / path.name
            if path.exists():
                return path
        package_dir = optional_string(config.get("package_dir"))
    if package_dir:
        path = Path(package_dir) / "bm25_tokens.json"
        return path if path.exists() else None
    if retrieval_config_path:
        path = Path(retrieval_config_path).resolve().parent / "bm25_tokens.json"
        return path if path.exists() else None
    return None


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


def fetch_payloads_by_chunk_ids(
    client: Any,
    collection_name: str,
    chunk_ids: list[str],
) -> dict[str, dict[str, Any]]:
    chunk_ids = sorted(set(chunk_ids))
    if not chunk_ids or not hasattr(client, "scroll"):
        return {}
    try:
        from qdrant_client.models import FieldCondition, Filter, MatchAny
    except ImportError:
        return {}
    response, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter=Filter(
            must=[FieldCondition(key="chunk_id", match=MatchAny(any=chunk_ids))]
        ),
        limit=len(chunk_ids),
        with_payload=True,
        with_vectors=False,
    )
    payloads = {}
    for point in response:
        payload = point_payload(point)
        chunk_id = str(payload.get("chunk_id") or "")
        if chunk_id:
            payloads[chunk_id] = payload
    return payloads


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


def document_from_fused(
    item_id: str,
    score: float,
    sources: list[str],
    payload: dict[str, Any],
) -> Document:
    payload = dict(payload)
    if not payload:
        payload["chunk_id"] = item_id
    content = document_content(payload)
    meta = {
        key: value
        for key, value in payload.items()
        if key not in {"text", "content", "caption", "ocr_text", "vlm_summary"}
    }
    meta["score"] = score
    meta["retrieval_sources"] = sources
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


def lexical_tokenize(text: str, config: dict[str, Any]) -> list[str]:
    strategy = str(config.get("strategy") or "mixed")
    lowercase = bool(config.get("lowercase", True))
    min_n = int(config.get("min_n") or 2)
    max_n = int(config.get("max_n") or 4)
    cjk_only = bool(config.get("ngram_cjk_only", True))
    tokens: list[str] = []
    if strategy in {"word", "mixed"}:
        tokens.extend(word_tokens(text, lowercase=lowercase))
    if strategy in {"char_ngram", "mixed"}:
        tokens.extend(
            char_ngram_tokens(
                text,
                min_n=min_n,
                max_n=max_n,
                lowercase=lowercase,
                cjk_only=cjk_only,
            )
        )
    if bool(config.get("deduplicate", False)):
        return stable_unique(tokens)
    return tokens


def word_tokens(text: str, lowercase: bool = True) -> list[str]:
    tokens = TOKEN_RE.findall(text)
    return [token.lower() for token in tokens] if lowercase else tokens


def char_ngram_tokens(
    text: str,
    min_n: int,
    max_n: int,
    lowercase: bool = True,
    cjk_only: bool = True,
) -> list[str]:
    if min_n <= 0 or max_n < min_n:
        return []
    ngrams = []
    for token in word_tokens(text, lowercase=lowercase):
        if cjk_only and not CJK_RE.search(token):
            continue
        upper = min(max_n, len(token))
        for size in range(min_n, upper + 1):
            for start in range(0, len(token) - size + 1):
                ngrams.append(token[start : start + size])
    return ngrams


def stable_unique(tokens: list[str]) -> list[str]:
    seen = set()
    selected = []
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        selected.append(token)
    return selected


def lexical_overlap(query_tokens: set[str], document_tokens: list[str]) -> float:
    if not query_tokens:
        return 0.0
    return len(query_tokens.intersection(document_tokens)) / len(query_tokens)
