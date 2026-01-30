# rag_engine.py (Versione finale ottimizzata per Render/Free Tier)

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq 
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS

load_dotenv()

# --- IMPOSTAZIONI GLOBALI ---
# 1. Modello ULTRA-LEGGERO per compatibilità RAM
LLM_MODEL = "llama-3.1-8b" 
EMBEDDING_MODEL = "paraphrase-albert-small-v2"
PDF_PATH = "fatture.pdf" 
CHUNK_SIZE = 2000 # Max chunk size per minimizzare il conteggio vettori

# 2. Inizializzazione LLM (Una sola volta)
LLM = ChatGroq(model=LLM_MODEL, temperature=0.1, groq_api_key=os.getenv("GROQ_API_KEY"))

# 3. Prompt Template (Il tuo template tecnico)
TEMPLATE = """Sei un assistente tecnico esperto di fiscalità italiana e normative sull'IVA. 
Il tuo unico compito è fornire informazioni precise basate SOLO sui documenti ufficiali dell'Agenzia delle Entrate forniti nel contesto.

Istruzioni:
1. Analizza il contesto fornito (la guida alla fattura elettronica).
2. Rispondi in modo conciso, tecnico e autorevole.
3. Se la domanda richiede un codice (es. TDxx o Nxx), fornisci il codice esatto e la sua funzione.
4. Se la risposta non è presente nel contesto, devi rispondere ESATTAMENTE: 'Non ho trovato informazioni a riguardo nella guida ufficiale.'

Contesto:
{context}

Domanda: {question}

Risposta Tecnica:"""


def get_rag_chain(query: str):
    """
    Funzione RAG on-demand: Carica, indicizza, esegue e libera la RAM.
    """
    
    # 1. Carica e Chunk - La parte lenta eseguita ad ogni richiesta
    loader = PyPDFLoader(PDF_PATH)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    
    # 2. Embedding e Vector Store (Consuma RAM temporaneamente)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = FAISS.from_documents(chunks, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3}) # K=3 per massima efficienza
    
    # 3. La catena LCEL
    rag_chain = (
        {
            "context": retriever | (lambda x: "\n\n".join(doc.page_content for doc in x)), 
            "question": RunnablePassthrough()
        }
        | PromptTemplate.from_template(TEMPLATE)
        | LLM
        | StrOutputParser()
    )
    
    # 4. Eseguiamo
    response = rag_chain.invoke(query)
    source_docs = retriever.invoke(query) 
    
    sources = [doc.metadata.get('page') for doc in source_docs]
    
    return {"answer": response, "sources": sources}