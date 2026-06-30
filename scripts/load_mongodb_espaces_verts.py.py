"""
Charge les données Gold espaces verts dans MongoDB Atlas -- C1.2
A lancer une seule fois depuis la racine du projet :
    python scripts/load_mongodb_espaces_verts.py
"""
import os
import pandas as pd
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Connexion MongoDB
MONGODB_URL = os.getenv("MONGODB_URL")
client = MongoClient(MONGODB_URL)
db = client["urban_data_explorer"]
collection = db["espaces_verts"]

# Charger le fichier Gold
ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "Gold"

df = pd.read_csv(GOLD / "espaces_verts.csv")
records = df.to_dict(orient="records")

# Vider la collection et recharger
collection.drop()
collection.insert_many(records)

print(f"✅ {len(records)} documents insérés dans MongoDB (collection espaces_verts)")
print(f"Exemple : {records[0]}")

# Test requête
result = list(collection.find({"arrondissement": 6}))
print(f"\nTest requête arrondissement 6 : {result}")

client.close()
