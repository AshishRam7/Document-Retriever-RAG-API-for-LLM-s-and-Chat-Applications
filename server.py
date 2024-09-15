import redis
import json
import threading
import time
import numpy as np
from flask import Flask, request, jsonify, session, abort
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import scrapy
from scrapy.crawler import CrawlerProcess
from sklearn.metrics.pairwise import cosine_similarity

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

class BlogSpider(scrapy.Spider):
    name = 'blogspider'
    start_urls = ['https://www.zyte.com/blog/']

    def parse(self, response):
        for post in response.css('.oxy-post-title')[:3]:
            title = post.css('::text').get()
            url = post.css('a::attr(href)').get()
            if url:
                yield scrapy.Request(url=url, callback=self.parse_post, meta={'title': title})

    def parse_post(self, response):
        title = response.meta['title']
        content = ' '.join(response.css('p::text').getall())
        collection_info = qdrant_client.get_collection(collection_name="Documents")
        current_points_count = collection_info.points_count
        qdrant_client.upsert(
            collection_name="Documents",
            points=[
                {
                    "id": current_points_count + 1,
                    "payload": {
                        "text": content,
                        "file": title
                    }
                }
            ]
        )

def start_scraper():
    process = CrawlerProcess()
    process.crawl(BlogSpider)
    process.start()

def background_worker():
    while True:
        start_scraper()
        time.sleep(120)

def cosine_similarity_custom(embedding1, embedding2):
    return cosine_similarity([embedding1], [embedding2])[0][0]


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
    similarity_threshold = data.get("similarity_threshold", 0.8)

    query_embedding = model.encode(prompt_text).tolist()

    cached_matches = []
    cache_keys = redis_client.keys("cache:*")

    for key in cache_keys:
        cache_data = json.loads(redis_client.get(key))
        cached_embedding = cache_data['embedding']
        cached_payload = cache_data['payload']
        similarity = cosine_similarity_custom(query_embedding, cached_embedding)
        if similarity >= similarity_threshold:
            cached_matches.append({"payload": cached_payload, "similarity": similarity})
        if len(cached_matches) >= k_count:
            break

    if len(cached_matches) >= k_count:
        cached_matches_sorted = sorted(cached_matches, key=lambda x: -x['similarity'])[:k_count]
        return jsonify({"results": cached_matches_sorted})

    try:
        results = qdrant_client.search(
            collection_name="Documents",
            query_vector=query_embedding,
            limit=k_count - len(cached_matches)
        )

        results_final = cached_matches
        for result in results:
            results_final.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            })
            redis_client.set(f"cache:{result.id}", json.dumps({
                "embedding": query_embedding,
                "payload": result.payload
            }), ex=3600)

        return jsonify({"results": results_final})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset_session", methods=["POST"])
def reset_session():
    session.pop("api_count", None)
    session["api_count"] = 1
    return {"status": "session has been reset"}

if __name__ == "__main__":
    #worker_thread = threading.Thread(target=background_worker, daemon=True)
    #worker_thread.start()
    app.run(debug=True)
