import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    uri = os.getenv("MONGO_URI")
    try:
        # 1. Tenta la connessione
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # 2. Chiedi al server di rispondere (comando ping)
        client.admin.command('ping')
        print("✅ SUCCESSO! Il tuo PC è collegato a MongoDB Atlas.")
        
        # 3. Vediamo se ci sono database
        print(f"Database disponibili: {client.list_database_names()}")
        
    except Exception as e:
        print("❌ ERRORE di connessione. Controlla:")
        print("1. Se la password nel file .env è corretta.")
        print("2. Se hai abilitato 'Allow Access from Anywhere' in Network Access.")
        print(f"\nDettaglio errore: {e}")

if __name__ == "__main__":
    test_connection()