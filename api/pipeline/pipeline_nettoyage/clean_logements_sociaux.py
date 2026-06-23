import json
import pandas as pd
from pathlib import Path

# --- chemins ---
raw_path = Path("data/Bronze/logements_sociaux.json")
clean_path = Path("data/Silver/logements_sociaux_clean.csv")

# --- lecture du JSON brut ---
with open(raw_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# --- extraction des enregistrements ---
records = data.get("records", [])

clean_data = []
for r in records:
    fields = r.get("fields", {})
    geo = fields.get("geo_point_2d", [None, None])
    
    clean_data.append({
        "annee": fields.get("annee"),
        "arrondissement": fields.get("arrdt"),
        "code_postal": fields.get("code_postal"),
        "nature_programme": fields.get("nature_prog"),
        "mode_realisation": fields.get("mode_real"),
        "nb_logements": fields.get("nb_logmt_total"),
        "coord_x": geo[1],
        "coord_y": geo[0]
    })

# --- création du DataFrame ---
df = pd.DataFrame(clean_data)

# --- nettoyage de base ---
df.drop_duplicates(inplace=True)
df.dropna(subset=["coord_x", "coord_y"], inplace=True)

# --- sauvegarde ---
clean_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(clean_path, index=False, encoding="utf-8")

print(f"✅ Données logement social nettoyées et sauvegardées dans {clean_path}")
