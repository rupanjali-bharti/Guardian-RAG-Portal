import os
from groq import Groq
from dotenv import load_dotenv

# 1. LOAD THE ENVIRONMENT FIRST
load_dotenv()

# 2. GET THE KEY AND CHECK IF IT EXISTS
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Check your .env file.")

# 3. NOW INITIALIZE THE CLIENT
client = Groq(api_key=api_key)

def run_rag_single(question):
    # Retrieve local context from your sample_data folder [cite: 26-30]
    context_files = ["security_policy.txt", "compliance_and_privacy.txt", "corporate_directory.txt"]
    context_parts = []
    base_path = os.path.join(os.path.dirname(__file__), "sample_data")
    
    for file_name in context_files:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                context_parts.append(f.read())
    
    context = "\n\n".join(context_parts) if context_parts else "No local documents found."

    # Generate answer using Llama 3 on Groq
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a Security Auditor. Answer based ONLY on the provided context. Use for citations where X is the number in the text."
                },
                {
                    "role": "user",
                    "content": f"Context: {context}\n\nQuestion: {question}",
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        return {
            "Question": question,
            "Answer": chat_completion.choices[0].message.content,
            "Citation": "Extracted from internal policy documents"
        }
    except Exception as e:
        return {
            "Question": question,
            "Answer": f"Groq API Error: {str(e)}",
            "Citation": "N/A"
        }