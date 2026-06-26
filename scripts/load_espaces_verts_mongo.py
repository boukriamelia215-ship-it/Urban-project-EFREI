"""
Charge data/Gold/espaces_verts.csv dans MongoDB -- C1.2 (NoSQL).
Script de migration a executer une fois (ou a chaque mise a jour du Gold).
"""
import os
import pandas as pd
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "Gold"

MONGODB_URL = os.getenv("MONGODB_URL")


def migrate():
    if not MONGODB_URL:
        print("ERREUR: MONGODB_URL manquant dans .env")
        return

    csv_path = GOLD / "espaces_verts.csv"
    if not csv_path.exists():
        print(f"ERREUR: {csv_path} introuvable")
        return

    df = pd.read_csv(csv_path)
    documents = df.to_dict(orient="records")

    client = MongoClient(MONGODB_URL)
    db = client["urban_data_explorer"]
    collection = db["espaces_verts"]

    collection.delete_many({})
    collection.insert_many(documents)

    print(f"OK: {len(documents)} documents inseres dans MongoDB (collection espaces_verts)")
    client.close()


if __name__ == "__main__":
    migrate()