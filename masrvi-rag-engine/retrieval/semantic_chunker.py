from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter, Language
import config

def chunk_documents(pages):
    # 1. Extraction de la structure Markdown (titres)
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
    
    md_splits = []
    current_headers = {}
    
    for page in pages:
        # MarkdownHeaderTextSplitter travaille sur du texte et retourne des Documents
        splits = markdown_splitter.split_text(page.page_content)
        for split in splits:
            # 1. Mettre à jour la mémoire globale avec les nouveaux headers de ce split
            for h in ["Header 1", "Header 2", "Header 3"]:
                if h in split.metadata:
                    current_headers[h] = split.metadata[h]
                    # Si on trouve un titre de niveau supérieur, on invalide les sous-titres précédents
                    if h == "Header 1":
                        current_headers.pop("Header 2", None)
                        current_headers.pop("Header 3", None)
                    elif h == "Header 2":
                        current_headers.pop("Header 3", None)
            
            # 2. Si le split n'a pas de header, on lui donne ceux de la mémoire (titres de la page précédente)
            for h in ["Header 1", "Header 2", "Header 3"]:
                if h not in split.metadata and h in current_headers:
                    split.metadata[h] = current_headers[h]
                    
            # 3. On fusionne les métadonnées de la page (numéro de page, source)
            split.metadata.update(page.metadata)
            md_splits.append(split)

    # 2. Découpage respectueux de la structure Markdown (tableaux, listes)
    markdown_chunker = RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN,
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )
    
    return markdown_chunker.split_documents(md_splits)
