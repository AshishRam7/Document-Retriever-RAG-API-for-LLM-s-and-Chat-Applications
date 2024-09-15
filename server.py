from flask import Flask,request,jsonify,session, abort
import time 
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
import threading
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
# app.config['TESTING'] = True

max_calls_api = 5

app.secret_key = "21BCE6193"
NEWS_API_KEY = "7120a59089024152a1c46783dec2d1b1"

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

def news_scraper():
    while True:
        try:
            print("Web Scraper is Executing")
            response = requests.get("https://news.ycombinator.com/")
            soup = BeautifulSoup(response.text, 'html.parser')

            headlines = soup.find_all('a', class_='storylink')

            points = []
            for i, headline in enumerate(headlines[:2]):
                title = headline.get_text()
                url = headline.get('href')

                article_response = requests.get(url)
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                content = article_soup.get_text()

                title_embedding = model.encode(title).tolist()
                content_embedding = model.encode(content).tolist()

                title_point = models.PointStruct(
                    id=f"hn_title_{int(time.time())}_{i}",
                    vector=title_embedding,
                    payload={"title": title, "source": "Hacker News"}
                )
                content_point = models.PointStruct(
                    id=f"hn_content_{int(time.time())}_{i}",
                    vector=content_embedding,
                    payload={"title": title, "content": content, "source": "Hacker News"}
                )
                points.append(title_point)
                points.append(content_point)
                print(f"Processed headline: {title} - {url}")

            if points:
                qdrant_client.upsert(
                    collection_name = "Documents",
                    points=points
                )
                print(f"Uploaded {len(points)} articles to Vector Database")

        except Exception as e:
            print(f"Error during news scraping: {e}")

        time.sleep(600)


def background_worker():
    bg_thread = threading.Thread(target=news_scraper, daemon = True)
    bg_thread.start()
    print("Green")

if __name__ == "__main__":
    app.run(debug=True)