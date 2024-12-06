from milvus_haystack import MilvusEmbeddingRetriever

from vector_db import document_store
from embed_api import get_embed

prompt_template = """You're an AI assistant. Respond efficiently using these steps:
                        1. Use provided context and your knowledge first.
                        2. If insufficient, use functions in order:
                           a. Dictionary Search (fast, cheap)
                           b. Online Search (comprehensive, costly)
                        3. Stop searching once you have enough info.
                        4. Check search history to avoid repetition.
                        5. Cite sources used.
                        6. Prioritize accuracy and relevance.
                        Efficiency is key. Minimize function calls.
                        History : {history}
                        Query: {query}
                        Documents:{doc}
                         Answer:
                         """


def fcall_rag(question):
    embed = get_embed(question)
    retriever = MilvusEmbeddingRetriever(
        document_store=document_store,
        top_k=5
    )
    result = retriever.run(query_embedding=embed[0])
    documents = result["documents"]
    # 검색된 문서 활용
    doc_cont = [doc.content for doc in documents]
    print(doc_cont)
    return doc_cont

if __name__ == '__main__':
    print(fcall_rag(" 도로 정비 공사가 뭐지"))




