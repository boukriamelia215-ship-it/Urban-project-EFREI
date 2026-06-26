# Optimisation des performances du pipeline — C2.4

## 1. Cache memoire au demarrage de l'API

Avant : chaque requete relisait le fichier CSV depuis le disque.
Apres : les 8 fichiers Gold sont charges une seule fois au demarrage
de l'API (`@app.on_event("startup")`), puis servis depuis la memoire.

Preuve de fonctionnement : endpoint `/admin/cache` (protege par cle API)
qui liste les fichiers en cache et leur nombre de lignes.

## 2. Format Parquet -- test honnete et limite identifiee

On a teste la conversion de `prix_m2_par_arrondissement.csv` (120 lignes)
en Parquet :

| Format  | Taille     |
|---------|------------|
| CSV     | 3 681 octets |
| Parquet | 4 768 octets |

**Resultat : Parquet est 29% PLUS GROS que le CSV sur ce fichier.**

Explication : Parquet stocke des metadonnees (schema, statistiques par
colonne, footer) qui representent un cout fixe non negligeable. Sur un
fichier de cette taille (quelques centaines de lignes), ce cout fixe
depasse le gain apporte par la compression colonnaire. Parquet devient
interessant a partir de plusieurs dizaines de milliers de lignes, ce qui
n'est pas le profil de nos fichiers Gold (agreges par arrondissement/annee,
donc volumetrie naturellement faible : max 20 arrondissements x quelques
annees).

**Conclusion** : pour ce projet, le CSV est le format le plus adapte au
volume reel de donnees. Le cache memoire (point 1) est l'optimisation
pertinente a cette echelle, pas le changement de format de stockage.

## 3. Ce qu'on ferait en production (volumetrie plus importante)

- Cache Redis partage entre plusieurs instances de l'API (au lieu d'un
  cache local par processus)
- Parquet si la volumetrie augmente significativement (donnees brutes
  non agregees, historique long)
- Index PostgreSQL sur (arrondissement, annee) pour les requetes SQL
  analytiques (tests de charge deja realises, voir postgres_load_test.md)
## 5. Test de charge MongoDB (C1.2 - performance NoSQL)

Script `scripts/test_load_mongodb.py` -- 10 threads x 20 requetes simultanees
sur la collection `espaces_verts` :

| Metrique | Valeur |
|---|---|
| Requetes reussies | 200/200 |
| Erreurs | 0 |
| Temps total | 3.607 s |
| Debit | 55.5 req/s |

## 6. Temps de reponse par source de donnees (mesure manuelle)

| Endpoint | Source | Latence typique |
|---|---|---|
| /prix_m2 | PostgreSQL (cache demarrage) | <5 ms |
| /espaces_verts | MongoDB (requete directe) | ~20-50 ms |
| /qualite_air/live | Redis (requete directe) | ~30-60 ms |