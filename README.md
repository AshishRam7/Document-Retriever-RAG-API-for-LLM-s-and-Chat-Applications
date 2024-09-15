Official Submission for the TradeMarkia AI Intern assignment . Name: Ashish Ram J A, Register Number: 21BCE6193 

Document Retriever implemented as a RESTful POST API endpoint
![Untitled design (14)](https://github.com/user-attachments/assets/336aabb8-c83b-4d1c-9d0f-6b3082e26990)


Tech Stack Used/Implementation Progress:
1. Backend - Flask(Python)
2. Vector Store/Database - Qdrant
3. Encoder for vector embeddings - nomic-embed-text by Ollama(Hugging Face) https://ollama.com/library/nomic-embed-text
4. Algorithm for similarity detection and search - Cosine Similarity 
5. Document Dataset used for Text Corpus - randomly chosen pdf's from(loaded into sample_text) - https://github.com/tpn/pdfs
6. API Rate Limiting - session module in Flask
7. background scraping process - threading, newsapi , beautifulsoup(partial implementation/initializatiom)
8. Logging - ElasticSearch(Only initialized due to time constraints)
9. Caching - Redis (Attempted but faced errors that couldn't be resolved on time)
10. Other Python libraries used - PyPDF2(Document parsing), time(Inference time)

Steps to run the project:
1. Clone the repository
2. In the root directory , run python server.py to run the server at localhost:5000.
3. API Status - Get endpoint at localhost:5000/health
4. Searching for Documents - POST endpoint(searching) at localhost:5000/search
   This request requires a json query payload of the below format:
   {
    "user_id": 1,
    "text": "high performance computing",
    "top_k": 5,
    "threshold": 10

  }
here text refers to the prompt string , user_id is the client's uid , top_k is top k similar results and threshold is similarity threshold values 

  5. Reset Session - POST endpoint : resets current user session , to enable the user to close the session and thus refresh the amount of API call's back to 5 (for use in testing) 
  
Output for a sample query:
![image](https://github.com/user-attachments/assets/73a388e2-6cb9-423b-a162-c804d3b80161)
![image](https://github.com/user-attachments/assets/f03ef3c2-a88e-4f71-9fb2-05d6968e8ab5)

Qdrant data store - Collection containing vector embeddings 
![image](https://github.com/user-attachments/assets/957175c1-8690-459d-ad38-ee23122cda8d)

