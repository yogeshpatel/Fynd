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
        self.file_map = {}

        self.file_map_path = os.path.join(self.db_path, "file_map.json")
        if os.path.exists(self.file_map_path):
            with open(self.file_map_path, "r") as f:
                self.file_map = json.load(f)

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

    def check_if_file_updated(self,file_path):
    # Check if the file has been updated by comparing its MD5 hash with the existing one
        file_hash = self.get_md5_hash(file_path)
        if self.file_map.get(file_path):
            if self.file_map.get(file_path) == file_hash:
                return True

        return False


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
            and not self.check_if_file_updated(
                os.path.join(root, file)
            )
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

        for _file_path_ in updated_files:
            _file_hash = self.get_md5_hash(_file_path_)
            self.file_map[_file_path_] = _file_hash

        with open(self.file_map_path, "w") as f:
            json.dump(self.file_map, f)

        if all_documents:
            self.vector_store.add_documents(all_documents, embedding=self.hf_embeddings)

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
