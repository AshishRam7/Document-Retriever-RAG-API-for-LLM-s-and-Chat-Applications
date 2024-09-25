Document Retriever for RAG’s to generate context for LLM’s and Chat Apps implemented as a RESTful POST API endpoint
![Untitled design (14)](https://github.com/user-attachments/assets/336aabb8-c83b-4d1c-9d0f-6b3082e26990)

Built a backend RESTful API server using Flask for a document retriever to generate context for large
language models (LLMs) and chat applications to use for inference.
• Leveraged Ollama’s nomic-embed-text embedding model for vector embeddings , and used Qdrant vector
database to store the embeddings and corresponding text chunk. Stored API Logs on SQLite DB.
• Implemented Caching to reduce Inference Time by storing recently accessed embeddings on Redis.




Tech Stack Used/Implementation Progress:
1. Backend - Flask(Python)
2. Vector Store/Database - Qdrant
3. Encoder for vector embeddings - nomic-embed-text by Ollama(Hugging Face) https://ollama.com/library/nomic-embed-text
4. Algorithm for similarity detection and search - Cosine Similarity 
5. Document Dataset used for Text Corpus - randomly chosen pdf's from(loaded into sample_text) - https://github.com/tpn/pdfs
6. API Rate Limiting - session module in Flask
7. Caching - Redis
8. background scraping process - scrapy (https://scrapy.org/) (partial implementation/initialization only due to error)
9. Logging - ElasticSearch(Only initialized due to time constraints)
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

