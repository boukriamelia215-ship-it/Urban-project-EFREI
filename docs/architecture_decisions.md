# Décisions d'architecture — Urban Data Explorer

## Choix SQL vs NoSQL (C1.2)

Notre architecture combine deux approches selon la nature des données :

**PostgreSQL (Supabase)** — pour les données Gold, structurées et analytiques
(prix par arrondissement/année, indicateurs agrégés). Ces données ont un schéma
fixe et stable, des relations claires (arrondissement + année comme clés), et
sont interrogées avec des filtres/jointures classiques — un cas d'usage
typique pour le relationnel.

**JSON (zone Bronze)** — pour les données brutes collectées depuis les APIs
externes (OpenData Paris, espaces verts, logements sociaux). Ces données ont
une structure variable selon la source (champs optionnels, géométries
imbriquées, métadonnées hétérogènes) et ne sont pas encore normalisées. Le
format JSON en Bronze évite de forcer un schéma rigide avant la phase de
nettoyage (Silver), ce qui correspond à un besoin NoSQL classique (données
semi-structurées, schema-on-read).

## Haute disponibilité et résilience (C1.4)

- **Backend (Render)** : hébergement managé avec restart automatique en cas de
  crash. Le plan gratuit met le service en veille après inactivité (cold start
  ~50s), un compromis budgétaire assumé pour ce projet pédagogique — en
  production, un plan payant élimine ce délai.
- **Base de données (Supabase)** : PostgreSQL managé avec sauvegardes
  automatiques et réplication gérées par l'infrastructure cloud, sans
  opération manuelle de notre part.
- **API** : chaque endpoint lit indépendamment son fichier Gold ; la panne
  d'un indicateur n'affecte pas les autres (isolation des erreurs constatée
  lors du développement : `/vacance` en erreur n'empêchait pas `/prix_m2` de
  répondre).
- **Limite assumée** : pas de cluster multi-nœuds (hors budget étudiant) ;
  documenté ici comme axe d'amélioration plutôt que dissimulé.
## Conformité RGPD et protection des données

Toutes les données utilisées dans ce projet sont des **données ouvertes
publiques** (open data) : data.gouv.fr (DVF), OpenData Paris, INSEE, SSMSI,
Airparif. Aucune donnée personnelle identifiante n'est collectée ou traitée
(pas de noms, adresses précises individuelles, ou informations permettant
d'identifier une personne physique).

Les données les plus granulaires (transactions DVF) sont déjà anonymisées
à la source par data.gouv.fr avant publication. Notre pipeline travaille
uniquement sur des agrégats par arrondissement et par année, ce qui exclut
tout risque de ré-identification.

Base légale : Licence Ouverte / Etalab pour les données françaises, ce qui
autorise explicitement la réutilisation, y compris à des fins d'analyse
et de visualisation comme dans ce projet.