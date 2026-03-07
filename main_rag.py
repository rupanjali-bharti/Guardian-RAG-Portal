import time
# Import from your sub-modules, NOT from main_rag
from rag.generator import generate_answer 
from vector_store import retrieve

def run_rag_single(question):
    """Processes a single question to allow UI updates in app.py."""
    context = retrieve(question)
    answer, citation = generate_answer(question, context)
    time.sleep(4) 
    
    return {
        "Question": question,
        "Answer": answer,
        "Citation": citation
    }