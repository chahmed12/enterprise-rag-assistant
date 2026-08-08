import pandas as pd
import pdfplumber
from langchain_core.documents import Document

def load_pdf_with_tables(file_path):
    documents = []
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # 1. Extraction des tableaux sur la page
            tables = page.extract_tables()
            
            # 2. Extraction du texte brut
            text = page.extract_text() or ""
            
            # Si des tableaux sont détectés, on peut les formatter en Markdown
            table_markdowns = []
            if tables:
                for table in tables:
                    # Nettoyage des valeurs None
                    cleaned_table = [[cell if cell is not None else "" for cell in row] for row in table]
                    
                    if len(cleaned_table) > 1:
                        # Utilisation de Pandas pour créer une structure claire
                        df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0])
                        # Conversion du tableau en format Markdown
                        table_markdowns.append(df.to_markdown(index=False))
            
            # Si un tableau a été extrait, on concatène le texte et le(s) tableau(x) formaté(s)
            full_content = text
            if table_markdowns:
                full_content += "\n\n--- TABLEAUX EXTRACTS ---\n" + "\n\n".join(table_markdowns)
            
            # Création du document LangChain
            doc = Document(
                page_content=full_content,
                metadata={
                    "source": file_path,
                    "page": page_num,
                    "total_pages": len(pdf.pages)
                }
            )
            documents.append(doc)
            
    return documents
class PandasPDFLoader:
    """Wrapper pour utiliser load_pdf_with_tables sous forme de loader compatible LangChain."""
    def __init__(self, filepath: str):
        self.filepath = filepath

    def load(self):
        return load_pdf_with_tables(self.filepath)
