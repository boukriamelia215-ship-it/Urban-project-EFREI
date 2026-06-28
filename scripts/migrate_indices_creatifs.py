"""
Migration des 3 indicateurs creatifs vers PostgreSQL Supabase.
"""
import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "Gold"

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

TABLES = {
    "indice_famille.csv": "indice_famille",
    "indice_investisseur.csv": "indice_investisseur",
    "indice_respire.csv": "indice_respire",
}

def migrate():
    engine = create_engine(SUPABASE_DB_URL)
    for csv_name, table_name in TABLES.items():
        df = pd.read_csv(GOLD / csv_name)
        df.columns = [c.lower() for c in df.columns]
        df.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"OK: {table_name} -- {len(df)} lignes migrees")

if __name__ == "__main__":
    migrate()