from flask import Flask,request,jsonify,session, abort
import time 
from elasticsearch import Elasticsearch

app = Flask(__name__)
# app.config['TESTING'] = True

max_calls_api = 5

app.secret_key = "21BCE6193"

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

    time_for_inference = time.time() - start_time_val

    session_info = {"Status" : "success",
            "Inference_Time" : time_for_inference,
            "API_calls_used" : session["api_count"]
            }

    if(session["api_count"] == 1):
        es.index(index='user', id=user_id, document=session_info)
    else:
        update_info = {
            "Inference_Time" : time_for_inference,
            "API_calls_used" : session["api_count"]
        }
        es.update(index='user', id=user_id, doc=update_info)

    return jsonify(session_info)

@app.route("/reset_session", methods = ["POST"])
def reset_session():
    data = request.get_json()
    user_id = data["user_id"]
    session.pop("api_count",None)
    es.index(index='user', id=user_id, document={"session": "reset"})
    return {"status" : "session has been reset"}

if __name__ == "__main__":
    app.run(debug=True)