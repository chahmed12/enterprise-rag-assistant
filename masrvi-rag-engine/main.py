import os
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks

from rag_service import process_file_task, generate_answer
from schemas import QuestionRequest, AnswerResponse, IngestResponse

app = FastAPI(title="Masrvi RAG Service")


@app.get("/health")
def health_check():
    return {"status": "ok"}


'''if not payload.question.strip():  Si la question est vide ou ne contient que des espaces'''

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
        filename=file.filename,
        message="Fichier en cours d'ingestion en arrière-plan.",
    )

