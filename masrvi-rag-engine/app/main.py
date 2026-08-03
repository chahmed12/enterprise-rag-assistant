import os
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks

from core.process_document import process_file_task
from core.exchange import generate_answer
from app.models import QuestionRequest, AnswerResponse, IngestResponse

app = FastAPI(title="Masrvi RAG Service")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ask", response_model=AnswerResponse)
def ask_question(payload: QuestionRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas etre vide.")
    result = generate_answer(payload.question)
    return AnswerResponse(**result)


@app.post("/ingest", response_model=IngestResponse)
def ingest_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    allowed_exts = (".pdf", ".txt", ".md", ".docx")
    if not file.filename.lower().endswith(allowed_exts):
        raise HTTPException(status_code=400, detail="Format non supporté (PDF, TXT, MD, DOCX).")

    os.makedirs("data", exist_ok=True)
    filepath = f"data/{file.filename}"

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_file_task, filepath)

    return IngestResponse(
        file_name=file.filename,
        messages="Fichier en cours d'ingestion en arrière-plan.",
    )
