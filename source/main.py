# Create simple rag based applicaiton with use of cache or any db read from folder and create index


from source.db_manager import DBManager

if __name__ == "__main__":
    # /Introduction_to_Python_Programming_WEB.pdf
    # data_path = "/media/Yogesh/DATA_2TB_M2/llm_db/rag_raw_data"
    # db_path = "/media/Yogesh/DATA_2TB_M2/llm_db/vector_db"
    #
    #
    # # Your main application logic here
    # print("RAG-based application started.")
    # manager = DBManager(data_path, db_path, 500, 50)
    # manager.load_documents()


        

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

# HI Test
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
