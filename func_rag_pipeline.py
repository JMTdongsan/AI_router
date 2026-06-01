from embed_api import get_embed
from vector_db import retriever

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
    embedding = get_embed(question)[0]
    result = retriever.run(query_embedding=embedding)
    documents = result["documents"]
    doc_cont = [doc.content for doc in documents]
    print(doc_cont)
    return doc_cont


if __name__ == "__main__":
    print(fcall_rag(" 도로 정비 공사가 뭐지"))



