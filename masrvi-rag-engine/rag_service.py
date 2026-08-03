import os
from fastapi import HTTPException
from langchain_ollama import OllamaEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from schemas import SourceItem

import config
from prompts import build_prompt
from file_loaders import get_loader


def _get_embeddings():
    """Retourne le provider d'embeddings selon la configuration.
    - Ollama (défaut) : appel HTTP local, aucun rechargement au démarrage
    - HuggingFace     : charge 430MB en RAM à chaque redémarrage (lent)
    """
    if config.USE_OLLAMA_EMBEDDINGS:
        return OllamaEmbeddings(
            model=config.EMBEDDING_MODEL,   # nomic-embed-text
            base_url=config.OLLAMA_URL,
        )
    return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)


def get_vector_store() -> QdrantVectorStore:
    try:
        embeddings = _get_embeddings()
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


def process_file_task(filepath: str):
    try:
        loader = get_loader(filepath)
        pages = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(pages)

        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
    except Exception as e:
        print(f"Erreur lors de l'ingestion de {filepath}: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

def search_passages(question: str):
    try:
        vector_store = get_vector_store()
        return vector_store.similarity_search_with_score(question, k=config.SEARCH_K)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur de recherche documentaire: {e}")


"""def generate_answer(question: str) -> str:
    resultats = search_passages(question)

    if not resultats or resultats[0][1] < config.RELEVANCE_THRESHOLD:
        return "Je n'ai pas trouvé d'information pertinente dans les documents."

    contexte = "\n\n".join(
        f"[Source: {doc.metadata.get('source')}, page {doc.metadata.get('page')}]\n{doc.page_content}"
        for doc, score in resultats
    )

    prompt = build_prompt(question=question, contexte=contexte)

    llm = ChatGroq(
        model=config.LLM_MODEL,
        api_key=config.GROQ_API_KEY,
        temperature=0,
    )

    reponse = llm.invoke(prompt)
    return reponse.content"""


def generate_answer(question: str) -> dict:
    resultats = search_passages(question)

    if not resultats or resultats[0][1] < config.RELEVANCE_THRESHOLD:
        return {
            "reponse": "Je n'ai pas trouve d'information pertinente dans les documents",
            "sources": []
        }

    sources = [
        SourceItem(
            document_name=doc.metadata.get("source","Inconnu"),
            page=doc.metadata.get("page"),
            score=round(score, 3)
        )
        for doc, score in resultats
    ]

    contexte = "\n\n".join(
        f"[source:{doc.metadata.get('source')}, page {doc.metadata.get('page')}] \n{doc.page_content}"
        for doc, score in resultats   # ← correction : décompresser le tuple (Document, score)
    )

    prompt = build_prompt(question=question, contexte=contexte)
    llm = ChatGroq(model=config.LLM_MODEL, api_key=config.GROQ_API_KEY, temperature=0)
    reponse = llm.invoke(prompt)

    return {"reponse": reponse.content, "sources": [s.dict() for s in sources] }
