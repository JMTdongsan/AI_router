import traceback

from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics


app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info("app_info", "AI Router application info", version="1.0.0")


def request_value(name):
    payload = request.get_json(silent=True) or {}
    value = payload.get(name)
    if value is None:
        value = request.form.get(name)
    if value is None:
        value = request.args.get(name)
    if isinstance(value, str):
        value = value.strip()
    return value


def json_error(message, status_code=400):
    body = {"error": message}
    if app.debug:
        body["trace"] = traceback.format_exc()
    return jsonify(body), status_code


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"}), 200


@app.route("/api/rag/config", methods=["GET"])
def rag_config():
    try:
        from vector_db import retrieval_status

        return jsonify(retrieval_status())
    except Exception as exc:
        return json_error(str(exc), 500)


@app.route("/api/ask_rag", methods=["GET", "POST"])
def rag_question():
    question = request_value("question")
    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        from ragpipeline import rag_pipeline

        results = rag_pipeline.run(
            {
                "text_embedder": {"text": question},
                "retriever": {"query": question},
                "prompt_builder": {"query": question},
            }
        )
        answer = results["generator"]["replies"][0]
        return jsonify({"question": question, "answer": answer})
    except Exception as exc:
        return json_error(str(exc), 500)


@app.route("/api/crawl", methods=["GET", "POST"])
def crawl_insert():
    keyword = request_value("keyword")
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400

    try:
        from crawler import naver_serch
        from insert2DB import insert_data

        summarizes, urls = naver_serch(keyword)
        insert_data(summarizes, urls)
        return jsonify({"keyword": keyword, "summaries": summarizes, "urls": urls})
    except Exception as exc:
        return json_error(str(exc), 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
