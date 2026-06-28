"""
Migration des fichiers Gold (CSV) vers PostgreSQL Supabase.
Lit chaque CSV de data/Gold et le pousse dans la table correspondante.
"""
import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "data" / "Gold"

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

TABLES = {
    "prix_m2_par_arrondissement.csv": "prix_m2_par_arrondissement",
    "logements_sociaux.csv": "logements_sociaux",
    "delinquance.csv": "delinquance",
    "densite.csv": "densite",
    "typologie_logements.csv": "typologie_logements",
    "espaces_verts.csv": "espaces_verts",
    "qualite_air.csv": "qualite_air",
}

def migrate():
    if not SUPABASE_DB_URL:
        print("ERREUR: SUPABASE_DB_URL manquant dans .env")
        return

    engine = create_engine(SUPABASE_DB_URL)

    for csv_name, table_name in TABLES.items():
        csv_path = GOLD / csv_name
        if not csv_path.exists():
            print(f"IGNORE: {csv_name} introuvable")
            continue

        df = pd.read_csv(csv_path)
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f"OK: {table_name} -- {len(df)} lignes migrees")

    print("Migration terminee.")

if __name__ == "__main__":
    migrate()