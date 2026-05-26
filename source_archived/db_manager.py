"""
[ARCHIVED] Document database manager — legacy prototype v0.

This module was the original document ingestion and retrieval
implementation. It used LangChain, FAISS, and HuggingFace sentence
embeddings to index PDFs and answer questions via an OpenAI ChatLLM.

Status
------
Superseded by ``backend/app/rag_loader.py``, which uses a lightweight
TF-IDF pipeline (scikit-learn) and supports llama.cpp and Ollama as
fully local LLM backends — no cloud APIs required.

This file is kept for historical reference only. Do not run or extend it.
"""

import hashlib
import json
import os

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import VectorStore
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

# SECURITY NOTE: The original prototype contained a hardcoded API key.
# That key has been removed. Set the OPENAI_API_KEY environment variable
# if you need to restore OpenAI connectivity (not recommended for this project).
OPEN_AI_KEY = os.getenv("OPENAI_API_KEY", "")


class DBManager:
    """
    [ARCHIVED] PDF ingestion, FAISS indexing, and LLM-powered retrieval.

    Scans a directory for PDF files, splits them into chunks with
    LangChain's ``RecursiveCharacterTextSplitter``, stores embeddings
    in a FAISS vector store, and answers queries through a LangChain
    retrieval chain backed by an OpenAI ChatLLM.

    MD5 hashes of processed files are persisted in ``file_map.json``
    to avoid re-ingesting unchanged PDFs on subsequent runs.

    .. deprecated::
        Use ``backend/app/rag_loader.py`` instead.

    Attributes:
        vector_store (VectorStore | None): FAISS index loaded from disk,
            or ``None`` if the index files are not found.
        chunk_size (int): Character chunk size for the text splitter.
        chunk_overlap (int): Character overlap between consecutive chunks.
        folder_path (str): Directory scanned for PDF source files.
        db_path (str): Directory where FAISS index files are persisted.
        file_map (dict[str, str]): Maps absolute file paths to their MD5
            hashes for change detection.
        file_map_path (str): Absolute path to the ``file_map.json`` cache.
        hf_embeddings (HuggingFaceEmbeddings): Sentence embedding model
            used to vectorise document chunks.
    """

    def __init__(
        self,
        folder_path: str,
        db_path: str,
        chunk_size: int,
        chunk_overlap: int,
    ):
        """
        Initialise the manager and load an existing FAISS index if present.

        Reads ``file_map.json`` from ``db_path`` to restore the hash map.
        Attempts to load ``index.faiss`` and ``index.pkl`` from ``db_path``
        if both files are present.

        Args:
            folder_path (str): Directory containing source PDF files.
            db_path (str): Directory for persisting the FAISS index and
                the ``file_map.json`` change-detection cache.
            chunk_size (int): Character size of each text chunk fed to
                the embedding model.
            chunk_overlap (int): Overlap in characters between adjacent
                chunks to preserve boundary context.
        """
        self.vector_store: VectorStore = None
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.folder_path = folder_path
        self.db_path = db_path
        self.file_map: dict[str, str] = {}

        self.file_map_path = os.path.join(self.db_path, "file_map.json")
        if os.path.exists(self.file_map_path):
            with open(self.file_map_path, "r") as f:
                self.file_map = json.load(f)

        self.hf_embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        if os.path.exists(self.db_path):
            faiss_file = os.path.join(self.db_path, "index.faiss")
            pkl_file = os.path.join(self.db_path, "index.pkl")
            if os.path.exists(faiss_file) and os.path.exists(pkl_file):
                try:
                    self.vector_store = FAISS.load_local(
                        self.db_path,
                        embeddings=self.hf_embeddings,
                        allow_dangerous_deserialization=True,
                    )
                except Exception as exc:
                    print(f"Failed to load FAISS vector store: {exc}")

    def check_if_file_updated(self, file_path: str) -> bool:
        """
        Return ``True`` if the file is unchanged since last ingestion.

        Compares the file's current MD5 hash against the value stored in
        ``self.file_map``. A ``True`` result means the file can be skipped.

        Args:
            file_path (str): Absolute path to the file to check.

        Returns:
            bool: ``True`` if the stored hash matches the current hash
                (file is unchanged); ``False`` if the file is new or
                has been modified.
        """
        file_hash = self.get_md5_hash(file_path)
        stored = self.file_map.get(file_path)
        return stored is not None and stored == file_hash

    def get_md5_hash(self, file_path: str) -> str:
        """
        Compute the MD5 hash of a file's binary content.

        Args:
            file_path (str): Absolute path to the file.

        Returns:
            str: Hexadecimal MD5 digest (32 characters).
        """
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def load_documents(self) -> None:
        """
        Ingest new or changed PDF files into the FAISS vector store.

        Walks ``folder_path`` recursively, skipping files whose MD5
        hash has not changed. For each changed file: loads pages via
        ``PyMuPDFLoader``, splits them with
        ``RecursiveCharacterTextSplitter``, and adds the resulting
        documents to the vector store.

        Updates and persists ``file_map.json`` after ingestion.
        """
        if not (os.path.exists(self.db_path) and os.path.exists(self.folder_path)):
            return

        updated_files = [
            os.path.join(root, fname)
            for root, _, files in os.walk(self.folder_path)
            for fname in files
            if fname.endswith(".pdf")
            and not self.check_if_file_updated(os.path.join(root, fname))
        ]

        print("Files to be parsed:")
        print("\n".join(updated_files))

        all_documents = []
        for file_path in updated_files:
            loader = PyMuPDFLoader(file_path)
            pages = loader.load()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
            all_documents.extend(splitter.split_documents(pages))

        for file_path in updated_files:
            self.file_map[file_path] = self.get_md5_hash(file_path)

        with open(self.file_map_path, "w") as f:
            json.dump(self.file_map, f)

        if all_documents:
            self.vector_store.add_documents(all_documents, embedding=self.hf_embeddings)

    def save_document(self) -> None:
        """
        Persist the in-memory FAISS index to ``db_path``.

        A no-op if the vector store has not been initialised or
        ``db_path`` does not exist.
        """
        if self.vector_store is not None and os.path.exists(self.db_path):
            self.vector_store.save_local(self.db_path)

    def query_document(self, query_string: str, call_llm: bool = True):
        """
        Query the FAISS index, optionally with OpenAI LLM synthesis.

        When ``call_llm=True`` a LangChain retrieval chain is constructed
        from a FAISS retriever and a ChatOpenAI model. The chain returns
        a dict containing the answer and source documents.

        When ``call_llm=False`` raw FAISS similarity search results are
        returned without LLM processing.

        Args:
            query_string (str): The user's question.
            call_llm (bool): If ``True`` (default), run the full RAG
                chain. If ``False``, return the raw similarity-search
                documents.

        Returns:
            dict | list: LangChain response dict (``call_llm=True``) or
                a list of LangChain ``Document`` objects (``call_llm=False``).
        """
        if call_llm:
            llm = ChatOpenAI(openai_api_key=OPEN_AI_KEY)
            retriever = self.vector_store.as_retriever()
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Answer using the given context."),
                ("human", "Context:\n{context}\n\nQuestion: {input}"),
            ])
            combine_chain = create_stuff_documents_chain(llm, prompt)
            retrieval_chain = create_retrieval_chain(
                retriever=retriever,
                combine_docs_chain=combine_chain,
            )
            return retrieval_chain.invoke({"input": query_string})
        else:
            return self.vector_store.similarity_search(query_string)
