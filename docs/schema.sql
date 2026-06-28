-- Schema relationnel Urban Data Explorer (PostgreSQL / Supabase)

CREATE TABLE arrondissement (
    arrondissement INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    code_insee TEXT
);

CREATE TABLE prix_m2_par_arrondissement (
    arrondissement INTEGER NOT NULL,
    annee INTEGER NOT NULL,
    prix_m2_median NUMERIC,
    nb_ventes INTEGER,
    PRIMARY KEY (arrondissement, annee),
    FOREIGN KEY (arrondissement) REFERENCES arrondissement(arrondissement)
);

CREATE TABLE logements_sociaux (
    arrondissement INTEGER NOT NULL,
    annee INTEGER NOT NULL,
    nb_programmes INTEGER,
    nb_logements INTEGER,
    nb_logements_cumule INTEGER,
    insee_log NUMERIC,
    part_logements_sociaux_pct NUMERIC,
    PRIMARY KEY (arrondissement, annee),
    FOREIGN KEY (arrondissement) REFERENCES arrondissement(arrondissement)
);

CREATE TABLE delinquance (
    arrondissement INTEGER NOT NULL,
    annee INTEGER NOT NULL,
    score_delinquance NUMERIC,
    PRIMARY KEY (arrondissement, annee),
    FOREIGN KEY (arrondissement) REFERENCES arrondissement(arrondissement)
);

CREATE TABLE densite (
    arrondissement INTEGER NOT NULL,
    annee INTEGER NOT NULL,
    densite_hab_km2 NUMERIC,
    PRIMARY KEY (arrondissement, annee),
    FOREIGN KEY (arrondissement) REFERENCES arrondissement(arrondissement)
);

CREATE TABLE typologie_logements (
    arrondissement INTEGER NOT NULL,
    annee INTEGER NOT NULL,
    part_T1 NUMERIC,
    part_T2 NUMERIC,
    part_T3 NUMERIC,
    part_T4 NUMERIC,
    PRIMARY KEY (arrondissement, annee),
    FOREIGN KEY (arrondissement) REFERENCES arrondissement(arrondissement)
);

CREATE TABLE espaces_verts (
    arrondissement INTEGER PRIMARY KEY,
    superficie_totale_m2 NUMERIC,
    insee_pop INTEGER,
    m2_par_habitant NUMERIC,
    annee INTEGER,
    FOREIGN KEY (arrondissement) REFERENCES arrondissement(arrondissement)
);

CREATE TABLE qualite_air (
    arrondissement INTEGER PRIMARY KEY,
    no2_moyen NUMERIC,
    o3_moyen NUMERIC,
    pm10_moyen NUMERIC,
    annee INTEGER,
    indice_exposition_pollution NUMERIC,
    FOREIGN KEY (arrondissement) REFERENCES arrondissement(arrondissement)
);

-- Row Level Security : lecture publique (open data, pas de donnees personnelles)
ALTER TABLE arrondissement ENABLE ROW LEVEL SECURITY;
ALTER TABLE prix_m2_par_arrondissement ENABLE ROW LEVEL SECURITY;
ALTER TABLE logements_sociaux ENABLE ROW LEVEL SECURITY;
ALTER TABLE delinquance ENABLE ROW LEVEL SECURITY;
ALTER TABLE densite ENABLE ROW LEVEL SECURITY;
ALTER TABLE typologie_logements ENABLE ROW LEVEL SECURITY;
ALTER TABLE espaces_verts ENABLE ROW LEVEL SECURITY;
ALTER TABLE qualite_air ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lecture publique" ON arrondissement FOR SELECT USING (true);
CREATE POLICY "Lecture publique" ON prix_m2_par_arrondissement FOR SELECT USING (true);
CREATE POLICY "Lecture publique" ON logements_sociaux FOR SELECT USING (true);
CREATE POLICY "Lecture publique" ON delinquance FOR SELECT USING (true);
CREATE POLICY "Lecture publique" ON densite FOR SELECT USING (true);
CREATE POLICY "Lecture publique" ON typologie_logements FOR SELECT USING (true);
CREATE POLICY "Lecture publique" ON espaces_verts FOR SELECT USING (true);
CREATE POLICY "Lecture publique" ON qualite_air FOR SELECT USING (true);
-- Indicateurs creatifs (C2.3) -- meme schema relationnel que les tables d'origine

CREATE TABLE indice_famille (
    arrondissement INTEGER PRIMARY KEY REFERENCES arrondissement(arrondissement),
    score_indice_famille NUMERIC,
    m2_par_habitant NUMERIC,
    part_t4 NUMERIC,
    score_delinquance NUMERIC
);

CREATE TABLE indice_investisseur (
    arrondissement INTEGER PRIMARY KEY REFERENCES arrondissement(arrondissement),
    score_indice_investisseur NUMERIC,
    croissance_pct NUMERIC,
    densite_hab_km2 NUMERIC,
    prix_2024 NUMERIC
);

CREATE TABLE indice_respire (
    arrondissement INTEGER PRIMARY KEY REFERENCES arrondissement(arrondissement),
    score_indice_respire NUMERIC,
    no2_moyen NUMERIC,
    m2_par_habitant NUMERIC,
    densite_hab_km2 NUMERIC
);

ALTER TABLE indice_famille ENABLE ROW LEVEL SECURITY;
ALTER TABLE indice_investisseur ENABLE ROW LEVEL SECURITY;
ALTER TABLE indice_respire ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lecture publique" ON indice_famille FOR SELECT USING (true);
CREATE POLICY "Lecture publique" ON indice_investisseur FOR SELECT USING (true);
CREATE POLICY "Lecture publique" ON indice_respire FOR SELECT USING (true);