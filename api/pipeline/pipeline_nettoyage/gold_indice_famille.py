"""
Indice Famille -- "Cet arrondissement est-il adapte pour elever des enfants ?"
Combine espaces verts + grands logements (T4+) - delinquance.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "data" / "Gold"


def normaliser(serie, inverser=False):
    s = (serie - serie.min()) / (serie.max() - serie.min()) * 10
    return 10 - s if inverser else s


verts = pd.read_csv(GOLD / "espaces_verts.csv")[["arrondissement", "m2_par_habitant"]]

typo = pd.read_csv(GOLD / "typologie_logements.csv")
typo = typo[typo["annee"] == 2024][["arrondissement", "part_T4"]]

delinq = pd.read_csv(GOLD / "delinquance.csv")
delinq = delinq[delinq["annee"] == 2024][["arrondissement", "score_delinquance"]]

df = verts.merge(typo, on="arrondissement").merge(delinq, on="arrondissement")

df["note_verts"] = normaliser(df["m2_par_habitant"])
df["note_t4"] = normaliser(df["part_T4"])
df["note_securite"] = normaliser(df["score_delinquance"], inverser=True)

df["score_indice_famille"] = (
    df["note_verts"] * 0.40 +
    df["note_t4"] * 0.40 +
    df["note_securite"] * 0.20
) * 10
df["score_indice_famille"] = df["score_indice_famille"].round(1)

resultat = df[["arrondissement", "score_indice_famille", "m2_par_habitant", "part_T4", "score_delinquance"]]
resultat = resultat.sort_values("score_indice_famille", ascending=False)

resultat.to_csv(GOLD / "indice_famille.csv", index=False)
print(f"Fichier GOLD cree -- {len(resultat)} lignes")
print(resultat.head(10).to_string(index=False))