import time
from concurrent.futures import ThreadPoolExecutor

from TEST.benchmark import bench_questions
from send_llm import vanila_inference

if __name__ == "__main__":  # for test
    futures = []
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=16) as executor:
        for i in range(1000):
            futures.append(executor.submit(vanila_inference, bench_questions[i % len(bench_questions)]))
            # 모든 작업이 완료될 때까지 기다립니다
        for future in futures:
            print(future.result())
    print("%s milliseconds" % round((time.time() - start_time) * 1000))