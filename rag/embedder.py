import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# The HF_TOKEN is used here to authenticate your request to Hugging Face
# it helps avoid rate limits and ensures faster model verification.
hf_token = os.getenv("HF_TOKEN")

class Embedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Initializes the embedding model. 
        The first time this runs, it will download the model weights.
        """
        self.model = SentenceTransformer(model_name, use_auth_token=hf_token)

    def get_embeddings(self, text_list):
        """
        Converts a list of text strings into a list of vector embeddings.
        """
        # Ensure input is a list
        if isinstance(text_list, str):
            text_list = [text_list]
            
        embeddings = self.model.encode(text_list)
        return embeddings.tolist()

# Global instance for easy importing
embedder_instance = Embedder()