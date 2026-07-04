import hashlib
import math
import re
from typing import Iterable

import numpy as np


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def embed_text(text: str, dim: int = 384) -> list[float]:
    """Deterministic local embedding for demo mode (no API key required)."""
    tokens = _tokenize(text)
    vector = np.zeros(dim, dtype=np.float32)
    if not tokens:
        return vector.tolist()

    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        for i in range(dim):
            byte_val = digest[i % len(digest)]
            vector[i] += (byte_val / 255.0) - 0.5

    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()


def cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    va = np.array(list(a), dtype=np.float32)
    vb = np.array(list(b), dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


async def get_embedding(text: str) -> list[float]:
    from config import get_settings

    settings = get_settings()
    if settings.has_openai_key and settings.embedding_provider == "openai":
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.embeddings.create(
                model=settings.openai_embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except Exception:
            pass
    return embed_text(text)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def keyword_overlap_score(text_a: str, text_b: str) -> float:
    tokens_a = set(_tokenize(text_a))
    tokens_b = set(_tokenize(text_b))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    jaccard = len(intersection) / len(union)
    return min(1.0, jaccard * 2.5)
