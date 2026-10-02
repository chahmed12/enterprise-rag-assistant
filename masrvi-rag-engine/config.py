import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "masrvi_docs")

# ── Embeddings ────────────────────────────────────────────────────────────────
# USE_OLLAMA_EMBEDDINGS=true  → utilise nomic-embed-text via Ollama (recommandé)
# USE_OLLAMA_EMBEDDINGS=false → utilise HuggingFace (télécharge 430MB au 1er démarrage)
USE_OLLAMA_EMBEDDINGS = os.getenv("USE_OLLAMA_EMBEDDINGS", "true").lower() == "true"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")  # modèle Ollama

# ── LLM ───────────────────────────────────────────────────────────────────────
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Le palier gratuit Groq plafonne à 1000 tokens de sortie par minute (OTPM).
# Sans plafond explicite, l'API utilise la valeur par défaut du modèle (1625)
# et toute requête échoue en HTTP 429.
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "800"))
# Nombre de tentatives automatiques sur erreur transitoire (429, 5xx, timeout).
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# ── Recherche & Chunking ──────────────────────────────────────────────────────
SEARCH_K = int(os.getenv("SEARCH_K", "5"))
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.65"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# ── Stockage des fichiers sources ─────────────────────────────────────────────
# Dossier permanent qui conserve les fichiers source pour permettre le rechargement
CORPUS_DIR = os.getenv("CORPUS_DIR", "corpus")