from time import time

from crawler import naver_serch, search2naver
from embed_api import get_embed

test_target = {
    "naver_search" : False,
    "search2naver" : True
}


if __name__ == '__main__':
    start_time = time()
    if test_target["naver_search"]:
        summarizes = naver_serch("도로 정비 사업")
        summarizes = naver_serch("월세")
        summarizes = naver_serch("가로 주택 정비 사항")
        summarizes = naver_serch("전세")
        print(summarizes)
    print("답변까지" ,time()-start_time)
    if test_target["search2naver"]:
        print(search2naver("도로 정비 사업"))