"""
Indice Respire -- "Ou respire-t-on le mieux a Paris ?"
Combine qualite de l'air + espaces verts - densite.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "data" / "Gold"


def normaliser(serie, inverser=False):
    s = (serie - serie.min()) / (serie.max() - serie.min()) * 10
    return 10 - s if inverser else s


air = pd.read_csv(GOLD / "qualite_air.csv")[["arrondissement", "no2_moyen"]]
verts = pd.read_csv(GOLD / "espaces_verts.csv")[["arrondissement", "m2_par_habitant"]]

densite = pd.read_csv(GOLD / "densite.csv")
densite = densite[densite["annee"] == 2024][["arrondissement", "densite_hab_km2"]]

df = air.merge(verts, on="arrondissement").merge(densite, on="arrondissement")

df["note_air"] = normaliser(df["no2_moyen"], inverser=True)
df["note_verts"] = normaliser(df["m2_par_habitant"])
df["note_densite"] = normaliser(df["densite_hab_km2"], inverser=True)

df["score_indice_respire"] = (
    df["note_air"] * 0.40 +
    df["note_verts"] * 0.40 +
    df["note_densite"] * 0.20
) * 10
df["score_indice_respire"] = df["score_indice_respire"].round(1)

resultat = df[["arrondissement", "score_indice_respire", "no2_moyen", "m2_par_habitant", "densite_hab_km2"]]
resultat = resultat.sort_values("score_indice_respire", ascending=False)

resultat.to_csv(GOLD / "indice_respire.csv", index=False)
print(f"Fichier GOLD cree -- {len(resultat)} lignes")
print(resultat.head(10).to_string(index=False))