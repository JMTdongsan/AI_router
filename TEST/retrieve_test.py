

from config import MILVUS
from pymilvus import connections, db

from pymilvus import MilvusClient


client = MilvusClient(
    uri=f"http://{MILVUS}:19530"
)

conn = connections.connect(host=MILVUS, port=19530)

res = client.search(
    collection_name="information_db",  # target collection
    data=[[-1]*1024],  # query vectors
    limit=2,  # number of returned entities
    output_fields=["content", "embed"],  # specifies fields to be returned
)

print(res)

