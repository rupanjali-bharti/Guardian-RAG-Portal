import os
import csv
from flask import Flask, jsonify, request
from main_rag import run_rag_single

app = Flask(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DATA_DIR = os.path.join(CURRENT_DIR, "sample_data")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def load_questions():
    csv_path = os.path.join(SAMPLE_DATA_DIR, "ques1.csv")
    if not os.path.exists(csv_path):
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


def build_audit_payload(questions):
    results = []
    for question in questions:
        result = run_rag_single(question)
        answer_text = str(result.get("Answer", "")).strip()
        citation_text = str(result.get("Citation", "")).strip()
        answer_lower = answer_text.lower()

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

    return {
        "summary": summary,
        "results": results,
        "documents": [
            {
                "name": file_name,
                "size": "local",
            }
            for file_name in sorted(os.listdir(SAMPLE_DATA_DIR))
            if file_name.endswith((".txt", ".pdf", ".docx", ".json")) and file_name != "ques1.csv"
        ],
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

    results = []
    for question in questions_to_answer:
        result = run_rag_single(question)
        results.append(result)

    return jsonify({"results": results})


@app.get("/api/audit")
def audit_endpoint():
    questions_to_answer = load_questions()
    payload = build_audit_payload(questions_to_answer)
    return jsonify(payload)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
