import requests
import json
from haystack import component, Document
from typing import List

import config

# URL 설정 (API 엔드포인트)
url = config.EMBED_URL  # 여기에 실제 URL을 입력하세요.
# sub_url = "http://117.16.136.198:8080/embed"

def get_embed(inputs:List[str]|str):
    # inputs가 문자열 또는 문자열 리스트일 수 있음
    if isinstance(inputs, str):
        inputs = [inputs]
    if not isinstance(inputs[0], str):
        raise ValueError("inputs must be a string")
    for i in range(len(inputs)):
        inputs[i] = inputs[i][:500]

    data = {"inputs": inputs}
    headers = {"Content-Type": "application/json"}
    if not url:
        raise ValueError("환경 변수 'EMBED_URL'이 설정되지 않았습니다.")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"임베딩 서버 요청 중 오류 발생: {e}")

    embeddings = response.json()
    if not isinstance(embeddings, list):
        raise ValueError("임베딩 서버의 응답이 예상한 형식이 아닙니다.")

    return embeddings  # 임베딩 리스트 반환


# 2. 사용자 정의 임베딩 컴포넌트 정의 (쿼리 임베딩용)
@component
class CustomTextEmbedder:
    @component.output_types(embedding=List[float])
    def run(self, text: str):
        embedding = get_embed(text)[0]  # get_embed 함수는 리스트를 반환하므로 첫 번째 요소 선택
        return {"embedding": embedding}



