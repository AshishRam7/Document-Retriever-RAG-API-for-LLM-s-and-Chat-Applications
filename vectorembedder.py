from qdrant_client import QdrantClient

qdrant_client = QdrantClient(
    "https://a3329a8d-14a1-4e8c-8e8f-020d8c23d5b5.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key="8-IYHB3uT83l8ypciVWx9rAp13jlH2Ey9jTIc46kxtGdBuuYMYWtog",
)

print(qdrant_client.get_collections())