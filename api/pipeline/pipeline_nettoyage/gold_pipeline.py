import pandas as pd
from pathlib import Path
# -----------------------------------------------------
# Détecter correctement la racine du projet
# gold_pipeline.py → pipeline_nettoyage → pipeline → api → racine (3 parents)
# -----------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[3]
# Dossiers data
DATA_DIR = ROOT_DIR / "data"
SILVER = DATA_DIR / "Silver"
GOLD = DATA_DIR / "Gold"

def build_prix_m2_par_arrondissement():
    print("Construction de l'indicateur : prix/m2 median...")
    dvf_path = SILVER / "dvf_ready.csv"
    # Charger DVF nettoye
    df = pd.read_csv(dvf_path, low_memory=False)
    # Normaliser le type d'arrondissement (corrige un bug de melange texte/nombre)
    df["arrondissement"] = pd.to_numeric(df["arrondissement"], errors="coerce")
    df = df.dropna(subset=["arrondissement"])
    df["arrondissement"] = df["arrondissement"].astype(int)
    # Calcul du prix au m2
    df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]
    # Groupby : arrondissement + annee
    grouped = (
        df.groupby(["arrondissement", "annee"])
        .agg(
            prix_m2_median=("prix_m2", "median"),
            nb_ventes=("id_mutation", "count")
        )
        .reset_index()
    )
    # Sauvegarde dans data/Gold
    output_path = GOLD / "prix_m2_par_arrondissement.csv"
    grouped.to_csv(output_path, index=False)
    print(f"Fichier GOLD cree : {output_path}")

if __name__ == "__main__":
    build_prix_m2_par_arrondissement()