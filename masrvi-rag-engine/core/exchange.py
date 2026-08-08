import config
from app.models import SourceItem
from retrieval.qdrant_client import search_passages
from utils.clients import get_llm

RAG_PROMPT_TEMPLATE = """Tu es un assistant virtuel expert et rigoureux. Ton rôle est de répondre aux questions des utilisateurs en t’appuyant EXCLUSIVEMENT sur les extraits de documents fournis dans le contexte ci-dessous.

--- RÈGLES À RESPECTER STRICTEMENT ---
1. FIDÉLITÉ AU CONTEXTE : Réponds uniquement à l'aide des informations explicitement mentionnées dans le contexte. N'invente rien et n'utilise pas de connaissances externes.
2. GESTION DE L'INCERTITUDE : Si la réponse ne se trouve pas dans le contexte ou si le contexte est insuffisant, réponds exactement : "Je ne trouve pas cette information dans les documents fournis."
3. CITATION DES SOURCES : Chaque affirmation importante doit citer sa source exacte en utilisant le format : [Nom_Du_Document, Page X].
4. FORMATAGE ET TON :
   - Adopte un ton professionnel, synthétique et clair.
   - Utilise du Markdown (listes à puces, gras) pour rendre la réponse facile à lire.

--- CONTEXTE DOCUMENTAIRE ---
{contexte}

--- QUESTION DE L'UTILISATEUR ---
{question}"""

def build_prompt(question: str, contexte: str) -> str:
    return RAG_PROMPT_TEMPLATE.format(question=question, contexte=contexte)

def generate_answer(question: str, source_filter: str = None, type_filter: str = None) -> dict:
    resultats = search_passages(question, source_filter=source_filter, type_filter=type_filter)

    if not resultats or resultats[0][1] < config.RELEVANCE_THRESHOLD:
        return {
            "reponse": "Je n'ai pas trouve d'information pertinente dans les documents",
            "sources": []
        }

    sources = [
        SourceItem(
            document_name=doc.metadata.get("source","Inconnu"),
            page=doc.metadata.get("page"),
            score=round(score, 3),
            section=doc.metadata.get("section")
        )
        for doc, score in resultats
    ]

    contexte = "\n\n".join(
        f"[source:{doc.metadata.get('source')}, page {doc.metadata.get('page')}, section {doc.metadata.get('section', 'N/A')}] \n{doc.page_content}"
        for doc, score in resultats
    )

    prompt = build_prompt(question=question, contexte=contexte)
    llm = get_llm()
    reponse = llm.invoke(prompt)

    return {"reponse": reponse.content, "sources": [s.model_dump() if hasattr(s, 'model_dump') else s.dict() for s in sources]}
