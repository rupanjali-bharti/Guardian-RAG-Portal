import os
import csv
import glob
import re
import uuid
from fnmatch import fnmatch
from flask import Flask, jsonify, request
from flask_cors import CORS
from main_rag import run_rag_single
from vector_store import reset_collection, add_documents

app = Flask(__name__)


def get_allowed_origins():
    fallback_origins = [
        "https://guardian-rag-portal.vercel.app",
        "http://localhost:5173",
        "http://localhost:5001",
    ]

    configured_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
    merged_origins = list(fallback_origins)

    if configured_origins:
        merged_origins.extend(
            origin.strip() for origin in configured_origins.split(",") if origin.strip()
        )

    seen = set()
    unique_origins = []
    for origin in merged_origins:
        if origin and origin not in seen:
            seen.add(origin)
            unique_origins.append(origin)

    return unique_origins


def is_origin_allowed(origin):
    if not origin:
        return False

    allowed_origins = get_allowed_origins()
    if "*" in allowed_origins:
        return True

    return any(fnmatch(origin, pattern) for pattern in allowed_origins) or origin in allowed_origins


def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin and is_origin_allowed(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"

    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, x-session-id, session_id"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


CORS(
    app,
    resources={r"/api/*": {"origins": get_allowed_origins()}},
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "x-session-id", "session_id"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.status_code = 200
        return add_cors_headers(response)


@app.after_request
def apply_cors_headers(response):
    return add_cors_headers(response)


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = CURRENT_DIR
SAMPLE_DATA_DIR = os.path.join(CURRENT_DIR, "sample_data")
UPLOAD_ROOT = os.path.join(CURRENT_DIR, "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)


def get_request_session_id():
    form_session_id = request.form.get("session_id")
    if form_session_id:
        return form_session_id.strip()

    header_session_id = request.headers.get("x-session-id") or request.headers.get("session_id")
    if header_session_id:
        return header_session_id.strip()

    payload = request.get_json(silent=True) or {}
    payload_session_id = payload.get("session_id")
    if payload_session_id:
        return str(payload_session_id).strip()

    return None


def load_questions(csv_path=None):
    if not csv_path:
        csv_path = find_questionnaire_csv(SAMPLE_DATA_DIR)
    if not csv_path or not os.path.exists(csv_path):
        return []

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    questions = []
    for row in rows:
        for value in row.values():
            if isinstance(value, str) and value.strip():
                questions.append(value.strip())
                break

    return questions


def find_questionnaire_csv(session_dir):
    csv_files = sorted(glob.glob(os.path.join(session_dir, "*.csv")))
    return csv_files[0] if csv_files else None


def persist_uploaded_file(uploaded_file, destination):
    stream = getattr(uploaded_file, "stream", None)
    if stream is not None and hasattr(stream, "seek"):
        stream.seek(0)

    content = uploaded_file.read() if hasattr(uploaded_file, "read") else b""
    if isinstance(content, str):
        content = content.encode("utf-8")
    elif not isinstance(content, (bytes, bytearray)):
        content = b""

    with open(destination, "wb") as handle:
        handle.write(content)

    if stream is not None and hasattr(stream, "seek"):
        stream.seek(0)

    file_size = os.path.getsize(destination)
    app.logger.info("Saved uploaded file %s size=%s bytes", destination, file_size)
    return file_size


def save_uploaded_files(policy_files, questionnaire_file, session_id=None):
    session_id = session_id or str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_ROOT, session_id)
    os.makedirs(session_dir, exist_ok=True)

    saved_policies = []
    for uploaded_file in policy_files or []:
        filename = uploaded_file.filename or "policy.txt"
        destination = os.path.join(session_dir, filename)
        persist_uploaded_file(uploaded_file, destination)
        saved_policies.append(destination)

    if questionnaire_file:
        questionnaire_path = os.path.join(session_dir, questionnaire_file.filename or "questionnaire.csv")
        persist_uploaded_file(questionnaire_file, questionnaire_path)
    else:
        questionnaire_path = None

    return session_id, session_dir, saved_policies, questionnaire_path


def index_uploaded_documents(policy_files, session_id=None):
    if not policy_files:
        return [], []

    session_id = session_id or str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_ROOT, session_id)
    os.makedirs(session_dir, exist_ok=True)

    indexed_files = []
    for uploaded_file in policy_files or []:
        filename = uploaded_file.filename or "policy.txt"
        destination = os.path.join(session_dir, filename)
        persist_uploaded_file(uploaded_file, destination)
        indexed_files.append(filename)

    reset_collection(session_id=session_id)
    for filename in indexed_files:
        file_path = os.path.join(session_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                add_documents([handle.read()], filename, session_id=session_id)

    return indexed_files, session_id


def is_missing_context_response(text):
    if text is None:
        return True

    normalized = str(text).strip().lower()
    if not normalized:
        return True

    patterns = [
        r"\bno information\b",
        r"\bnot provided\b",
        r"\bdoes not contain\b",
        r"\bdoes not provide\b",
        r"\bempty\b",
        r"\bno context\b",
        r"\bnot enough information\b",
        r"\bno evidence\b",
        r"\[documentation_gap_detected\]",
        r"\bprovided documents are empty\b",
        r"\bthere is no information\b",
    ]
    return any(re.search(pattern, normalized) for pattern in patterns)


def build_audit_payload(questions, session_id=None, questionnaire_path=None, target_directory=None):
    target_directory = target_directory or SAMPLE_DATA_DIR
    results = []
    for question in questions:
        result = run_rag_single(question, session_id=session_id)
        answer_text = str(result.get("Answer", "")).strip()
        citation_text = str(result.get("Citation", "")).strip()
        answer_lower = answer_text.lower()

        verified = True
        if "[documentation_gap_detected]" in answer_lower:
            answer_text = "No relevant policy information found in uploaded documents."
            gap_value = 100
            verified = False
            status = "Critical Gap"
        elif is_missing_context_response(answer_text) or is_missing_context_response(citation_text):
            answer_text = "No relevant policy information found in uploaded documents."
            gap_value = 100
            verified = False
            status = "Critical Gap"
        else:
            grounding_score = 0
            if any(ext in citation_text.lower() for ext in [".txt", ".pdf", ".docx"]):
                grounding_score += 40

            gap_words = ["not found", "not mentioned", "unavailable", "does not specify"]
            if not any(word in answer_lower for word in gap_words):
                grounding_score += 30
            if len(answer_text) > 80:
                grounding_score += 30

            gap_value = max(0, min(100, 100 - grounding_score))

            if gap_value <= 20:
                status = "Verified"
            elif gap_value <= 50:
                status = "Partial Info"
            elif gap_value <= 80:
                status = "Significant Gap"
            else:
                status = "Critical Gap"

        results.append({
            "Question": question,
            "Answer": answer_text,
            "Citation": citation_text,
            "Status": status,
            "GapPercentage": gap_value,
            "Verified": verified,
        })

    summary = {
        "total_items": len(results),
        "verified_count": sum(1 for item in results if item["Status"] == "Verified"),
        "partial_count": sum(1 for item in results if item["Status"] == "Partial Info"),
        "significant_count": sum(1 for item in results if item["Status"] == "Significant Gap"),
        "critical_count": sum(1 for item in results if item["Status"] == "Critical Gap"),
        "gaps_found": sum(1 for item in results if item["Status"] != "Verified"),
        "compliance_score": round((sum(1 for item in results if item["Status"] == "Verified") / len(results)) * 100) if results else 0,
    }

    documents = []
    if questionnaire_path and os.path.exists(questionnaire_path):
        documents.append({
            "name": os.path.basename(questionnaire_path),
            "size": "questionnaire",
            "audit_score": 100 if summary["verified_count"] == len(results) else 0,
        })

    if os.path.isdir(target_directory):
        for file_name in sorted(os.listdir(target_directory)):
            if file_name.endswith((".txt", ".pdf", ".docx", ".json")) and not file_name.endswith(".csv"):
                documents.append({"name": file_name, "size": "local", "audit_score": 100 if summary["verified_count"] == len(results) else 0})

    return {
        "summary": summary,
        "results": results,
        "documents": documents,
    }


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/questions")
def questions():
    return jsonify({"questions": load_questions()})


@app.post("/api/rag")
def rag_endpoint():
    payload = request.get_json(silent=True) or {}
    questions_to_answer = payload.get("questions") or load_questions()
    if isinstance(questions_to_answer, str):
        questions_to_answer = [questions_to_answer]

    session_id = payload.get("session_id")
    results = []
    for question in questions_to_answer:
        result = run_rag_single(question, session_id=session_id)
        results.append(result)

    return jsonify({"results": results})


@app.get("/api/audit")
def audit_endpoint():
    questions_to_answer = load_questions()
    payload = build_audit_payload(
        questions_to_answer,
        questionnaire_path=find_questionnaire_csv(SAMPLE_DATA_DIR),
        target_directory=SAMPLE_DATA_DIR,
    )
    return jsonify(payload)


@app.post("/api/index-documents")
def index_documents_endpoint():
    policy_files = request.files.getlist("policy_files")
    if not policy_files:
        return jsonify({"error": "At least one policy file is required."}), 400

    session_id = get_request_session_id() or str(uuid.uuid4())
    indexed_files, active_session_id = index_uploaded_documents(policy_files, session_id=session_id)
    return jsonify({
        "success": True,
        "session_id": active_session_id,
        "indexed_files": indexed_files,
        "message": "Knowledge base indexed successfully.",
    })


@app.post("/api/audit")
def upload_audit_endpoint():
    session_id = get_request_session_id()
    policy_files = request.files.getlist("policy_files")
    questionnaire_file = request.files.get("questionnaire_file")

    if session_id:
        session_dir = os.path.join(UPLOAD_ROOT, session_id)
        os.makedirs(session_dir, exist_ok=True)
    else:
        session_id = str(uuid.uuid4())
        session_dir = os.path.join(UPLOAD_ROOT, session_id)
        os.makedirs(session_dir, exist_ok=True)

    if policy_files or questionnaire_file:
        session_id, session_dir, saved_policies, questionnaire_path = save_uploaded_files(
            policy_files,
            questionnaire_file,
            session_id=session_id,
        )
    else:
        saved_policies = []
        questionnaire_path = find_questionnaire_csv(session_dir)

    if not questionnaire_path:
        return jsonify({"error": "A questionnaire CSV is required."}), 400

    indexed_files, active_session_id = index_uploaded_documents(policy_files, session_id=session_id)

    questions_to_answer = load_questions(questionnaire_path)
    payload = build_audit_payload(
        questions_to_answer,
        session_id=active_session_id,
        questionnaire_path=questionnaire_path,
        target_directory=session_dir,
    )
    payload["session_id"] = active_session_id
    payload["session_dir"] = session_dir
    payload["saved_policies"] = saved_policies
    payload["indexed_files"] = indexed_files
    return jsonify(payload)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
