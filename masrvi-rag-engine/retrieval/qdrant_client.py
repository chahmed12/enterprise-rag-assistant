from fastapi import HTTPException
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import config
from utils.clients import get_embeddings

def get_vector_store() -> QdrantVectorStore:
    try:
        embeddings = get_embeddings()
        client = QdrantClient(url=config.QDRANT_URL)

        if not client.collection_exists(config.COLLECTION_NAME):
            client.create_collection(
                collection_name=config.COLLECTION_NAME,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

        return QdrantVectorStore(
            client=client,
            collection_name=config.COLLECTION_NAME,
            embedding=embeddings,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur de connexion à Qdrant: {e}")

def search_passages(question: str):
    try:
        vector_store = get_vector_store()
        return vector_store.similarity_search_with_score(question, k=config.SEARCH_K)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur de recherche documentaire: {e}")
