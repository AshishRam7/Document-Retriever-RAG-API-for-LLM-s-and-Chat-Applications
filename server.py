import redis
import json
from flask import Flask, request, jsonify, session, abort
import time
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

app = Flask(__name__)
app.secret_key = "21BCE6193"

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

qdrant_client = QdrantClient(
    "https://a3329a8d-14a1-4e8c-8e8f-020d8c23d5b5.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key="8-IYHB3uT83l8ypciVWx9rAp13jlH2Ey9jTIc46kxtGdBuuYMYWtog",
)
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)

def elasticsearch(**kwargs):
    _es_hosts = ['http://localhost:9200']
    if 'hosts' in kwargs.keys():
        _es_hosts = kwargs['hosts']
    
    _es_obj = Elasticsearch(hosts=_es_hosts, request_timeout=10)
    if _es_obj.ping():
        print('Connected to ElasticSearch Successfully')
    else:
        print("Connection Unsuccessful")
    return _es_obj

es = elasticsearch()

@app.route("/search", methods=['POST'])
def search():
    if "api_count" not in session:
        session["api_count"] = 1
    else:
        session["api_count"] += 1

    if session["api_count"] > 5:
        return abort(429, description="Maximum API Call Limit Reached.")

    data = request.get_json()
    prompt_text = data["text"]
    k_count = data["top_k"]

    cache_key = f"search:{prompt_text}"

    cached_result = redis_client.get(cache_key)
    if cached_result:
        return jsonify(json.loads(cached_result))

    start_time_val = time.time()

    try:
        query_embedding = model.encode(prompt_text).tolist()

        results = qdrant_client.search(
            collection_name="Documents",
            query_vector=query_embedding,
            limit=k_count
        )

        results_final = []
        for result in results:
            results_final.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            })

        time_for_inference = time.time() - start_time_val

        session_info = {
            "Status": "success",
            "results": results_final,
            "Inference_Time": time_for_inference,
            "API_calls_used": session["api_count"]
        }

        redis_client.set(cache_key, json.dumps(session_info), ex=3600)

        redis_client.lpush("recent_queries", cache_key)
        if redis_client.llen("recent_queries") > 10:
            oldest_query = redis_client.rpop("recent_queries")
            redis_client.delete(oldest_query)

        return jsonify(session_info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset_session", methods=["POST"])
def reset_session():
    session.pop("api_count", None)
    session["api_count"] = 1
    return {"status": "session has been reset"}

if __name__ == "__main__":
    app.run(debug=True)
