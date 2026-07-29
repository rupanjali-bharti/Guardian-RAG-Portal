import os
import re
import chromadb
from sentence_transformers import SentenceTransformer

hf_token = os.getenv("HF_TOKEN")

# Initialize ChromaDB (Saves data to a local folder)
client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(__file__), "chroma_db"))
MODEL_NAME = "all-MiniLM-L6-v2"
MODEL = SentenceTransformer(MODEL_NAME)


def _get_collection_name(session_id=None):
    return f"compliance_docs_{session_id or 'default'}"


def _get_collection(session_id=None):
    collection_name = _get_collection_name(session_id)
    return client.get_or_create_collection(name=collection_name)


def reset_collection(session_id=None):
    collection_name = _get_collection_name(session_id)
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    return client.get_or_create_collection(name=collection_name)


def chunk_text(text, chunk_size=500, overlap=80):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if not chunk:
            break
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def add_documents(docs, source_name, session_id=None):
    """Chunks are embedded and stored with metadata."""
    collection = _get_collection(session_id=session_id)
    all_chunks = []
    for doc in docs:
        for chunk in chunk_text(doc):
            all_chunks.append(chunk)

    if not all_chunks:
        return []

    ids = [f"{source_name}_{i}" for i in range(len(all_chunks))]
    embeddings = MODEL.encode(all_chunks).tolist()

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=all_chunks,
        metadatas=[{"source": source_name} for _ in all_chunks]
    )
    return ids


def retrieve(query, k=3, session_id=None):
    """Semantic search to find the most relevant context."""
    collection = _get_collection(session_id=session_id)
    query_vec = MODEL.encode([query]).tolist()
    results = collection.query(query_embeddings=query_vec, n_results=k)

    formatted = []
    if results.get('documents'):
        for i in range(len(results['documents'][0])):
            formatted.append({
                "text": results['documents'][0][i],
                "source": results['metadatas'][0][i]['source']
            })
    return formatted