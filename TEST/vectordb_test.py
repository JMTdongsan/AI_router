from pymilvus import connections
from pymilvus.orm import utility

from config import MILVUS

# Milvus 서버에 연결 (기본적으로 로컬호스트의 19530 포트를 사용)
connections.connect(alias="default", host=MILVUS , port="19530")

# 연결 상태 확인
if connections.has_connection("default"):
    print("Milvus에 연결가능")
else:
    raise ConnectionError("Milvus 연결불가")


collections = utility.list_collections()
print("컬렉션 목록:", collections)

# 원하는 컬렉션이 있는지 조회
collection_name = "inforamion_db"
if not utility.has_collection(collection_name):
        raise Exception(f"'{collection_name}' 컬렉션이 존재하지 않습니다.")




