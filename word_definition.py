import json
import time
import urllib
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from send_llm import vanila_inference


def fetch_and_summarize(url, word):
    """각 URL에서 데이터를 가져와 요약하는 함수"""
    full_url = "https://www.molit.go.kr" + url
    html = BeautifulSoup(requests.get(full_url).text, 'html.parser')
    body = html.select_one('#cont-body').text
    body = str(body)
    completion = vanila_inference(f"아래의 글을 읽고 {word}에 관련한 내용이다. 아래의 글을 잘 이해가 되게 자세히 설명해라. "
                                  f"예시가 있다면 예시도 같이 설명해라. {body}")
    return completion


def get_word_definition(word: str):
    url =f"https://www.molit.go.kr/search/search2023.jsp?query={word}&collections=n_policy&listCount=10&startCount=0"
    encoded = urllib.parse.quote(urllib.parse.quote(word))
    url = f"https://www.molit.go.kr/wisenut/search.do?query={encoded}&collections=n_policy&listCount=10&startCount=0"
    print(url)
    html = BeautifulSoup(requests.get(url).text,'html.parser')
    data = json.loads(html.get_text())
    urls = [item['url'] for item in data['searchResult']['n_policy']]
    futures = []
    extract = ""
    results = []

    # ThreadPoolExecutor로 병렬 처리
    with ThreadPoolExecutor(max_workers=len(urls)) as executor:
        # 모든 Future 작업을 제출하고 관리
        for url in urls:
            futures.append(executor.submit(fetch_and_summarize, url, word))
            time.sleep(1)

        # as_completed로 Future의 결과 순차 처리
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error fetching data from {futures[future]}: {e}")

    # 모든 결과를 하나의 문자열로 합침
    extract = ''.join(results)
    message = f"아래의 글을 읽고 {word}에 대해서 최대한 자세히 설명해달라. 예시가 있다면 같이 설명해달라." + extract
    return vanila_inference(message)
