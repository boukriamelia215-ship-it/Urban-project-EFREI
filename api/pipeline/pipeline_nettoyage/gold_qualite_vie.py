"""
Score de qualite de vie -- indicateur composite multi-sources (C2.3)
Combine pollution, espaces verts, delinquance et densite en un seul
score pondere sur 100, apres normalisation de chaque composante.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "data" / "Gold"

air = pd.read_csv(GOLD / "qualite_air.csv")[["arrondissement", "no2_moyen"]]
verts = pd.read_csv(GOLD / "espaces_verts.csv")[["arrondissement", "m2_par_habitant"]]
delinq = pd.read_csv(GOLD / "delinquance.csv")
delinq = delinq[delinq["annee"] == 2024][["arrondissement", "score_delinquance"]]
densite = pd.read_csv(GOLD / "densite.csv")
densite = densite[densite["annee"] == 2024][["arrondissement", "densite_hab_km2"]]

df = air.merge(verts, on="arrondissement").merge(delinq, on="arrondissement").merge(densite, on="arrondissement")

def normaliser_0_10(serie):
    return (serie - serie.min()) / (serie.max() - serie.min()) * 10

df["note_pollution"] = normaliser_0_10(df["no2_moyen"])
df["note_verts"] = normaliser_0_10(df["m2_par_habitant"])
df["note_densite"] = normaliser_0_10(df["densite_hab_km2"])

df["note_pollution_inv"] = 10 - df["note_pollution"]
df["note_delinquance_inv"] = 10 - df["score_delinquance"]
df["note_densite_inv"] = 10 - df["note_densite"]

df["score_qualite_vie"] = (
    df["note_pollution_inv"] * 0.40 +
    df["note_verts"] * 0.30 +
    df["note_delinquance_inv"] * 0.20 +
    df["note_densite_inv"] * 0.10
) * 10

df["score_qualite_vie"] = df["score_qualite_vie"].round(1)

resultat = df[["arrondissement", "score_qualite_vie", "no2_moyen", "m2_par_habitant",
               "score_delinquance", "densite_hab_km2"]].sort_values(
    "score_qualite_vie", ascending=False
)

resultat.to_csv(GOLD / "qualite_vie.csv", index=False)
print(f"Fichier GOLD cree -- {len(resultat)} lignes")
print(resultat.head(10))