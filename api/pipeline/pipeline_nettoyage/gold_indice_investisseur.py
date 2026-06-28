"""
Indice Investisseur -- "Ou investir pour un bon rendement locatif ?"
Combine croissance du prix (2020-2024) + densite (demande locative) - prix d'entree.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "data" / "Gold"


def normaliser(serie, inverser=False):
    s = (serie - serie.min()) / (serie.max() - serie.min()) * 10
    return 10 - s if inverser else s


prix = pd.read_csv(GOLD / "prix_m2_par_arrondissement.csv")

prix_2020 = prix[prix["annee"] == 2020][["arrondissement", "prix_m2_median"]].rename(columns={"prix_m2_median": "prix_2020"})
prix_2024 = prix[prix["annee"] == 2024][["arrondissement", "prix_m2_median"]].rename(columns={"prix_m2_median": "prix_2024"})

croissance = prix_2020.merge(prix_2024, on="arrondissement")
croissance["croissance_pct"] = (
    (croissance["prix_2024"] - croissance["prix_2020"]) / croissance["prix_2020"] * 100
).round(2)

densite = pd.read_csv(GOLD / "densite.csv")
densite = densite[densite["annee"] == 2024][["arrondissement", "densite_hab_km2"]]

df = croissance.merge(densite, on="arrondissement")

df["note_croissance"] = normaliser(df["croissance_pct"])
df["note_densite"] = normaliser(df["densite_hab_km2"])
df["note_prix_entree"] = normaliser(df["prix_2024"], inverser=True)

df["score_indice_investisseur"] = (
    df["note_croissance"] * 0.50 +
    df["note_densite"] * 0.30 +
    df["note_prix_entree"] * 0.20
) * 10
df["score_indice_investisseur"] = df["score_indice_investisseur"].round(1)

resultat = df[["arrondissement", "score_indice_investisseur", "croissance_pct", "densite_hab_km2", "prix_2024"]]
resultat = resultat.sort_values("score_indice_investisseur", ascending=False)

resultat.to_csv(GOLD / "indice_investisseur.csv", index=False)
print(f"Fichier GOLD cree -- {len(resultat)} lignes")
print(resultat.head(10).to_string(index=False))