import chromadb
from sentence_transformers import SentenceTransformer
import os
hf_token = os.getenv("HF_TOKEN")
# Initialize ChromaDB (Saves data to a local folder)
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="compliance_docs")
model = SentenceTransformer("all-MiniLM-L6-v2")

def add_documents(docs, source_name):
    """Chunks are embedded and stored with metadata."""
    ids = [f"{source_name}_{i}" for i in range(len(docs))]
    embeddings = model.encode(docs).tolist()
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=docs,
        metadatas=[{"source": source_name} for _ in docs]
    )

def retrieve(query, k=3):
    """Semantic search to find the most relevant context."""
    query_vec = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_vec, n_results=k)
    
    formatted = []
    if results['documents']:
        for i in range(len(results['documents'][0])):
            formatted.append({
                "text": results['documents'][0][i],
                "source": results['metadatas'][0][i]['source']
            })
    return formatted