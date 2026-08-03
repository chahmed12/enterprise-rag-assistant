RAG_PROMPT_TEMPLATE = """Réponds à la question UNIQUEMENT à partir des passages ci-dessous.
Si les passages ne contiennent pas la réponse, dis clairement que tu ne sais pas.
Cite le document et la page dans ta réponse.

Passages :
{contexte}

Question : {question}

Réponse :"""


def build_prompt(question: str, contexte: str) -> str:
    return RAG_PROMPT_TEMPLATE.format(question=question, contexte=contexte)