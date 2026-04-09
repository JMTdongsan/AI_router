import json
import os
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

from insert2DB import insert_data

PENDING_INGEST_PATH = Path(os.getenv("PENDING_INGEST_PATH", "data/pending_naver_ingest.jsonl"))
PROCESSED_INGEST_PATH = Path(os.getenv("PROCESSED_INGEST_PATH", "data/processed_naver_ingest.jsonl"))


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _is_valid_summary(summary: str) -> bool:
    if not isinstance(summary, str):
        return False
    stripped = summary.strip()
    if not stripped:
        return False
    if stripped.lower() == "advertisement":
        return False
    return True


def build_records(keyword: str, summaries: List[str], urls: List[str]) -> List[dict]:
    if len(summaries) != len(urls):
        raise ValueError("summaries와 urls의 길이가 다릅니다.")

    created_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    records = []
    for summary, url in zip(summaries, urls):
        records.append(
            {
                "keyword": keyword,
                "summary": summary,
                "source_url": url,
                "created_at": created_at,
            }
        )
    return records


def append_records(records: Iterable[dict], path: Path = PENDING_INGEST_PATH) -> int:
    _ensure_parent(path)
    count = 0
    with path.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def stage_search_results(keyword: str, summaries: List[str], urls: List[str]) -> Tuple[int, Path]:
    records = build_records(keyword, summaries, urls)
    saved = append_records(records)
    return saved, PENDING_INGEST_PATH


def load_pending_records(path: Path = PENDING_INGEST_PATH) -> List[dict]:
    if not path.exists():
        return []

    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _split_valid_records(records: List[dict]) -> Tuple[List[dict], List[dict]]:
    valid = []
    skipped = []
    for record in records:
        if _is_valid_summary(record.get("summary")) and record.get("source_url"):
            valid.append(record)
        else:
            skipped.append(record)
    return valid, skipped


def archive_records(records: Iterable[dict], path: Path = PROCESSED_INGEST_PATH) -> int:
    _ensure_parent(path)
    count = 0
    with path.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def upload_staged_data() -> dict:
    records = load_pending_records()
    if not records:
        return {"uploaded": 0, "skipped": 0, "pending_path": str(PENDING_INGEST_PATH)}

    valid_records, skipped_records = _split_valid_records(records)
    uploaded = 0
    if valid_records:
        summaries = [record["summary"] for record in valid_records]
        urls = [record["source_url"] for record in valid_records]
        insert_data(summaries, urls)
        uploaded = len(valid_records)

    archive_records(records)
    _ensure_parent(PENDING_INGEST_PATH)
    PENDING_INGEST_PATH.write_text("", encoding="utf-8")

    return {
        "uploaded": uploaded,
        "skipped": len(skipped_records),
        "pending_path": str(PENDING_INGEST_PATH),
        "processed_path": str(PROCESSED_INGEST_PATH),
    }
