from langchain_text_splitters import RecursiveCharacterTextSplitter
import config

def chunk_documents(pages):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )
    return splitter.split_documents(pages)
