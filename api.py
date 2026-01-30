# api.py (Versione Finale per il Deploy Leggero)

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse 
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os

# Importiamo la FUNZIONE RAG e i dati dal file del motore
from rag_engine import get_rag_chain, PDF_PATH, LLM_MODEL # Importiamo la funzione e le costanti

load_dotenv()

# --- 1. CONFIGURAZIONE DATABASE (Leggerissima, solo per log) ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["fatture_db"]
    collection = db["chat_history"]
    db_status = True
except Exception:
    db_status = False

# --- 2. INIZIALIZZAZIONE API (Niente Motore Pesante Qui) ---
app = FastAPI(title="Agenzia Entrate Assistant")

class Query(BaseModel):
    text: str

# Rimuoviamo la classe RispostaRag dal file finale per semplicità nel codice, 
# ma nella versione completa andrebbe ripristinata per la validazione!

# --- 3. FRONTEND UI (Invariata) ---
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
    <!-- Il tuo codice HTML va qui, come lo hai scritto tu -->
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fattura Elettronica Assistant</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 h-screen flex flex-col">
        <div class="max-w-2xl mx-auto w-full flex-1 flex flex-col p-4">
            <header class="text-center py-6">
                <h1 class="text-3xl font-bold text-green-700">🇮🇹 Agenzia Entrate Assistant</h1>
                <p class="text-gray-500">Chiedi tutto sulla Guida alla Fattura Elettronica</p>
            </header>
            
            <div id="chat" class="flex-1 overflow-y-auto bg-white rounded-lg shadow-md p-4 mb-4 space-y-4">
                <div class="bg-green-100 p-3 rounded-lg self-start w-fit">
                    Ciao! Sono l'assistente per la Fattura Elettronica. Chiedimi di codici, tipi documento (TDxx) e natura IVA (Nxx).
                </div>
            </div>

            <div class="flex gap-2 p-2 bg-white rounded-lg shadow-sm">
                <input id="input" type="text" class="flex-1 p-2 outline-none" placeholder="Es: Quale codice TD uso per l'autofattura?">
                <button onclick="ask()" class="bg-green-700 text-white px-6 py-2 rounded-md hover:bg-green-800">Invia</button>
            </div>
        </div>

        <script>
            async function ask() {
                const input = document.getElementById('input');
                const chat = document.getElementById('chat');
                const text = input.value;
                if(!text) return;

                // Aggiungi domanda utente
                chat.innerHTML += `<div class="bg-gray-200 p-3 rounded-lg self-end ml-auto w-fit">${text}</div>`;
                input.value = '';
                
                // Loader finto
                const loadingId = 'loading-' + Date.now();
                chat.innerHTML += `<div id="${loadingId}" class="text-gray-400 italic">L'assistente sta consultando la guida...</div>`;
                chat.scrollTop = chat.scrollHeight;

                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                const data = await response.json();
                
                // Rimuovi loader e aggiungi risposta
                document.getElementById(loadingId).remove();
                // Aggiungiamo la risposta del bot (ora è più semplice dato che la logica è nel rag_engine)
                chat.innerHTML += `<div class="bg-green-700 text-white p-3 rounded-lg self-start w-fit">${data.answer}</div>`; 
                chat.scrollTop = chat.scrollHeight;
            }
        </script>
    </body>
    </html>
    """


@app.post("/ask")
async def ask_simon(query: Query):
    try:
        # CHIAMATA ON-DEMAND ALLA FUNZIONE ESTERNA
        risultato = get_rag_chain(query.text)
        
        # Logica di salvataggio
        if db_status:
            log_entry = {
                "user_query": query.text,
                "bot_response": risultato['answer'],
                "timestamp": datetime.now(),
                "model": "llama-3.1-8b-groq"
            }
            collection.insert_one(log_entry)
        
        # Risposta (Il frontend si aspetta solo {answer: "..."})
        return {"answer": risultato['answer']}
    
    except Exception as e:
        # Se fallisce, è un errore di RAM o di Groq/PDF
        raise HTTPException(status_code=500, detail=f"Errore RAG: {e}")