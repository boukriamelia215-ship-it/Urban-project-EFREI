"""
Gold logements sociaux — % de logements sociaux par arrondissement/année.
Numérateur : nb_logements créés/financés (cumulé) — OpenData Paris.
Dénominateur : parc total de logements — INSEE (via base SSMSI).
"""
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
SILVER = ROOT_DIR / "data" / "Silver"
GOLD = ROOT_DIR / "data" / "Gold"

# Logements sociaux créés par arrondissement/année
df = pd.read_csv(SILVER / "logements_sociaux_clean.csv", encoding="utf-8-sig")
df["arrondissement"] = pd.to_numeric(df["arrondissement"], errors="coerce")
df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
df = df.dropna(subset=["arrondissement", "annee", "nb_logements"])
df["arrondissement"] = df["arrondissement"].astype(int)
df["annee"] = df["annee"].astype(int)

agg = df.groupby(["arrondissement", "annee"]).agg(
    nb_programmes=("nb_logements", "count"),
    nb_logements=("nb_logements", "sum"),
).reset_index()

# Cumul du nombre de logements sociaux dans le temps (stock, pas flux annuel)
agg = agg.sort_values(["arrondissement", "annee"])
agg["nb_logements_cumule"] = agg.groupby("arrondissement")["nb_logements"].cumsum()

# Parc total de logements (INSEE, via base SSMSI)
pop = pd.read_csv(SILVER / "delinquance_paris.csv", encoding="utf-8-sig")
pop["arrondissement"] = pop["CODGEO_2025"].astype(str).str[3:5].astype(int)
pop_log = pop.groupby(["arrondissement", "annee"])["insee_log"].first().reset_index()

final = agg.merge(pop_log, on=["arrondissement", "annee"], how="left")
final["part_logements_sociaux_pct"] = (final["nb_logements_cumule"] / final["insee_log"] * 100).round(2)

final.to_csv(GOLD / "logements_sociaux.csv", index=False)
print(f"Fichier GOLD cree — {len(final)} lignes")
print(final[final["annee"] == 2024].sort_values("part_logements_sociaux_pct", ascending=False).head(10))