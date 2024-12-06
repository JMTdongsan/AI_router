import traceback

from flask import Flask, request, jsonify

from insert2DB import insert_data
from ragpipeline import rag_pipeline
from crawler import naver_serch

app = Flask(__name__)


# API to handle RAG-based question answering
@app.route('/api/ask_rag', methods=['GET'])
def rag_question():
    question = request.args.get('question')
    if not question:
        return jsonify({"error": "Question is required"}), 400
    try:
        # Use the RAG pipeline to get an answer
        results = rag_pipeline.run(
            {
                "text_embedder": {"text": question},
                "prompt_builder": {"query": question},
            }
        )
        answer = results["generator"]["replies"][0]
        return jsonify({"question": question, "answer": answer})
    except Exception as e:
        error_message = str(e)
        trace = traceback.format_exc()  # 에러의 전체 스택 트레이스를 가져옵니다
        return jsonify({"error": error_message, "trace": trace}), 500


@app.route('/api/ask', methods=["GET"])
def fcall_question():
    question = request.args.get('question')
    if not question:
        return jsonify({"error": "Question is required"}), 400
    try:
        results = funcrag_pipeline.run(
            {
                "text_embedder": {"text": question},
                "prompt_builder": {"query": question},
            }
        )
        answer = results["generator"]["replies"][0]
        return jsonify({"question": question, "answer": answer})
    except Exception as e:
        error_message = str(e)
        trace = traceback.format_exc()  # 에러의 전체 스택 트레이스를 가져옵니다
        return jsonify({"error": error_message, "trace": trace}), 500



@app.route('/api/crawl', methods=['GET'])
def crawl_insert():
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400
    summarizes, urls = naver_serch(keyword)
    insert_data(summarizes, urls)
    return jsonify({"keyword": keyword, "summaries": summarizes})




# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)