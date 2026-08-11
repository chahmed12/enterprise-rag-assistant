from fastapi import HTTPException
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import (Distance, VectorParams, Filter, FilterSelector, FieldCondition, MatchValue, MatchAny, IsEmptyCondition, PayloadField)
import config
from utils.clients import get_embeddings
import os

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

def delete_document(source: str):
    """Supprime tous les chunks d'un document (identifié par son basename) pour éviter les doublons."""
    try:
        client = QdrantClient(url=config.QDRANT_URL)
        if client.collection_exists(config.COLLECTION_NAME):
            client.delete(
                collection_name=config.COLLECTION_NAME,
                points_selector=FilterSelector(
                    filter=Filter(must=[FieldCondition(key="metadata.source", match=MatchValue(value=source))])
                ),
            )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur lors de la suppression du document {source}: {e}")

def document_exists(source: str) -> bool:
    """Retourne True si le document (identifié par son basename) est déjà présent dans l'index."""
    try:
        client = QdrantClient(url=config.QDRANT_URL)
        if not client.collection_exists(config.COLLECTION_NAME):
            return False
        count = client.count(
            collection_name=config.COLLECTION_NAME,
            count_filter=Filter(must=[FieldCondition(key="metadata.source", match=MatchValue(value=source))]),
        )
        return count.count > 0
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur lors de la vérification du document {source}: {e}")

def search_passages(question: str, source_filter: str = None, type_filter: str = None, user_departments: list = None):
    try:
        vector_store = get_vector_store()
        
        must_conditions = []
        if source_filter:
            must_conditions.append(FieldCondition(key="metadata.source", match=MatchValue(value=os.path.basename(source_filter))))
        if type_filter:
            must_conditions.append(FieldCondition(key="metadata.type", match=MatchValue(value=type_filter)))

        # Filtre d'accès par département :
        # - PUBLIC (ou métadonnée absente, docs legacy) → visible par tous
        # - DEPARTMENT → visible si le département du doc est dans ceux de l'utilisateur
        # - RESTRICTED → visible si un département autorisé est dans ceux de l'utilisateur
        if user_departments:
            access_should = [
                FieldCondition(key="metadata.visibility", match=MatchValue(value="PUBLIC")),
                IsEmptyCondition(is_empty=PayloadField(key="metadata.visibility")),
                Filter(must=[
                    FieldCondition(key="metadata.visibility", match=MatchValue(value="DEPARTMENT")),
                    FieldCondition(key="metadata.department", match=MatchAny(any=user_departments)),
                ]),
                Filter(must=[
                    FieldCondition(key="metadata.visibility", match=MatchValue(value="RESTRICTED")),
                    FieldCondition(key="metadata.allowed_departments", match=MatchAny(any=user_departments)),
                ]),
            ]
            must_conditions.append(Filter(should=access_should))

        qdrant_filter = None
        if must_conditions:
            qdrant_filter = Filter(must=must_conditions)

        return vector_store.similarity_search_with_score(question, k=config.SEARCH_K, filter=qdrant_filter)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur de recherche documentaire: {e}")
