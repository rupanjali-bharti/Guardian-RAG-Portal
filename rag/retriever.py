from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

def retrieve_docs(question):

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = Chroma(
        persist_directory="chroma_db",
        embedding_function=embeddings
    )

    docs = db.similarity_search(question, k=3)

    return docs