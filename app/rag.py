"""Local document ingestion, embedding, persistence, and retrieval."""

import hashlib
import json
import math
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


class HashingEmbedder:
    """Deterministic, dependency-free embedding fallback for offline demos.

    Tokens and token bigrams are projected into a fixed-dimensional vector.
    This is less semantic than a transformer but remains a real vector
    retrieval pipeline and never requires a model download.
    """

    name = "hash"

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    @staticmethod
    def _tokens(text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def encode(self, texts: Sequence[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            tokens = self._tokens(text)
            features = tokens + [
                f"{left}_{right}" for left, right in zip(tokens, tokens[1:])
            ]
            vector = [0.0] * self.dimensions
            for feature in features:
                digest = hashlib.blake2b(
                    feature.encode("utf-8"), digest_size=8
                ).digest()
                raw = int.from_bytes(digest, "big")
                index = raw % self.dimensions
                vector[index] += 1.0 if raw & 1 else -1.0
            norm = math.sqrt(sum(value * value for value in vector))
            if norm:
                vector = [value / norm for value in vector]
            vectors.append(vector)
        return vectors


class SentenceTransformerEmbedder:
    """Optional higher-quality local embedding backend."""

    name = "sentence-transformers"

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Sequence[str]) -> List[List[float]]:
        values = self.model.encode(
            list(texts), normalize_embeddings=True, show_progress_bar=False
        )
        return [row.tolist() for row in values]


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


class RAGService:
    """Persisted local vector store for text files in the data directory."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        index_path: Optional[Path] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        embedding_backend: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> None:
        self.data_dir = Path(data_dir or settings.data_dir)
        self.index_path = Path(index_path or settings.vector_index_path)
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.requested_backend = (
            embedding_backend or settings.embedding_backend
        ).lower()
        self.min_score = settings.rag_min_score if min_score is None else min_score
        self._embedder = None
        self._lock = threading.RLock()

    def _get_embedder(self):
        if self._embedder is not None:
            return self._embedder
        if self.requested_backend in {"sentence-transformers", "transformer"}:
            try:
                self._embedder = SentenceTransformerEmbedder(settings.embedding_model)
                logger.info("Using sentence-transformers embedding backend")
            except Exception as exc:  # optional dependency/model may be unavailable
                logger.warning(
                    "Transformer embeddings unavailable (%s); using hash backend", exc
                )
                self._embedder = HashingEmbedder()
        else:
            self._embedder = HashingEmbedder()
        return self._embedder

    def _chunk_text(self, text: str) -> List[str]:
        paragraphs = [
            re.sub(r"\s+", " ", paragraph).strip()
            for paragraph in re.split(r"\n\s*\n", text)
            if paragraph.strip()
        ]
        chunks: List[str] = []
        current = ""
        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                if current:
                    chunks.append(current)
                    current = ""
                step = max(1, self.chunk_size - self.chunk_overlap)
                chunks.extend(
                    paragraph[start : start + self.chunk_size].strip()
                    for start in range(0, len(paragraph), step)
                    if paragraph[start : start + self.chunk_size].strip()
                )
                continue
            candidate = f"{current}\n\n{paragraph}".strip()
            if current and len(candidate) > self.chunk_size:
                chunks.append(current)
                overlap = current[-self.chunk_overlap :].strip()
                if len(current) > self.chunk_overlap:
                    # Avoid beginning the next chunk with a partial word.
                    overlap = re.sub(r"^\S+\s+", "", overlap, count=1)
                current = f"{overlap}\n\n{paragraph}".strip()
            else:
                current = candidate
        if current:
            chunks.append(current)
        return chunks

    def _source_files(self) -> List[Path]:
        if not self.data_dir.exists():
            return []
        return sorted(path for path in self.data_dir.glob("*.txt") if path.is_file())

    def ingest_documents(self) -> Dict[str, object]:
        """Read, chunk, embed, and persist every text file in ``data_dir``."""

        # Ingestion is atomic: the complete index is written to a temporary
        # file and renamed only after every readable document is processed.
        with self._lock:
            files = self._source_files()
            records: List[Dict[str, object]] = []
            for path in files:
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as exc:
                    logger.error("Could not read %s: %s", path, exc)
                    continue
                for chunk_id, chunk in enumerate(self._chunk_text(text)):
                    records.append(
                        {
                            "source": path.name,
                            "chunk_id": chunk_id,
                            "text": chunk,
                            "text_preview": chunk[:160],
                        }
                    )

            embedder = self._get_embedder()
            if records:
                embeddings = embedder.encode([record["text"] for record in records])
                for record, embedding in zip(records, embeddings):
                    record["embedding"] = embedding

            payload = {
                "version": 1,
                "embedding_backend": embedder.name,
                "documents": len(files),
                "chunks": records,
            }
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self.index_path.with_suffix(".tmp")
            temporary_path.write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
            temporary_path.replace(self.index_path)
            logger.info("Ingested %d files into %d chunks", len(files), len(records))
            return {
                "status": "success" if files else "no_documents",
                "documents": len(files),
                "chunks": len(records),
                "embedding_backend": embedder.name,
                "sources": [path.name for path in files],
            }

    def _load_index(self) -> Optional[Dict[str, object]]:
        if not self.index_path.exists():
            return None
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Could not load vector index: %s", exc)
            return None

    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, object]]:
        """Return the most similar stored chunks with metadata and scores."""

        if not query.strip():
            return []
        with self._lock:
            index = self._load_index()
            if not index or not index.get("chunks"):
                return []
            stored_backend = str(index.get("embedding_backend", "hash"))
            if stored_backend != self._get_embedder().name:
                logger.warning(
                    "Index uses %s but runtime uses %s; rebuild with /ingest",
                    stored_backend,
                    self._get_embedder().name,
                )
                return []
            query_vector = self._get_embedder().encode([query])[0]
            stop_words = {
                "a",
                "an",
                "and",
                "are",
                "for",
                "in",
                "is",
                "of",
                "the",
                "to",
                "what",
            }
            query_terms = {
                token
                for token in HashingEmbedder._tokens(query)
                if token not in stop_words
            }
            ranked = []
            for record in index["chunks"]:
                vector_score = _cosine_similarity(query_vector, record["embedding"])
                document_terms = set(HashingEmbedder._tokens(record["text"]))
                lexical_score = (
                    len(query_terms & document_terms) / len(query_terms)
                    if query_terms
                    else 0.0
                )
                # Hash embeddings are lexical projections, so a zero-overlap
                # match is only a hash collision, not semantic evidence.
                if stored_backend == "hash" and lexical_score == 0.0:
                    continue
                # A lexical signal stabilizes exact protocol terms, visit numbers,
                # and abbreviations while vector similarity handles broader phrasing.
                score = vector_score + (0.35 * lexical_score)
                ranked.append(
                    {
                        "source": record["source"],
                        "chunk_id": record["chunk_id"],
                        "text": record["text"],
                        "text_preview": record["text_preview"],
                        "score": round(float(score), 4),
                    }
                )
            ranked.sort(key=lambda item: item["score"], reverse=True)
            # A minimum relevance threshold prevents an unrelated question
            # from receiving arbitrary chunks merely because an index exists.
            relevant = [item for item in ranked if item["score"] >= self.min_score]
            return relevant[: max(1, top_k)]

    def get_all_documents(self) -> List[Dict[str, object]]:
        """Return all indexed chunks without their embedding vectors."""

        with self._lock:
            index = self._load_index()
            if not index:
                return []
            return [
                {
                    "source": record["source"],
                    "chunk_id": record["chunk_id"],
                    "text": record["text"],
                    "text_preview": record["text_preview"],
                }
                for record in index.get("chunks", [])
            ]

    def is_ingested(self) -> bool:
        index = self._load_index()
        return bool(index and index.get("chunks"))


rag_service = RAGService()


def ingest_documents() -> Dict[str, object]:
    return rag_service.ingest_documents()


def search_documents(query: str, top_k: int = 5) -> List[Dict[str, object]]:
    return rag_service.search_documents(query, top_k)


def get_all_documents() -> List[Dict[str, object]]:
    return rag_service.get_all_documents()


def is_index_ready() -> bool:
    return rag_service.is_ingested()
