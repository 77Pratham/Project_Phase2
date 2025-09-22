# rag_engine.py
import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import google.generativeai as genai
from contextlib import redirect_stderr

class RAGEngine:
    def __init__(self, knowledge_path="knowledge_base", index_file="faiss_index.pkl"):
        self.knowledge_path = knowledge_path
        self.index_file = index_file
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.text_chunks = []

    def build_index(self):
        texts = []
        for file in os.listdir(self.knowledge_path):
            if file.endswith(".txt"):
                with open(os.path.join(self.knowledge_path, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    # split into chunks
                    chunks = [content[i:i+500] for i in range(0, len(content), 500)]
                    texts.extend(chunks)

        if not texts:
            print("No .txt files found in knowledge_base.")
            return

        embeddings = self.model.encode(texts, convert_to_numpy=True)
        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)
        self.text_chunks = texts

        # Save index + chunks
        with open(self.index_file, "wb") as f:
            pickle.dump((self.index, self.text_chunks), f)

        print("FAISS index built and saved.")

    def load_index(self):
        if os.path.exists(self.index_file):
            with open(self.index_file, "rb") as f:
                self.index, self.text_chunks = pickle.load(f)
            print("FAISS index loaded.")
        else:
            print("No index found. Please run build_index() first.")

    def get_context(self, query, top_k=1):
        if not self.index:
            self.load_index()
        if not self.index:
            return "No index available."

        query_vec = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_vec, top_k)

        results = [self.text_chunks[i] for i in indices[0] if i < len(self.text_chunks)]
        return results[0] if results else "No relevant context found."
    
    def answer_query(self, query):
        context = self.get_context(query)
        if not context or context == "No relevant context found.":
            prompt = f"""You are an AI assistant. 
The user asked: {query} 
Answer the question directly, even if no external context is provided."""
        else:
            # ✅ Use retrieved context
            prompt = f"""You are an AI assistant. Use the context below to answer the question clearly and concisely.

Context:
{context}

Question: {query}"""

        # Suppress the C++ logs by redirecting stderr
        with open(os.devnull, 'w') as devnull:
            with redirect_stderr(devnull):
                try:
                    # Configure the API key
                    genai.configure(api_key=os.getenv("AIzaSyDYZCbstkr7GWhPMU_A6qdYYYKHbDJuSI4"))
                    
                    # Create the model and generate content
                    model = genai.GenerativeModel('gemini-1.5-flash-latest')
                    response = model.generate_content(prompt)
                    
                    # Return the text from the response
                    return response.text.strip()
                    
                except Exception as e:
                    # NOTE: Real errors will be suppressed too.
                    # For debugging, temporarily remove the 'with' blocks above.
                    print(f"An error occurred: {e}")
                    return "Sorry, I encountered an error while trying to generate a response."



