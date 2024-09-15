from flask import Flask,request,jsonify,session, abort
import time 
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
import threading
import requests
from bs4 import BeautifulSoup
from newsapi import NewsApiClient

app = Flask(__name__)
# app.config['TESTING'] = True

max_calls_api = 5

app.secret_key = "21BCE6193"
newsapi = NewsApiClient(api_key='7120a59089024152a1c46783dec2d1b1')

qdrant_client = QdrantClient(
    "https://a3329a8d-14a1-4e8c-8e8f-020d8c23d5b5.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key="8-IYHB3uT83l8ypciVWx9rAp13jlH2Ey9jTIc46kxtGdBuuYMYWtog",
)

model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)

def elasticsearch(** kwargs):
    _es_hosts = ['http://localhost:9200']
    if 'hosts' in kwargs.keys():
        _es_hosts = kwargs['hosts']
    
    _es_obj = None
    _es_obj = Elasticsearch(hosts=_es_hosts,request_timeout = 10)
    if _es_obj.ping():
        print('Connected to ElasticSearch Successfully')
    else:
        print("Connection Unsuccessful")
        
    return _es_obj

es = elasticsearch()

@app.route("/health" ,methods = ['GET'])
def health():
    return {"status" : "API is active"}

@app.route("/search" ,methods = ['POST'])
def search():

    if "api_count" not in session:
        session["api_count"] = 1
    else:
        session["api_count"] += 1
    
    if session["api_count"] > max_calls_api:
        return abort(429,description="Maximum API Call Limit of 5 Reached. Please try again after sometime.")

    data = request.get_json()
    user_id = data["user_id"]
    prompt_text = data["text"]
    k_count = data["top_k"]
    similarity_threshold = data["threshold"]

    start_time_val = time.time()

    try:
        query_embedding = model.encode(prompt_text).tolist()
        #print(query_embedding)
        results = qdrant_client.search(
            collection_name = "Documents",
            query_vector = query_embedding,
            limit = k_count
        )

        results_final = []
        for result in results:
            results_final.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            })

        print(results_final)

        time_for_inference = time.time() - start_time_val

        session_info = {"Status" : "success",
                "results" : results_final, 
                "Inference_Time" : time_for_inference,
                "API_calls_left" : 5 - session["api_count"]
                }

        # if(session["api_count"] == 1):
        #     es.index(index='user', id=user_id, document=session_info)
        # else:
        #     update_info = {
        #         "Inference_Time" : time_for_inference,
        #         "API_calls_used" : session["api_count"]
        #     }
        #     es.update(index='user', id=user_id, doc=update_info)

        return jsonify(session_info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset_session", methods = ["POST"])
def reset_session():
    data = request.get_json()
    user_id = data["user_id"]
    session.pop("api_count",None)
    # es.index(index='user', id=user_id, document={"session": "reset"})
    return {"status" : "session has been reset"}

def split_text(text, chunk_size=1000, chunk_overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - chunk_overlap
    return chunks

def get_last_indexed_point():
    try:
        search_result = qdrant_client.search(
            collection_name="Documents",
            query_vector=[0.0] * 768,
            limit=1,
            with_payload=False,
            with_vectors=False,
            score_threshold=0.0,
            sort_by="id",
            descending=True
        )
        if search_result:
            last_point_id = int(search_result[0].id)
            return last_point_id
    except Exception as e:
        print(f"Error fetching last indexed point: {e}")
    
    return 0

def news_scraper():
    while True:
        try:
            last_index = get_last_indexed_point()
            print(f"Starting from index {last_index + 1}")

            top_headlines = newsapi.get_top_headlines(q='bitcoin',
                                                      sources='bbc-news,the-verge',
                                                      category='business',
                                                      language='en',
                                                      country='us')

            articles = top_headlines.get('articles', [])

            points = []
            for i, article in enumerate(articles[:5]):
                title = article.get("title", "No Title")
                content = article.get("content", article.get("description", ""))

                if not content.strip():
                    print(f"News article empty : {title}")
                    continue

                chunked_content = split_text(content)

                for j, chunk in enumerate(chunked_content):
                    embedding = model.encode(chunk).tolist()

                    point_id = last_index + 1 
                    last_index += 1 

                    point = models.PointStruct(
                        id=point_id, 
                        vector=embedding,
                        payload={
                            "file_name": title,
                            "text": chunk,
                        }
                    )
                    points.append(point)
                    print(f"Processed article: {title} (Chunk {j + 1})")

            if points:
                qdrant_client.upsert(
                    collection_name="Documents",
                    points=points
                )
                print(f"Uploaded {len(points)} article chunks to Vector Database")

        except Exception as e:
            print(f"Error fetching or uploading news: {e}")

        time.sleep(600)


def background_worker():
    bg_thread = threading.Thread(target=news_scraper, daemon = True)
    bg_thread.start()
    news_scraper()

if __name__ == "__main__":
    app.run(debug=True)
    background_worker()