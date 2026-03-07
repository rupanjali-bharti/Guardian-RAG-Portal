import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

# Using your preferred Qwen 2.5 model (Stable for 2026 Chat tasks)
HF_TOKEN = os.getenv("HF_TOKEN")
client = InferenceClient(api_key=HF_TOKEN)
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

def generate_answer(question, context_list):
    """
    Uses your established Hugging Face InferenceClient logic 
    to generate grounded compliance answers.
    """
    if not context_list:
        return "Not found in references.", "N/A"

    # Format the context from your vector search
    context_text = "\n\n".join([f"Source: {c['source']}\nContent: {c['text']}" for c in context_list])
    
    try:
        # Using chat_completion as in your reference for better instruction following
        response = client.chat_completion(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional compliance assistant. Answer ONLY using the provided context."
                },
                {
                    "role": "user", 
                    "content": f"Context:\n{context_text}\n\nQuestion: {question}"
                }
            ],
            max_tokens=512,
            temperature=0.1 # Keep low for accuracy
        )
        
        answer = response.choices[0].message.content
        citation = context_list[0]['source']
        return answer, citation
        
    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg:
            return "The AI model is currently loading on Hugging Face. Please retry in 30 seconds.", "Error"
        return f"Hugging Face Error: {error_msg}", "Error"