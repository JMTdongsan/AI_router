from config import QDRANT_API_KEY, QDRANT_COLLECTION, QDRANT_URL
from qdrant_retriever import build_qdrant_client


client = build_qdrant_client(url=QDRANT_URL, api_key=QDRANT_API_KEY)
collections = client.get_collections().collections
collection_names = [collection.name for collection in collections]
print("Qdrant collections:", collection_names)

if QDRANT_COLLECTION not in collection_names:
    raise Exception(f"'{QDRANT_COLLECTION}' Qdrant collection does not exist.")
