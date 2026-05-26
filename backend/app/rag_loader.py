"""
Document loading, chunking, TF-IDF indexing, and retrieval.

RAGLoader is the core of the retrieval pipeline. It reads ``.md`` and
``.txt`` files from a data directory, splits them into overlapping
character chunks, builds a TF-IDF matrix with scikit-learn, and ranks
chunks by cosine similarity at query time.

Optionally, the top-ranked chunks are passed to an LLM runner
(LLMRunner or OllamaRunner) to synthesise a natural-language answer.
"""

import os

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RAGLoader:
    """
    TF-IDF retrieval pipeline with optional LLM synthesis.

    On construction the loader immediately indexes all documents found
    in ``data_dir``. The index is rebuilt whenever a new document is
    added or an explicit reindex is requested.

    Supported file extensions: ``.md``, ``.txt``.

    Attributes:
        data_dir (str): Directory scanned for source documents.
        storage_dir (str): Directory reserved for cache files
            (reserved for future persistent storage; not used by TF-IDF).
        llm_runner: Optional LLMRunner or OllamaRunner instance used for
            answer synthesis. ``None`` disables LLM mode.
        chunks (list[dict]): Flat list of all indexed chunks.
            Each chunk contains ``source``, ``chunk_id``, and ``text``.
        vectorizer (TfidfVectorizer | None): Fitted TF-IDF vectorizer,
            or ``None`` when no documents are indexed.
        tfidf_matrix: Sparse TF-IDF matrix aligned with ``self.chunks``,
            or ``None`` when no documents are indexed.
    """

    def __init__(self, data_dir: str, storage_dir: str, llm_runner=None):
        """
        Initialise the loader and trigger an initial reindex.

        Args:
            data_dir (str): Path to the directory containing source
                documents (``.md`` / ``.txt`` files).
            storage_dir (str): Path to a directory for cache files.
                The directory is created if it does not exist.
            llm_runner: Optional runner instance (LLMRunner or
                OllamaRunner). When supplied and ``use_llm=True`` is
                passed to :meth:`query`, the runner is used to generate
                a synthesised answer. Default: ``None``.
        """
        self.data_dir = data_dir
        self.storage_dir = storage_dir
        self.llm_runner = llm_runner
        self.chunks: list[dict] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.tfidf_matrix = None

        self.reindex()

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def reindex(self) -> dict:
        """
        Reload all documents from disk and rebuild the TF-IDF index.

        Scans ``data_dir`` for supported files, splits each file into
        overlapping chunks, and fits a new TF-IDF vectorizer over the
        full corpus. Any previous index is discarded.

        Returns:
            dict: A summary with keys:
                - ``status`` (str): Always ``"reindexed"``.
                - ``documents`` (int): Number of unique source files indexed.
                - ``chunks`` (int): Total number of chunks indexed.
        """
        documents = self._load_documents()

        self.chunks = []
        for doc in documents:
            self.chunks.extend(self._chunk_text(doc["source"], doc["text"]))

        if self.chunks:
            texts = [c["text"] for c in self.chunks]
            self.vectorizer = TfidfVectorizer()
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        else:
            self.vectorizer = None
            self.tfidf_matrix = None

        sources = {c["source"] for c in self.chunks}
        return {
            "status": "reindexed",
            "documents": len(sources),
            "chunks": len(self.chunks),
        }

    def query(self, question: str, use_llm: bool = False) -> str:
        """
        Retrieve relevant context for a question, with optional LLM synthesis.

        In retrieval-only mode (``use_llm=False``) the top-ranked chunks
        are returned as a numbered, formatted string.

        In LLM mode (``use_llm=True``) the chunks are assembled into a
        RAG prompt and forwarded to the configured LLM runner.

        Args:
            question (str): The user's question. Must be non-empty.
            use_llm (bool): If ``True``, synthesise an answer using the
                LLM runner. If ``False`` (default), return raw retrieved
                context.

        Returns:
            str: Formatted retrieval results, a synthesised answer, or
                an informative message when no results are found or the
                LLM is unavailable.
        """
        if not question or not question.strip():
            return "Please enter a question."

        results = self._retrieve(question)
        if not results:
            return "No documents are indexed yet, or no matching context was found."

        if not use_llm:
            lines = ["Top retrieved context:\n"]
            for i, chunk in enumerate(results, 1):
                lines.append(
                    f"{i}. Source: {chunk['source']} (score: {chunk['score']:.4f})\n"
                    f"{chunk['text']}\n"
                )
            return "\n".join(lines)

        if self.llm_runner is None:
            return (
                "LLM is not enabled. Set ENABLE_LLM=true and configure "
                "MODEL_PATH (llama_cpp) or OLLAMA_MODEL (ollama) to use "
                "LLM synthesis."
            )

        context = "\n\n".join(
            [f"[{c['source']}]\n{c['text']}" for c in results]
        )
        prompt = (
            "Use the following context to answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        try:
            return self.llm_runner.query(prompt)
        except Exception as exc:
            return f"LLM query failed: {exc}"

    def list_available_documents(self) -> list[dict]:
        """
        Return a summary of all currently indexed documents.

        Returns:
            list[dict]: One entry per unique source file, each with:
                - ``source`` (str): Filename of the document.
                - ``chunks`` (int): Number of chunks indexed from that file.
        """
        counts: dict[str, int] = {}
        for chunk in self.chunks:
            src = chunk["source"]
            counts[src] = counts.get(src, 0) + 1
        return [{"source": src, "chunks": count} for src, count in counts.items()]

    def add_document(self, source: str, text: str) -> dict:
        """
        Write a new document to ``data_dir`` and rebuild the index.

        Args:
            source (str): Filename for the document (e.g. ``"my-note.md"``).
                Must be a plain filename, not a path.
            text (str): Full text content to write and index.

        Returns:
            dict: A result dict with keys:
                - ``status`` (str): Always ``"indexed"`` on success.
                - ``source`` (str): The filename that was written.
                - ``chunks`` (int): Number of chunks indexed from this file.

        Raises:
            ValueError: If ``source`` or ``text`` is empty.
        """
        if not source or not source.strip():
            raise ValueError("Document source is required.")
        if not text or not text.strip():
            raise ValueError("Document text is required.")

        os.makedirs(self.data_dir, exist_ok=True)
        file_path = os.path.join(self.data_dir, source)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        self.reindex()

        chunks_for_source = sum(1 for c in self.chunks if c["source"] == source)
        return {"status": "indexed", "source": source, "chunks": chunks_for_source}

    # ──────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────

    def _load_documents(self) -> list[dict]:
        """
        Scan ``data_dir`` and read all supported documents.

        Walks the directory tree recursively. Files with extensions
        ``.md`` or ``.txt`` are read as UTF-8 text. Read errors are
        logged and skipped rather than raising.

        Returns:
            list[dict]: One entry per file, each with keys:
                - ``source`` (str): Bare filename (no path).
                - ``text`` (str): Full file content.
        """
        supported_exts = {".md", ".txt"}
        docs: list[dict] = []

        if not os.path.exists(self.data_dir):
            return docs

        for root, _, files in os.walk(self.data_dir):
            for fname in sorted(files):
                ext = os.path.splitext(fname)[1].lower()
                if ext not in supported_exts:
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        text = f.read()
                    docs.append({"source": fname, "text": text})
                except Exception as exc:
                    print(f"RAGLoader: failed to read {fpath}: {exc}")

        return docs

    def _chunk_text(self, source: str, text: str) -> list[dict]:
        """
        Split a document into overlapping fixed-size character chunks.

        Uses a chunk size of 1 000 characters with a 175-character
        overlap so that context at chunk boundaries is not lost.

        Args:
            source (str): Source filename, stored on each chunk for
                attribution in retrieval results.
            text (str): Full document text to split.

        Returns:
            list[dict]: Ordered list of chunks, each with keys:
                - ``source`` (str): Source filename.
                - ``chunk_id`` (int): Zero-based sequence number within
                  the document.
                - ``text`` (str): Chunk text (up to 1 000 characters).
        """
        chunk_size = 1000
        overlap = 175
        chunks: list[dict] = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            if chunk_text.strip():
                chunks.append(
                    {
                        "source": source,
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                    }
                )
                chunk_id += 1
            if end >= len(text):
                break
            start = end - overlap

        return chunks

    def _retrieve(self, question: str, top_k: int = 5) -> list[dict]:
        """
        Rank indexed chunks by TF-IDF cosine similarity to a question.

        Args:
            question (str): User question used as the query vector.
            top_k (int): Maximum number of chunks to return. Default: 5.
                Only chunks with a positive similarity score are included.

        Returns:
            list[dict]: Up to ``top_k`` chunks sorted by descending
                similarity score. Each dict contains the chunk fields
                (``source``, ``chunk_id``, ``text``) plus:
                - ``score`` (float): Cosine similarity score (0–1).
                Returns an empty list if no documents are indexed or all
                scores are zero.
        """
        if self.vectorizer is None or self.tfidf_matrix is None or not self.chunks:
            return []

        q_vec = self.vectorizer.transform([question])
        scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: list[dict] = []
        for idx in top_indices:
            if scores[idx] > 0:
                chunk = dict(self.chunks[idx])
                chunk["score"] = float(scores[idx])
                results.append(chunk)

        return results
