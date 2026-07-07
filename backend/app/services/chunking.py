"""
This module is used to chunk the text into smaller chunks.
"""

from typing import List


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks (sentence-aware)."""
    if len(text) <= chunk_size:
        return [text]

    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            last_part = text[max(start, end - 100):end]
            sentence_end = max(last_part.rfind('.'), last_part.rfind('!'), last_part.rfind('?'))
            if sentence_end > -1:
                end = max(start, end - 100) + sentence_end + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break

    return chunks
