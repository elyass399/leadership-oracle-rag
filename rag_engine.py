# rag_engine.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
# --- CAMBIO QUI: Importiamo Groq invece di Google ---
from langchain_groq import ChatGroq 
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class LeadershipEngine:
    def __init__(self, pdf_path="Leaders-Eat-Last-Sinek.pdf"):
        print(f" Initializing Groq-powered Oracle for: {pdf_path}")
        
        # 1. Loading & Chunking (Invariato)
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=50)
        self.chunks = splitter.split_documents(docs)

        # 2. Vector DB (Invariato)
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = FAISS.from_documents(self.chunks, embeddings)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

        # 3. Brain (GROQ)
        # Usiamo llama-3.3-70b-versatile per la massima qualità
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile", 
            temperature=0.3,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )

        # 4. Prompt (Sinek Style)
        template = """You are Simon Sinek's digital twin. 
Use the following context from 'Leaders Eat Last' to answer the question.
Context:
{context}

Question: {question}

Simon's Answer:"""
        self.prompt = PromptTemplate.from_template(template)

        # 5. LCEL Chain
        self.chain = (
            {"context": self.retriever | self.format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def ask(self, query: str):
        return self.chain.invoke(query)