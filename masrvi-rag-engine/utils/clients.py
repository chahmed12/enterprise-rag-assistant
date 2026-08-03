import config
from langchain_ollama import OllamaEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

def get_embeddings():
    if config.USE_OLLAMA_EMBEDDINGS:
        return OllamaEmbeddings(
            model=config.EMBEDDING_MODEL,
            base_url=config.OLLAMA_URL,
        )
    return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

def get_llm():
    return ChatGroq(model=config.LLM_MODEL, api_key=config.GROQ_API_KEY, temperature=0)
