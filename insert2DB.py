import uuid
from haystack import  Document
from typing import List

from pymilvus import connections, Collection

from config import MILVUS
from vector_db import document_store
from embed_api import get_embed



# 데이터 삽입 함수 정의
def insert_data(summarized: List[str], urls: List[str]):
    if len(summarized) != len(urls):
        raise ValueError("summarized와 urls의 길이가 다릅니다.")
    conn = connections.connect("default", host=MILVUS, port="19530")
    collection = Collection("information_db")

    print("Before Number of documents:", collection.num_entities)
    """documents = [
        Document(content=summarized[i], meta={'source_url': urls[i]}, id=None)
        for i in range(len(summarized))
        for doc, embedding in zip(documents, embeddings):
        doc.embedding = embedding
    ]"""
    embeddings = get_embed(summarized)
    entities = [
        {
            "embed": embedding,
            "content": text,
            "source_url": url
        }
        for embedding, text, url in zip(embeddings, summarized, urls)
    ]

    # 데이터 삽입
    collection.insert(entities)

    # 변경사항 적용
    collection.flush()
    print("After Number of documents:", collection.num_entities)


