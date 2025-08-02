# Create simple rag based applicaiton with use of cache or any db read from folder and create index



import hashlib
import torch
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings

import os

class DBManager:

    def __init__(self, folder_path, db_path ,chunk_size , chunk_overlap):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.folder_path = folder_path
        self.db_path = db_path
        # hf_token = os.getenv("HF_TOKEN_KEY")

        self.hf_embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    
    
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


        # self.vector_store.save_local(self.db_path)

        search_result = self.vector_store.similarity_search("how to use list in python")
        document = "\n".join([doc.page_content for doc in search_result])
        print(document)
        return None

        # for root, _, files in os.walk(self.folder_path):
        #     for file in files:
        #         file_path = os.path.join(root, file)
        #         if file_path.endswith('.pdf'):
        #             md5_hash = self.get_md5_hash(file_path)
        #             if not self.check_if_file_updated(file_path, md5_hash):
        #                 updated_files.append(file_path)
        
        #     if updated_files:
        #         for file_path in updated_files:
                    
        
    

if __name__ == "__main__":
    # /Introduction_to_Python_Programming_WEB.pdf
    data_path = "/media/Yogesh/DATA_2TB_M2/llm_db/rag_raw_data"
    db_path = "/media/Yogesh/DATA_2TB_M2/llm_db/vector_db"


    # Your main application logic here
    print("RAG-based application started.")
    manager = DBManager(data_path, db_path, 500, 50)
    manager.load_documents()


        

# print(torch.__version__)  # Should print: 2.7.0+cu128
# print(torch.cuda.is_available())  # Should print: True
# print(torch.cuda.get_device_name(0))  # Should print: NVIDIA GeForce RTX 5060 Ti
# print(torch.cuda.get_device_capability(0))  # Should print: (12, 0)

# os.environ["HF_TOKEN_KEY"] = "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"

# from langchain.llms import HuggingFaceHub
# from langchain.embeddings import HuggingFaceEmbeddings
# import os
# import  torch

# hf_token = os.getenv("HF_TOKEN_KEY")
# cach_dir = "/media/yogesh/2TM_m2/llm_model"

# hf_embedding = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/all-MiniLM-L6-v2"
# )

# data_path = "/media/yogesh/2TM_m2/llm_db/rag_raw_data/language/Introduction_to_Python_Programming_WEB.pdf"
# db_path = "/media/yogesh/2TM_m2/llm_db"

# # vector_store = FAISS.load_local(folder_path=db_path,
# #                                embeddings=hf_embedding,
# #                                allow_dangerous_deserialization=True)

# if os.path.exists(db_path) and os.path.exists(data_path):
#     print("os path exsists")
#     loader = PyMuPDFLoader(data_path)
#     pages = loader.load()

#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,
#                                                    chunk_overlap=50)

#     all_documents = text_splitter.split_documents(pages)

#     vector_store = FAISS.from_documents(all_documents, hf_embedding)
#     search_resault = vector_store.similarity_search("how to use list in python")

#     document = "\n".join([doc.page_content for doc in search_resault])
#     print(document)
