from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection
)
from config import MILVUS

if __name__ == '__main__':
    # Milvus에 연결
    conn = connections.connect("default", host=MILVUS, port="19530")

    # 필드 정의
    id_field = FieldSchema(name="id",dtype=DataType.INT64,is_primary=True,auto_id=True)
    content_field = FieldSchema(name="content",dtype=DataType.VARCHAR,max_length=1000)
    source_url_field = FieldSchema(name="source_url",dtype=DataType.VARCHAR,max_length=100)
    embed_field = FieldSchema(name="embed",dtype=DataType.FLOAT_VECTOR,dim=1024)

    # 컬렉션 스키마 정의
    schema = CollectionSchema(
        fields=[id_field, content_field, source_url_field, embed_field],
        description="Content with embeddings and source URLs"
    )
    #컬렉션이 존재하면 삭제하고 생성함
    collection_name = "information_db"
    try:
        collection = Collection(name=collection_name)
        collection.drop()
        print(f"컬렉션 '{collection_name}'이 삭제")
    except:
        pass
    collection = Collection(name=collection_name,schema=schema)
    print("현재생성된 스키마",collection.schema)
    # GPU_CAGRA 인덱스 생성
    index_params = {
        "index_type": "GPU_CAGRA",
        "metric_type": "L2",   # 벡터 간 거리 계산을 위한 메트릭 타입 (유클리드 거리)
        "params": {
            "intermediate_graph_degree": 64,  # 그래프의 중간 차수
            "graph_degree": 32,               # 그래프의 최종 차수
            "build_algo": "NN_DESCENT",       # 그래프 생성 알고리즘
            "cache_dataset_on_device": "false"  # GPU 메모리에 원본 데이터셋 캐싱 여부
        }
    }
    '''
    GPT왈
    intermediate_graph_degree 클 수록 정확도 향상 -> 빌드시간 증가
    graph_degree 클 수록 정확도 향상 -> 메모리 사용량 빌드 시간 증가
    쓰기 비중이 낮지 않다고 가정 (30프로 이상) 만약에 이것보다 낮다면 좀 더 숫자를 올려서 정확도 향상을 도모
    NN_DESCENT 대신에 IVF_PQ가 조금 더 느리지만 성능향상 도모 가능 쓰기 작업이 낮을 경우 고려
    cache_dataset_on_device 는 GPU 메모리가 넉넉하지 않는 상황을 고려
    search_width:  검색 시 그래프의 진입점 수를 결정합니다.
    기본 값: 자동 설정 (빈 값)
    조정 가이드: 정확도 향상이 필요한 경우 값을 높입니다. 검색 성능(속도) 향상이 필요한 경우 값을 낮춥니다. 
    itopk_size:검색 시 중간 결과의 크기를 결정합니다.
    기본 값: 자동 설정 (빈 값)
    조정 가이드: 정확도 향상이 필요한 경우 값을 높입니다. 검색 성능(속도) 향상이 필요한 경우 값을 낮춥니다. 단, top_k보다 크거나 같아야 합니다.
    '''
    # 인덱스 생성
    collection.create_index(field_name="embed",index_params=index_params,using="default",index_name="embed_gpu_cagra_index")
    collection.load()