import PyPDF2
from sentence_transformers import SentenceTransformer
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models


qdrant_client = QdrantClient(
    "https://a3329a8d-14a1-4e8c-8e8f-020d8c23d5b5.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key="8-IYHB3uT83l8ypciVWx9rAp13jlH2Ey9jTIc46kxtGdBuuYMYWtog",
)

model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)

directory_path = "D:\Trademarkia_AI\sample_text"

def load_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return [page.extract_text() for page in reader.pages]

def split_text(text, chunk_size=1000, chunk_overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - chunk_overlap
    return chunks

collection_name = "Documents"
try:
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=768,
            distance=models.Distance.COSINE
        )
    )
    print(f"Collection Created: {collection_name}")

except Exception as e:
    print(f"Collection already exists or error found: {e}")

for filename in os.listdir(directory_path):
    if filename.endswith(".pdf"):
        file_path = os.path.join(directory_path, filename)
        print(f"Processing : {file_path}")

        pdf_content = load_pdf(file_path)
        all_text = " ".join(pdf_content)
        chunked_documents = split_text(all_text)

        points = []
        for i, chunk in enumerate(chunked_documents):
            embedding = model.encode(chunk).tolist()
            points.append(
                models.PointStruct(
                    id=i, 
                    vector=embedding,
                    payload={"text": chunk, "file_name": filename}
                )
            )

        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )

        print(f"Uploaded{len(chunked_documents)} chunks from {filename} to Vector Database")