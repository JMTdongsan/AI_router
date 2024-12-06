import concurrent
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

from insert2DB import insert_data
from send_llm import vanila_inference


def get_html(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless 모드 추가
    chrome_options.add_argument("--no-sandbox")  # 일부 환경에서 충돌 방지를 위해 추가
    chrome_options.add_argument("--disable-dev-shm-usage")  # 리소스 부족 문제 해결
    chrome_options.add_argument("--disable-gpu")  # GPU 비활성화 (Linux에서 가끔 필요)

    # Chrome Driver 실행
    service = Service()  # 필요시 경로 지정 가능
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    time.sleep(2)
    try:
        driver.switch_to.frame('mainFrame')
        try:
            html = driver.find_element(By.CSS_SELECTOR, '#post-area').text
        except Exception as e:
            html = driver.find_element(By.TAG_NAME, 'body').text
    except:
        html = driver.find_element(By.TAG_NAME, 'body').text

    driver.close()
    return html



def naver_serch(keyword): # DB저장 X summarizes, urls 반환
    blog_url = f"https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={keyword}"
    news_url = f"https://search.naver.com/search.naver?ssc=tab.news.all&where=news&sm=tab_jum&query={keyword}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(blog_url, headers=headers)
    response2 = requests.get(news_url, headers=headers)
    # 블로그와 뉴스 크롤링 대상 링크 수집
    if response.status_code != 200:
        return "Error fetching the page", 500
    blog_urls = []
    blog_soup = BeautifulSoup(response.text, 'html.parser')
    for item in blog_soup.select(
            'div#main_pack > section > div.api_subject_bx > ul > li > div > div.detail_box > div.title_area > a'):
        blog_urls.append(item.attrs['href'])
    news_soup = BeautifulSoup(response2.text, 'html.parser')
    news_url = []
    for item in news_soup.select('div.group_news > ul > li > div > div > div.news_contents > a.news_tit'):
        news_url.append(item['href'])
    # html 추출
    urls = blog_urls[:3] + news_url[:3]
    summarizes = [None] * len(urls)
    htmls = []
    futures = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        for url in tqdm(urls, desc="selenium crawl"):
            futures.append(executor.submit(get_html, url))
    for future in concurrent.futures.as_completed(futures):
        htmls.append(future.result())
    print("html 추출 완료, llm 전송 시작")
    def task(index, html):
        prompt = f"You are an assistant that specializes in summarizing text."\
                 f"아래 웹페이지의 내용을 요약해 주세요. 작성자의 정보는 제외하고, 광고나 관련 없는 정보도 무시해 주세요."\
                 f"핵심 정보만 포함해 주세요. 영어로 생각하고 한글로 답변해주세요"\
                 f"{keyword}과 관련없는 광고가 포함될 수 있다. 웹페이지 전체가 관련이 없다면 광고라고 판단하고 'advertisement' 라고 답변해라. "\
                 f"content : {html}"
        summarizes[index] = vanila_inference(prompt)
        print(summarizes[index])
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(task, i, obj) for i, obj in enumerate(htmls)]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    return summarizes, urls

def search2naver(keyword): # 여러개의 크롤링 결과를 통합, DB 저장 메소드
    summarizes, urls = naver_serch(keyword)
    insert_data(summarizes, urls)
    message = (f"Read below articles and then explain about {keyword}. as possible as you can describe it in detail."
               f"max length is 500 words"
               f"It must be understandable to teenagers. think in chinese, reply in korean. article: ".join(summarizes))
    return vanila_inference(message)



if __name__ == "__main__":
    print("for debug only")
    start = time.time()
    naver_serch("도로 정비 사업")
    print("elapsed time ",time.time() - start)





