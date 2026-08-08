import os
import re
from langchain_community.document_loaders import TextLoader, Docx2txtLoader
from retrieval.semantic_chunker import chunk_documents
from retrieval.qdrant_client import get_vector_store
from utils.pdf_loaders import PandasPDFLoader

def clean_text(text: str) -> str:
    # Nettoyage des espaces multiples
    text = re.sub(r' +', ' ', text)
    # Remplacement des sauts de ligne multiples par un seul saut de ligne
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()



def get_loader(filepath: str):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return PandasPDFLoader(filepath)
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
        
        # Nettoyage avant découpage
        for page in pages:
            page.page_content = clean_text(page.page_content)
            
        chunks = chunk_documents(pages)
        
        # Enrichissement des métadonnées
        ext = os.path.splitext(filepath)[1].lower().replace(".", "")
        for chunk in chunks:
            chunk.metadata["type"] = ext
            
            # Heuristique pour la section : première ligne si elle est courte
            lines = chunk.page_content.split('\n')
            if lines:
                first_line = lines[0].strip()
                if len(first_line) > 0 and len(first_line) < 100 and first_line[0].isupper():
                    chunk.metadata["section"] = first_line
                else:
                    chunk.metadata["section"] = "Général"
            else:
                chunk.metadata["section"] = "Général"

        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
    except Exception as e:
        print(f"Erreur lors de l'ingestion de {filepath}: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
