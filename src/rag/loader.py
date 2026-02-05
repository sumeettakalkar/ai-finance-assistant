from pathlib import Path
from typing import List, Dict

def load_documents(data_dir: str = "documents/articles") -> List[Dict]:
    """
    Load text documents from a specified directory.

    Args:
        directory_path (str): The path to the directory containing text files.  
    Returns:
        List[Dict]: A list of dictionaries, each containing the filename and content of a text file.
    """
    documents = []
    for file_path in Path(data_dir).glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")
        documents.append({
            "text": text,
            "source": file_path.stem
        })
    return documents

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into chunks of specified size with overlap.

    Args:
        text (str): The text to be chunked.
        chunk_size (int): The size of each chunk.
        overlap (int): The number of overlapping characters between chunks.

    Returns:
        List[str]: A list of text chunks.
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        start += chunk_size - overlap
    
    return chunks