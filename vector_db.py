from milvus_haystack import MilvusDocumentStore

from config import MILVUS

#  MilvusDocumentStore 설정
document_store = MilvusDocumentStore(
    collection_name="information_db",
    connection_args={"uri": "http://" + MILVUS + ":19530"},
    consistency_level="Session",
    drop_old=False,
    #primary_field="id",
    text_field="content",
    vector_field="embed",
    index_params={
        "index_type": "GPU_CAGRA",
        "metric_type": "L2",
        "params": {
            "intermediate_graph_degree": 64,
            "graph_degree": 32,
            "build_algo": "NN_DESCENT",
            "cache_dataset_on_device": "false"
        }
    }
)








