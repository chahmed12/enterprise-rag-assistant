import os
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks

import config
from core.process_document import process_file_task
from core.exchange import generate_answer
from retrieval.qdrant_client import clear_collection, document_exists
from app.models import QuestionRequest, AnswerResponse, IngestResponse, ReloadResponse

app = FastAPI(title="Masrvi RAG Service")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ask", response_model=AnswerResponse)
def ask_question(payload: QuestionRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas etre vide.")
    result = generate_answer(
        payload.question,
        source_filter=payload.source_filter,
        type_filter=payload.type_filter
    )
    return AnswerResponse(**result)


@app.post("/ingest", response_model=IngestResponse)
def ingest_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    allowed_exts = (".pdf", ".txt", ".md", ".docx", ".html", ".htm")
    if not file.filename.lower().endswith(allowed_exts):
        raise HTTPException(status_code=400, detail="Format non supporté (PDF, TXT, MD, DOCX).")

    # Garde anti-doublon : refuser uniquement si le fichier est déjà présent dans le corpus.
    # S'il est dans Qdrant mais absent du corpus (corpus vidé), on ré-ingère pour le restaurer.
    if document_exists(os.path.basename(file.filename)):
        corpus_dest = os.path.join(config.CORPUS_DIR, file.filename)
        if os.path.exists(corpus_dest):
            return IngestResponse(
                file_name=file.filename,
                messages="Document déjà ingéré, aucun traitement.",
            )

    os.makedirs("data", exist_ok=True)
    filepath = f"data/{file.filename}"

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_file_task, filepath)

    return IngestResponse(
        file_name=file.filename,
        messages="Fichier en cours d'ingestion en arrière-plan.",
    )


@app.post("/reload", response_model=ReloadResponse)
def reload_corpus(background_tasks: BackgroundTasks):
    clear_collection()
    
    corpus_dir = config.CORPUS_DIR
    count = 0
    if os.path.exists(corpus_dir):
        for filename in os.listdir(corpus_dir):
            filepath = os.path.join(corpus_dir, filename)
            if os.path.isfile(filepath):
                # On re-ingère directement depuis corpus/
                # process_file_task ne supprimera pas le fichier car il voit qu'il est déjà dans corpus/
                background_tasks.add_task(process_file_task, filepath)
                count += 1
                
    return ReloadResponse(
        messages=f"Collection réinitialisée. {count} fichier(s) en cours de rechargement depuis le corpus."
    )
