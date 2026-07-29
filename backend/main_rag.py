import os
import re
from dotenv import load_dotenv
from vector_store import reset_collection, add_documents, retrieve

try:
    from groq import Groq
except ImportError:  # pragma: no cover - fallback for environments without the SDK
    Groq = None

# 1. LOAD THE ENVIRONMENT FIRST
load_dotenv()

# 2. GET THE KEY IF AVAILABLE
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key and Groq else None


def _load_context_documents(session_id=None):
    context_files = ["security_policy.txt", "compliance_and_privacy.txt", "corporate_directory.txt", "data_retention_policy.txt"]
    base_path = os.path.join(os.path.dirname(__file__), "sample_data")
    documents = []

    for file_name in context_files:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as handle:
                documents.append({"name": file_name, "text": handle.read()})

    if session_id:
        session_dir = os.path.join(os.path.dirname(__file__), "uploads", session_id)
        if os.path.isdir(session_dir):
            for file_name in sorted(os.listdir(session_dir)):
                if file_name.endswith((".txt", ".md", ".json", ".pdf", ".docx")) and not file_name.endswith(".csv"):
                    file_path = os.path.join(session_dir, file_name)
                    if os.path.exists(file_path):
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                            documents.append({"name": file_name, "text": handle.read()})

    return documents


def _build_context_from_retrieval(question, session_id=None):
    hits = retrieve(question, k=4, session_id=session_id)
    if not hits:
        return []

    return [{"name": hit["source"], "text": hit["text"]} for hit in hits]


def _fallback_answer(question, documents):
    question_tokens = set(re.findall(r"[a-z0-9]+", question.lower()))
    best_match = None
    best_score = -1

    for document in documents:
        text = document["text"]
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        for paragraph in paragraphs:
            paragraph_tokens = set(re.findall(r"[a-z0-9]+", paragraph.lower()))
            score = len(question_tokens & paragraph_tokens)
            if score > best_score:
                best_score = score
                best_match = (document["name"], paragraph)

    if not best_match:
        return {
            "Question": question,
            "Answer": "No relevant information was found in the local policy documents.",
            "Citation": "None",
        }

    source_name, paragraph = best_match
    return {
        "Question": question,
        "Answer": paragraph,
        "Citation": source_name,
    }


def run_rag_single(question, session_id=None):
    documents = _load_context_documents(session_id=session_id)
    if not documents:
        return {"Question": question, "Answer": "No local documents were found for the audit index.", "Citation": "None"}

    indexed_context = _build_context_from_retrieval(question, session_id=session_id)
    if indexed_context:
        documents = indexed_context

    if client:
        context_files = [doc["name"] for doc in documents]
        context_parts = []
        for doc in documents:
            context_parts.append(f"--- DOCUMENT: {doc['name']} ---\n{doc['text']}")

        context = "\n\n".join(context_parts)
        system_prompt = (
            "You are a ruthless, highly literal compliance auditor. Your ONLY job is to extract exact answers "
            "from the provided context. If the provided context does not explicitly contain the direct answer to "
            "the question, you must NOT extrapolate, guess, or synthesize related information. Instead, you MUST "
            "reply with EXACTLY this string and nothing else: [DOCUMENTATION_GAP_DETECTED]."
        )

        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ],
                model="llama-3.3-70b-versatile",
            )

            full_text = response.choices[0].message.content
            source_match = re.search(r"SOURCES_USED:\s*\[(.*?)\]", full_text)

            if source_match:
                clean_citation = source_match.group(1)
                clean_answer = full_text.replace(source_match.group(0), "").strip()
            else:
                clean_citation = ", ".join(context_files)
                clean_answer = full_text

            return {
                "Question": question,
                "Answer": clean_answer,
                "Citation": clean_citation,
            }
        except Exception:
            pass

    return _fallback_answer(question, documents)