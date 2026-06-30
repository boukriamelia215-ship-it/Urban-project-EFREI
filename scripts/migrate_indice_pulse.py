"""
Migration de l'indice PULSE vers PostgreSQL Supabase.
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

def migrate():
    engine = create_engine(SUPABASE_DB_URL)
    df = pd.read_csv(GOLD / "indice_pulse.csv")
    df.to_sql("indice_pulse", engine, if_exists="append", index=False)
    print(f"OK: indice_pulse -- {len(df)} lignes migrees")

if __name__ == "__main__":
    migrate()