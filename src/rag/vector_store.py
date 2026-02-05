import faiss
from openai import OpenAI
import numpy as np

class VectorStore:
    
    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Initialize the vector store.
        
        Args:
            model: The OpenAI model to use for creating embeddings
        """
        self.model = model  
        
        self.index = None
        self.text_chunks = []
        
        self.client = OpenAI()

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        """
        Convert text into embeddings (lists of numbers that represent meaning).
        
        Args:
            texts: A list of text strings to convert
            
        Returns:
            A list of embeddings (numpy arrays), one for each input text
        """
        # Send texts to OpenAI to get embeddings
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        
        # Extract just the embedding arrays from the response
        # This loops through each embedding object and pulls out the .embedding property
        return [e.embedding for e in response.data]
    
    def build(self, texts: list[str]):
        """
        Build the vector store from a list of texts.
        
        Args:
            texts: A list of text strings to add to the vector store
        """
        # Get embeddings for all the texts
        embeddings = self.embed(texts)
        
        dimension = len(embeddings[0])  # Store the embedding size

        # Create a FAISS index - this is like a database optimized for finding similar vectors
        # IndexFlatL2 uses L2 distance (Euclidean distance) to measure similarity
        self.index = faiss.IndexFlatL2(dimension)
        # Convert embeddings to a numpy array of type float32 (required by FAISS)
        embedding_matrix = np.array(embeddings, dtype='float32')
        
        # Add the embeddings to the FAISS index
        self.index.add(embedding_matrix)
        
        # Store the original texts
        self.text_chunks = texts

    def search(self, query: str, top_k: int = 5) -> list[str]:
        """
        Search for the most similar texts to a given query.
        
        Args:
            query: The text query to search for
            top_k: How many results to return (default 5)
            
        Returns:
            A list of the most similar texts
        """
        query_embedding = self.embed([query])[0]
        
        # Search the FAISS index for similar vectors
        # D = distances, I = indices of the closest matches
        distances, indices = self.index.search(np.array([query_embedding]).astype("float32"), top_k)
        
        # Get the actual text for each matching index
        # Skip any invalid indices (marked as -1)
        results = [self.text_chunks[i] for i in indices[0] if i != -1]
        return results