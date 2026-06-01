from config import QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL
from qdrant_retriever import build_qdrant_client


if __name__ == "__main__":
    client = build_qdrant_client(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    print("Qdrant collections:", collection_names)
    if QDRANT_COLLECTION not in collection_names:
        raise SystemExit(
            f"Qdrant collection '{QDRANT_COLLECTION}' does not exist. "
            "Create and upsert it with chunking-docs qdrant-upsert-package first."
        )
    info = client.get_collection(collection_name=QDRANT_COLLECTION)
    print(f"Qdrant collection '{QDRANT_COLLECTION}' is ready.")
    print(info)
