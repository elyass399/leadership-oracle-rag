# api.py (Aggiornato)
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse # Aggiunto
from fastapi.staticfiles import StaticFiles # Aggiunto
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from rag_engine import LeadershipEngine

load_dotenv()

app = FastAPI(title="Simon Sinek Oracle")

# Inizializzazione RAG e MongoDB
oracle = LeadershipEngine()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["leadership_oracle_db"]
collection = db["chat_history"]

class Query(BaseModel):
    text: str

# --- FRONTEND UI (Minima ed elegante con Tailwind) ---
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simon Sinek Oracle</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 h-screen flex flex-col">
        <div class="max-w-2xl mx-auto w-full flex-1 flex flex-col p-4">
            <header class="text-center py-6">
                <h1 class="text-3xl font-bold text-indigo-600">📖 Leadership Oracle</h1>
                <p class="text-gray-500">Chiedi consiglio a Simon Sinek</p>
            </header>
            
            <div id="chat" class="flex-1 overflow-y-auto bg-white rounded-lg shadow-md p-4 mb-4 space-y-4">
                <div class="bg-indigo-100 p-3 rounded-lg self-start w-fit">
                    Ciao! Sono il tuo coach digitale. Chiedimi qualunque cosa su 'Leaders Eat Last'.
                </div>
            </div>

            <div class="flex gap-2 p-2 bg-white rounded-lg shadow-sm">
                <input id="input" type="text" class="flex-1 p-2 outline-none" placeholder="Scrivi la tua domanda...">
                <button onclick="ask()" class="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700">Invia</button>
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
                chat.innerHTML += `<div id="${loadingId}" class="text-gray-400 italic">Simon sta pensando...</div>`;
                chat.scrollTop = chat.scrollHeight;

                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                const data = await response.json();
                
                // Rimuovi loader e aggiungi risposta
                document.getElementById(loadingId).remove();
                chat.innerHTML += `<div class="bg-indigo-600 text-white p-3 rounded-lg self-start w-fit">${data.answer}</div>`;
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