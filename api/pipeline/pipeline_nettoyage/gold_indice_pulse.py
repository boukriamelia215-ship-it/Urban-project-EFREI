"""
Indice PULSE -- indicateur composite avance (C2.3)
Pollution, Urbanisme, eLigibilite ecologique, Securite, Evolution du marche.

Methode : moyenne geometrique ponderee (comme l'IDH de l'ONU depuis 2010),
qui penalise plus fortement une faiblesse marquee sur une seule dimension,
contrairement a une moyenne arithmetique qui peut la "diluer".
"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "data" / "Gold"


def normaliser_borne(serie, inverser=False):
    """Normalise sur [0.05, 1.0] -- la borne basse evite qu'un score de 0
    sur une seule dimension annule tout le produit (effet trop punitif)."""
    s = (serie - serie.min()) / (serie.max() - serie.min())
    if inverser:
        s = 1 - s
    return 0.05 + 0.95 * s


# --- Sources ---
air = pd.read_csv(GOLD / "qualite_air.csv")[["arrondissement", "no2_moyen"]]
verts = pd.read_csv(GOLD / "espaces_verts.csv")[["arrondissement", "m2_par_habitant"]]

delinq = pd.read_csv(GOLD / "delinquance.csv")
delinq = delinq[delinq["annee"] == 2024][["arrondissement", "score_delinquance"]]

densite = pd.read_csv(GOLD / "densite.csv")
densite = densite[densite["annee"] == 2024][["arrondissement", "densite_hab_km2"]]

# --- Stabilite du marche : coefficient de variation du prix sur 2020-2024 ---
prix = pd.read_csv(GOLD / "prix_m2_par_arrondissement.csv")
stabilite = prix.groupby("arrondissement")["prix_m2_median"].agg(
    moyenne_prix="mean", ecart_type_prix="std"
).reset_index()
stabilite["coefficient_variation_prix"] = (
    stabilite["ecart_type_prix"] / stabilite["moyenne_prix"]
).round(4)

# --- Fusion ---
df = air.merge(verts, on="arrondissement") \
        .merge(delinq, on="arrondissement") \
        .merge(densite, on="arrondissement") \
        .merge(stabilite[["arrondissement", "coefficient_variation_prix"]], on="arrondissement")

# --- Normalisation (chaque note sur [0.05, 1.0]) ---
note_p = normaliser_borne(df["no2_moyen"], inverser=True)               # Pollution (inverse : moins = mieux)
note_u = normaliser_borne(df["densite_hab_km2"], inverser=True)         # Urbanisme/densite (inverse)
note_l = normaliser_borne(df["m2_par_habitant"], inverser=False)        # eLigibilite ecologique
note_s = normaliser_borne(df["score_delinquance"], inverser=True)       # Securite (inverse)
note_e = normaliser_borne(df["coefficient_variation_prix"], inverser=True)  # Evolution/stabilite (inverse)

# --- Moyenne geometrique ponderee (methode IDH-ONU) ---
poids = {"p": 0.25, "u": 0.20, "l": 0.25, "s": 0.20, "e": 0.10}

df["score_indice_pulse"] = 100 * (
    note_p ** poids["p"] *
    note_u ** poids["u"] *
    note_l ** poids["l"] *
    note_s ** poids["s"] *
    note_e ** poids["e"]
)
df["score_indice_pulse"] = df["score_indice_pulse"].round(1)

resultat = df[[
    "arrondissement", "score_indice_pulse", "no2_moyen", "densite_hab_km2",
    "m2_par_habitant", "score_delinquance", "coefficient_variation_prix"
]].sort_values("score_indice_pulse", ascending=False)

resultat.to_csv(GOLD / "indice_pulse.csv", index=False)
print(f"Fichier GOLD cree -- {len(resultat)} lignes")
print(resultat.head(10).to_string(index=False))