# api.py (Aggiornato per l'Agenzia delle Entrate)

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse 
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv

# Importiamo il motore RAG (assicurati che il pdf_path sia corretto)
from rag_engine import LeadershipEngine # Nota: L'oggetto si chiama ancora 'LeadershipEngine'

load_dotenv()

# --- CONFIGURAZIONE DATABASE (invariata) ---
client = MongoClient(os.getenv("MONGO_URI"))
db = client["leadership_oracle_db"] # Puoi cambiarlo in "fatture_db" se vuoi
collection = db["chat_history"]

# --- INIZIALIZZAZIONE ---
app = FastAPI(title="Fattura Elettronica Oracle")
# AGGIUSTA IL NOME DEL PDF NEL CARICAMENTO
oracle = LeadershipEngine(pdf_path="fatture.pdf") 

class Query(BaseModel):
    text: str

# --- FRONTEND UI (Modificato per l'Agenzia delle Entrate) ---
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
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
        response = oracle.ask(query.text)
        log_entry = {
            "user_query": query.text,
            "bot_answer": response,
            "timestamp": datetime.now(),
            "platform": "Render Cloud"
        }
        collection.insert_one(log_entry)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))