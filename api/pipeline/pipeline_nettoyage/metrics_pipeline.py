"""
Mesure de performance du pipeline Bronze -> Silver -> Gold (C2.4).
Execute chaque etape et mesure le temps reel, + verifie la qualite
des donnees produites (valeurs nulles, doublons).
"""
import time
import subprocess
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "data" / "Gold"
PIPELINE_DIR = Path(__file__).resolve().parent

ETAPES = [
    ("Nettoyage DVF (Silver)", PIPELINE_DIR / "clean_dvf.py"),
    ("Gold prix/m2", PIPELINE_DIR / "gold_pipeline.py"),
    ("Gold delinquance", PIPELINE_DIR / "gold_delinquance.py"),
    ("Gold densite", PIPELINE_DIR / "gold_densite.py"),
    ("Gold typologie", PIPELINE_DIR / "gold_typologie.py"),
]

def mesurer_etapes():
    print("=" * 60)
    print("METRIQUES DE PERFORMANCE DU PIPELINE")
    print("=" * 60)
    resultats = []
    for nom, script in ETAPES:
        if not script.exists():
            print(f"{nom:30s} -- script introuvable, ignore")
            continue
        debut = time.time()
        subprocess.run(["python", str(script)], capture_output=True)
        duree = time.time() - debut
        resultats.append((nom, duree))
        print(f"{nom:30s} {duree:.2f} s")
    return resultats

def verifier_qualite():
    print("\n" + "=" * 60)
    print("QUALITE DES DONNEES GOLD")
    print("=" * 60)
    for csv_path in sorted(GOLD.glob("*.csv")):
        df = pd.read_csv(csv_path)
        nulls = df.isnull().sum().sum()
        cols_id = [c for c in ["arrondissement", "annee"] if c in df.columns]
        doublons = df.duplicated(subset=cols_id).sum() if cols_id else "N/A"
        print(f"{csv_path.name:40s} {len(df):4d} lignes | {nulls:3d} nulls | {doublons} doublons")

if __name__ == "__main__":
    mesurer_etapes()
    verifier_qualite()