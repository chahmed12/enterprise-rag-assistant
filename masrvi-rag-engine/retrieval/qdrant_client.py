from fastapi import HTTPException
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue
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

def clear_collection():
    try:
        client = QdrantClient(url=config.QDRANT_URL)
        if client.collection_exists(config.COLLECTION_NAME):
            client.delete_collection(collection_name=config.COLLECTION_NAME)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur lors de la suppression de la collection: {e}")

def search_passages(question: str, source_filter: str = None, type_filter: str = None):
    try:
        vector_store = get_vector_store()
        
        filter_conditions = []
        if source_filter:
            filter_conditions.append(FieldCondition(key="metadata.source", match=MatchValue(value=source_filter)))
        if type_filter:
            filter_conditions.append(FieldCondition(key="metadata.type", match=MatchValue(value=type_filter)))
            
        qdrant_filter = None
        if filter_conditions:
            qdrant_filter = Filter(must=filter_conditions)

        return vector_store.similarity_search_with_score(question, k=config.SEARCH_K, filter=qdrant_filter)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur de recherche documentaire: {e}")
