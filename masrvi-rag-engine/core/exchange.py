import config
from app.models import SourceItem
from retrieval.qdrant_client import search_passages
from utils.clients import get_llm

RAG_PROMPT_TEMPLATE = """Réponds à la question UNIQUEMENT à partir des passages ci-dessous.
Si les passages ne contiennent pas la réponse, dis clairement que tu ne sais pas.
Cite le document et la page dans ta réponse.

Passages :
{contexte}

Question : {question}

Réponse :"""

def build_prompt(question: str, contexte: str) -> str:
    return RAG_PROMPT_TEMPLATE.format(question=question, contexte=contexte)

def generate_answer(question: str) -> dict:
    resultats = search_passages(question)

    if not resultats or resultats[0][1] < config.RELEVANCE_THRESHOLD:
        return {
            "reponse": "Je n'ai pas trouve d'information pertinente dans les documents",
            "sources": []
        }

    sources = [
        SourceItem(
            document_name=doc.metadata.get("source","Inconnu"),
            page=doc.metadata.get("page"),
            score=round(score, 3)
        )
        for doc, score in resultats
    ]

    contexte = "\n\n".join(
        f"[source:{doc.metadata.get('source')}, page {doc.metadata.get('page')}] \n{doc.page_content}"
        for doc, score in resultats
    )

    prompt = build_prompt(question=question, contexte=contexte)
    llm = get_llm()
    reponse = llm.invoke(prompt)

    return {"reponse": reponse.content, "sources": [s.dict() for s in sources]}
