import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from retrieval.semantic_chunker import chunk_documents
from retrieval.qdrant_client import get_vector_store

def get_loader(filepath: str):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return PyPDFLoader(filepath)
    elif ext in [".txt", ".md"]:
        return TextLoader(filepath, encoding="utf-8")
    elif ext == ".docx":
        return Docx2txtLoader(filepath)
    else:
        raise ValueError(f"Format non supporté : {ext}")

def process_file_task(filepath: str):
    try:
        loader = get_loader(filepath)
        pages = loader.load()
        chunks = chunk_documents(pages)

        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
    except Exception as e:
        print(f"Erreur lors de l'ingestion de {filepath}: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
