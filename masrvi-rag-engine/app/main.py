import logging
import os
import shutil
import threading
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks

import config
from core.process_document import process_file_task
from core.exchange import generate_answer
from retrieval.qdrant_client import clear_collection, document_exists, count_document_chunks
from app.models import QuestionRequest, AnswerResponse, IngestResponse, ReloadResponse, DocumentStatusResponse

logger = logging.getLogger("masrvi.startup")

MAX_STARTUP_ATTEMPTS = 5
STARTUP_RETRY_DELAY = 3
STARTUP_INGEST_WAIT_TIMEOUT = 300

# Sérialise toute mutation du corpus (ingestion de démarrage, /reload, /ingest)
# pour éviter qu'un clear_collection() n'efface des points en cours d'écriture.
_CORPUS_LOCK = threading.RLock()
_STARTUP_INGEST_DONE = threading.Event()


def _ingest_missing_corpus():
    """Indexe au démarrage tout fichier du corpus absent de Qdrant (idempotent)."""
    try:
        for attempt in range(MAX_STARTUP_ATTEMPTS):
            try:
                if not os.path.exists(config.CORPUS_DIR):
                    return
                pending = False
                with _CORPUS_LOCK:
                    for filename in os.listdir(config.CORPUS_DIR):
                        filepath = os.path.join(config.CORPUS_DIR, filename)
                        if not os.path.isfile(filepath):
                            continue
                        try:
                            if document_exists(os.path.basename(filepath)):
                                continue
                            pending = True
                            logger.info("Auto-ingest : indexation de %s", filename)
                            process_file_task(filepath)
                        except Exception as e:
                            logger.error("Auto-ingest échoué pour %s : %s", filename, e, exc_info=True)
                            pending = True
                if not pending:
                    return
            except Exception as e:
                logger.error("Auto-ingest : tentative %s échouée : %s", attempt + 1, e, exc_info=True)
            time.sleep(STARTUP_RETRY_DELAY)
    finally:
        _STARTUP_INGEST_DONE.set()


def _reingest_corpus_files():
    """Ré-ingère l'intégralité du corpus sous verrou (une seule tâche de fond)."""
    with _CORPUS_LOCK:
        corpus_dir = config.CORPUS_DIR
        if not os.path.exists(corpus_dir):
            return
        for filename in sorted(os.listdir(corpus_dir)):
            filepath = os.path.join(corpus_dir, filename)
            if not os.path.isfile(filepath):
                continue
            try:
                process_file_task(filepath)
            except Exception as e:
                logger.error("Reload : ré-ingestion échouée pour %s : %s", filename, e, exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=_ingest_missing_corpus, daemon=True).start()
    yield


app = FastAPI(title="Masrvi RAG Service", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/document-status", response_model=DocumentStatusResponse)
def document_status(filename: str = None):
    if not filename:
        raise HTTPException(status_code=400, detail="Le paramètre 'filename' est obligatoire.")
    chunks = count_document_chunks(os.path.basename(filename))
    return DocumentStatusResponse(exists=chunks > 0, chunk_count=chunks)


@app.post("/ask", response_model=AnswerResponse)
def ask_question(payload: QuestionRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas etre vide.")
    result = generate_answer(
        payload.question,
        source_filter=payload.source_filter,
        type_filter=payload.type_filter,
        user_departments=payload.user_departments
    )
    return AnswerResponse(**result)


@app.post("/ingest", response_model=IngestResponse)
def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    department: str = Form(None),
    visibility: str = Form("PUBLIC"),
    allowed_departments: str = Form(None),
):
    allowed_exts = (".pdf", ".txt", ".md", ".docx", ".html", ".htm")
    if not file.filename or not file.filename.lower().endswith(allowed_exts):
        raise HTTPException(status_code=400, detail="Format non supporté (PDF, TXT, MD, DOCX).")

    # Sécurité : le nom est réduit au basename pour empêcher toute injection
    # de chemin (ex: "../../etc/passwd") ; un nom non conforme est refusé.
    safe_name = os.path.basename(file.filename)
    if safe_name != file.filename or not safe_name:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide.")

    # Garde anti-doublon : refuser uniquement si le fichier est déjà présent dans le corpus.
    # S'il est dans Qdrant mais absent du corpus (corpus vidé), on ré-ingère pour le restaurer.
    if document_exists(safe_name):
        corpus_dest = os.path.join(config.CORPUS_DIR, file.filename)
        if os.path.exists(corpus_dest):
            return IngestResponse(
                file_name=file.filename,
                messages="Document déjà ingéré, aucun traitement.",
            )

    os.makedirs("data", exist_ok=True)
    # Fichier temporaire à nom unique (uuid) pour éviter les collisions entre
    # uploads simultanés ; le nom original est conservé pour le corpus.
    tmp_name = f"{uuid.uuid4().hex}_{safe_name}"
    filepath = os.path.join("data", tmp_name)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    allowed_deps = None
    if allowed_departments:
        allowed_deps = [d.strip() for d in allowed_departments.split(",") if d.strip()]

    background_tasks.add_task(
        process_file_task, filepath,
        department=department,
        visibility=visibility,
        allowed_departments=allowed_deps,
        original_name=safe_name,
    )

    return IngestResponse(
        file_name=file.filename,
        messages="Fichier en cours d'ingestion en arrière-plan.",
    )


@app.post("/reload", response_model=ReloadResponse)
def reload_corpus(background_tasks: BackgroundTasks):
    # L'indexation de démarrage doit être terminée : sinon son clear/write
    # entrelacerait la réinitialisation et produirait un corpus incohérent.
    if not _STARTUP_INGEST_DONE.wait(timeout=STARTUP_INGEST_WAIT_TIMEOUT):
        raise HTTPException(
            status_code=503,
            detail="Indexation de démarrage encore en cours, réessayez dans un instant.",
        )

    corpus_dir = config.CORPUS_DIR
    with _CORPUS_LOCK:
        clear_collection()
        count = 0
        if os.path.exists(corpus_dir):
            for filename in os.listdir(corpus_dir):
                filepath = os.path.join(corpus_dir, filename)
                if os.path.isfile(filepath):
                    count += 1

    # Une seule tâche de fond, sous verrou, pour garantir l'atomicité du rechargement.
    background_tasks.add_task(_reingest_corpus_files)

    return ReloadResponse(
        messages=f"Collection réinitialisée. {count} fichier(s) en cours de rechargement depuis le corpus."
    )
