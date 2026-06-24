"""Conversion CSV -> Parquet -- C2.4
Parquet = stockage colonnaire compresse, plus rapide en lecture analytique."""
import pandas as pd
from pathlib import Path

GOLD = Path(__file__).resolve().parents[1] / "data" / "Gold"

df = pd.read_csv(GOLD / "prix_m2_par_arrondissement.csv")
df.to_parquet(GOLD / "prix_m2_par_arrondissement.parquet", index=False)

csv_size = (GOLD / "prix_m2_par_arrondissement.csv").stat().st_size
parquet_size = (GOLD / "prix_m2_par_arrondissement.parquet").stat().st_size

print(f"CSV     : {csv_size:,} octets")
print(f"Parquet : {parquet_size:,} octets")
print(f"Gain    : {(1 - parquet_size/csv_size)*100:.1f}%")