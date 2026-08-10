import os
import re
import shutil
import config
from langchain_community.document_loaders import TextLoader, Docx2txtLoader, BSHTMLLoader
from langchain_core.documents import Document
from retrieval.semantic_chunker import chunk_documents
from retrieval.qdrant_client import get_vector_store, delete_document
from utils.pdf_loaders import PandasPDFLoader
import pymupdf4llm

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
    elif ext in [".html", ".htm"]:
        return BSHTMLLoader(filepath, open_encoding="utf-8")
    else:
        raise ValueError(f"Format non supporté : {ext}")




def process_file_task(filepath: str):
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".pdf":
            # page_chunks=True renvoie une liste de dictionnaires, un par page
            md_pages = pymupdf4llm.to_markdown(filepath, page_chunks=True)
            pages = []
            for item in md_pages:
                text = item.get("text", "")
                meta = item.get("metadata", {})
                
                # On extrait la page (pymupdf4llm utilise généralement 'page' ou on peut indexer manuellement si besoin)
                # S'il manque, on peut aussi utiliser l'index de la boucle
                page_num = meta.get("page", len(pages) + 1)
                
                pages.append(Document(page_content=text, metadata={"source": os.path.basename(filepath), "page": page_num}))
        else:
            loader = get_loader(filepath)
            pages = loader.load()
            for page in pages:
                page.metadata["source"] = os.path.basename(filepath)
        
        # Nettoyage avant découpage
        for page in pages:
            page.page_content = clean_text(page.page_content)
            
        chunks = chunk_documents(pages)
        
        # Enrichissement des métadonnées
        clean_ext = ext.replace(".", "")
        for chunk in chunks:
            chunk.metadata["type"] = clean_ext
            
            # La section est désormais automatiquement extraite par le MarkdownHeaderTextSplitter
            # On consolide cela dans la clé 'section' pour compatibilité avec l'existant.
            section = "Général"
            for h in ["Header 3", "Header 2", "Header 1"]:
                if h in chunk.metadata:
                    if section == "Général":
                        # Récupérer le titre le plus profond et nettoyer les balises Markdown (gras, italique)
                        raw_section = chunk.metadata[h]
                        section = raw_section.replace("**", "").replace("*", "").replace("__", "").replace("_", "").strip()
                    # Supprimer la clé originale pour éviter les doublons dans les métadonnées
                    del chunk.metadata[h]
            
            chunk.metadata["section"] = section

        # Déduplication : on supprime les anciens chunks du même document avant ré-ingestion
        delete_document(os.path.basename(filepath))

        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
    except Exception as e:
        print(f"Erreur lors de l'ingestion de {filepath}: {e}")
    finally:
        # Sauvegarder dans corpus/ AVANT de supprimer le fichier temporaire
        if os.path.exists(filepath):
            os.makedirs(config.CORPUS_DIR, exist_ok=True)
            corpus_dest = os.path.join(config.CORPUS_DIR, os.path.basename(filepath))
            # Ne copier que si le fichier source est différent du corpus (évite les rechargements)
            if os.path.abspath(filepath) != os.path.abspath(corpus_dest):
                shutil.copy2(filepath, corpus_dest)
                # On supprime uniquement le temporaire data/, jamais les fichiers de corpus/
                os.remove(filepath)
