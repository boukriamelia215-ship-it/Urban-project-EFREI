"""
Gold qualite air -- moyenne NO2/O3/PM10 par arrondissement + indice
d'exposition croise avec les espaces verts (C2.3 -- formule complexe).
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SILVER = ROOT / "data" / "Silver"
GOLD = ROOT / "data" / "Gold"

df = pd.read_csv(SILVER / "qualite_air_clean.csv")

gold = df.groupby("arrondissement").agg(
    no2_moyen=("no2", "mean"),
    o3_moyen=("o3", "mean"),
    pm10_moyen=("pm10", "mean")
).reset_index().round(1)

gold["annee"] = 2018

# Croisement avec espaces_verts : indice d'exposition a la pollution
# Un meme niveau de NO2 est plus problematique dans un arrondissement
# avec peu d'espaces verts pour compenser.
espaces_verts = pd.read_csv(GOLD / "espaces_verts.csv")[["arrondissement", "m2_par_habitant"]]
gold = gold.merge(espaces_verts, on="arrondissement", how="left")
gold["indice_exposition_pollution"] = gold.apply(
    lambda r: round(r["no2_moyen"] / r["m2_par_habitant"], 2) if r["m2_par_habitant"] > 0.05 else None,
    axis=1
)
gold = gold.drop(columns=["m2_par_habitant"])

gold.to_csv(GOLD / "qualite_air.csv", index=False)
print(f"Fichier GOLD cree -- {len(gold)} lignes")
print(gold.sort_values("indice_exposition_pollution", ascending=False).head(5))