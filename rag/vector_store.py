"""Small FAISS vector store with local TF-IDF or IBM watsonx embeddings."""
import pickle
from pathlib import Path

import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from config import (
    STORAGE_DIR,
    WATSONX_API_KEY,
    WATSONX_EMBEDDING_MODEL_ID,
    WATSONX_PROJECT_ID,
    WATSONX_URL,
)


class NutritionVectorStore:
    """Store document vectors and return the most similar documents for a query."""

    def __init__(self, provider: str = "local"):
        if provider not in {"local", "watsonx"}:
            raise ValueError("Embedding provider must be 'local' or 'watsonx'.")
        self.provider = provider
        self.documents = []
        self.index = None
        self.vectorizer = None
        self.embedding_client = None

    def _watsonx_embeddings(self, texts: list[str]) -> np.ndarray:
        """Call IBM Slate embeddings through the official watsonx SDK."""
        if self.embedding_client is None:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import Embeddings

            credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
            self.embedding_client = Embeddings(
                model_id=WATSONX_EMBEDDING_MODEL_ID,
                credentials=credentials,
                project_id=WATSONX_PROJECT_ID,
            )
        vectors = self.embedding_client.embed_documents(texts=texts)
        return np.asarray(vectors, dtype="float32")

    def _embed_documents(self, texts: list[str]) -> np.ndarray:
        if self.provider == "watsonx":
            return self._watsonx_embeddings(texts)
        self.vectorizer = TfidfVectorizer(
            lowercase=True, stop_words="english", ngram_range=(1, 2), sublinear_tf=True
        )
        return self.vectorizer.fit_transform(texts).toarray().astype("float32")

    def _embed_query(self, text: str) -> np.ndarray:
        if self.provider == "watsonx":
            return self._watsonx_embeddings([text])
        if self.vectorizer is None:
            raise RuntimeError("Build the vector index before searching.")
        return self.vectorizer.transform([text]).toarray().astype("float32")

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors so FAISS inner product behaves as cosine similarity."""
        vectors = np.asarray(vectors, dtype="float32")
        if vectors.ndim != 2 or vectors.shape[0] == 0:
            raise ValueError("Embedding generation returned no usable vectors.")
        faiss.normalize_L2(vectors)
        return vectors

    def build(self, documents: list[dict]) -> None:
        """Create an in-memory FAISS index from dictionaries with text and metadata."""
        if not documents:
            raise ValueError("At least one knowledge document is required.")
        self.documents = documents
        vectors = self._normalize(self._embed_documents([doc["text"] for doc in documents]))
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Return ranked results with cosine-like scores and traceable metadata."""
        if self.index is None or not query.strip():
            return []
        query_vector = self._normalize(self._embed_query(query))
        top_k = max(1, min(int(top_k), len(self.documents)))
        scores, indices = self.index.search(query_vector, top_k)
        results = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue
            document = self.documents[index]
            results.append({
                "id": document["id"],
                "text": document["text"],
                "metadata": document["metadata"],
                "score": round(float(score), 4),
            })
        return results

    def save_local(self, directory: Path = STORAGE_DIR) -> None:
        """Optionally persist a local index for inspection; app rebuilds it on startup."""
        if self.provider != "local" or self.index is None:
            raise ValueError("Only a built local index can be saved with this helper.")
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / "nutrition.faiss"))
        with (directory / "local_index.pkl").open("wb") as file:
            pickle.dump({"documents": self.documents, "vectorizer": self.vectorizer}, file)
