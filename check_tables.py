import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(os.getenv("SUPABASE_DB_URL"))
tables = ["arrondissement", "prix_m2_par_arrondissement", "logements_sociaux", "delinquance", "densite", "qualite_air", "typologie_logements"]
for t in tables:
    try:
        df = pd.read_sql(f"SELECT COUNT(*) as n FROM {t}", engine)
        print(f"{t}: {df.iloc[0][chr(110)]} lignes")
    except Exception as e:
        print(f"{t}: ERREUR - {e}")
