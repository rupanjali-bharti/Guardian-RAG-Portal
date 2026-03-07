import os
from groq import Groq
from dotenv import load_dotenv
import re

# 1. LOAD THE ENVIRONMENT FIRST
load_dotenv()

# 2. GET THE KEY AND CHECK IF IT EXISTS
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Check your .env file.")

# 3. NOW INITIALIZE THE CLIENT
client = Groq(api_key=api_key)


def run_rag_single(question):
    # 1. Load all potential context files [cite: 17-25, 26-30]
    context_files = ["security_policy.txt", "compliance_and_privacy.txt", "corporate_directory.txt", "data_retention_policy.txt"]
    base_path = os.path.join(os.path.dirname(__file__), "sample_data")
    
    # We prefix each document with its filename so the AI knows where the info is from
    context_parts = []
    for file_name in context_files:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                context_parts.append(f"--- DOCUMENT: {file_name} ---\n{f.read()}")
    
    context = "\n\n".join(context_parts)

    # 2. Update the System Prompt to force source tracking 
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
        
        # 3. Use Regex to separate the Answer from the Citations
        # This looks for the SOURCES_USED: [...] pattern we told the AI to use
        source_match = re.search(r"SOURCES_USED:\s*\[(.*?)\]", full_text)
        
        if source_match:
            clean_citation = source_match.group(1)
            # Remove the tag from the final answer shown to the user
            clean_answer = full_text.replace(source_match.group(0), "").strip()
        else:
            clean_citation = "General Context"
            clean_answer = full_text

        return {
            "Question": question,
            "Answer": clean_answer,
            "Citation": clean_citation
        }
    except Exception as e:
        return {"Question": question, "Answer": f"Error: {e}", "Citation": "N/A"}
    """
    Retrieves context from multiple local files and tracks 
    their names for dynamic citations.
    """
    context_files = ["security_policy.txt", "compliance_and_privacy.txt", "corporate_directory.txt", "data_retention_policy.txt"]
    context_parts = []
    used_sources = [] # Track which files we actually found and used
    
    base_path = os.path.join(os.path.dirname(__file__), "sample_data")
    
    for file_name in context_files:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                context_parts.append(f.read())
                used_sources.append(file_name) # Add to our citation list 
    
    context = "\n\n".join(context_parts) if context_parts else "No local documents found."

    # Prompting Groq/Gemini [cite: 26-30]
    prompt = f"Context: {context}\n\nQuestion: {question}"
    
    try:
        # Assuming you are using the Groq client we set up earlier
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a Security Auditor. Answer based ONLY on the provided context."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
        )
        
        # JOIN ALL USED SOURCES: This turns ['file1.txt', 'file2.txt'] into "file1.txt, file2.txt"
        citation_str = ", ".join(used_sources) if used_sources else "Unknown Source"

        return {
            "Question": question,
            "Answer": response.choices[0].message.content,
            "Citation": citation_str # This will now show all docs! [cite: 1-10]
        }
    except Exception as e:
        return {"Question": question, "Answer": f"Error: {e}", "Citation": "N/A"}