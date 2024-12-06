from ragpipeline import rag_pipeline

if __name__ == '__main__':
    question = "도로 정비 사업이 뭐지?"
    results = rag_pipeline.run(
        {
            "text_embedder": {"text": question},
            "prompt_builder": {"query": question},
        }
    )
    print('RAG answer:', results["generator"]["replies"][0])