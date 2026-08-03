import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
)

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
