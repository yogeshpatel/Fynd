import hashlib
import os

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json

class DBManager:

    def __init__(self, folder_path, db_path ,chunk_size , chunk_overlap):
        self.vector_store : VectorStore = None
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.folder_path = folder_path
        self.db_path = db_path

        self.hf_embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Check if db_path exists and required FAISS files are present
        if os.path.exists(self.db_path):
            faiss_file = os.path.join(self.db_path, "index.faiss")
            pkl_file = os.path.join(self.db_path, "index.pkl")
            if os.path.exists(faiss_file) and os.path.exists(pkl_file):
                try:
                    self.vector_store = FAISS.load_local(self.db_path, embeddings=self.hf_embeddings,allow_dangerous_deserialization=True)
                except Exception as e:
                    print(f"Failed to load FAISS vector store: {e}")

    def check_if_file_updated(self,file_path, md5_hash):
    # Check if the file has been updated by comparing its MD5 hash with the existing one
        existing_md5_hash = self.get_existing_md5_hash(file_path)
        return existing_md5_hash != md5_hash

    def get_existing_md5_hash(self,file_path):
        # Get the existing MD5 hash of the file from the vector database
        _db_path = os.path.join(self.db_path, os.path.basename(file_path))
        if os.path.exists(_db_path):
            vector_store = FAISS.load_local(_db_path, embeddings=self.hf_embeddings)
            document = vector_store.get_document_by_id(file_path)
            return document.md5_hash
        return None

    def get_md5_hash(self, file_path):
    # Calculate MD5 hash of the file
        with open(file_path, "rb") as f:
            md5_hash = hashlib.md5(f.read()).hexdigest()
        return md5_hash

    def load_documents(self):
        if not (os.path.exists(self.db_path) and os.path.exists(self.folder_path)):
            return []

        updated_files = [
            os.path.join(root, file)
            for root, _, files in os.walk(self.folder_path)
            for file in files
            if file.endswith('.pdf')
            # and not self.check_if_file_updated(
            #     os.path.join(root, file),
            #     self.get_md5_hash(os.path.join(root, file))
            # )
        ]

        print("Files to be parsed")
        print("\n".join(f"{fileName}" for fileName in updated_files))

        all_documents = []
        for file_path in updated_files:
            pdfloader = PyMuPDFLoader(file_path)
            pages = pdfloader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size,
                                                chunk_overlap=self.chunk_overlap)

            _documents = text_splitter.split_documents(pages)
            all_documents.extend(_documents)


        self.vector_store = FAISS.from_documents(all_documents, embedding=self.hf_embeddings)

        return None

    def save_document(self):
        if self.vector_store is not None:
            if os.path.exists(self.db_path):
                self.vector_store.save_local(self.db_path)

    def query_document(self, query_string: str ):
        return self.vector_store.similarity_search(query_string)






        # for root, _, files in os.walk(self.folder_path):
        #     for file in files:
        #         file_path = os.path.join(root, file)
        #         if file_path.endswith('.pdf'):
        #             md5_hash = self.get_md5_hash(file_path)
        #             if not self.check_if_file_updated(file_path, md5_hash):
        #                 updated_files.append(file_path)

        #     if updated_files:
        #         for file_path in updated_files:
