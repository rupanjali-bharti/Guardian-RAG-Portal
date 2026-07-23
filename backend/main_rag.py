import os
import re
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:  # pragma: no cover - fallback for environments without the SDK
    Groq = None

# 1. LOAD THE ENVIRONMENT FIRST
load_dotenv()

# 2. GET THE KEY IF AVAILABLE
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key and Groq else None


def _load_context_documents():
    context_files = ["security_policy.txt", "compliance_and_privacy.txt", "corporate_directory.txt", "data_retention_policy.txt"]
    base_path = os.path.join(os.path.dirname(__file__), "sample_data")
    documents = []

    for file_name in context_files:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as handle:
                documents.append({"name": file_name, "text": handle.read()})

    return documents


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


def run_rag_single(question):
    documents = _load_context_documents()
    if not documents:
        return {"Question": question, "Answer": "No local documents were found for the audit index.", "Citation": "None"}

    if client:
        context_files = [doc["name"] for doc in documents]
        context_parts = []
        for doc in documents:
            context_parts.append(f"--- DOCUMENT: {doc['name']} ---\n{doc['text']}")

        context = "\n\n".join(context_parts)
        system_prompt = (
            "You are a Security Auditor. Answer the question using ONLY the provided context. "
            "At the very end of your answer, you MUST list the document names you used to find the answer "
            "in this exact format: SOURCES_USED: [file1.txt, file2.txt]. "
            "If you find no information, write: SOURCES_USED: [None]."
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