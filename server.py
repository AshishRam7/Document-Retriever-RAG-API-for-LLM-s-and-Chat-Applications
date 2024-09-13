from flask import Flask,request,jsonify,session, abort
import time 

app = Flask(__name__)

max_calls_api = 5

app.secret_key = "21BCE6193"

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

    return {"Status" : "success",
            "Inference_Time" : time_for_inference,
            "API_calls_used" : session["api_count"]
            }

if __name__ == "__main__":
    app.run(debug=True)