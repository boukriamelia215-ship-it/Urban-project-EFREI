\# Veille technologique — Streaming \& systèmes distribués (C2.2)



\## Besoin



Implémenter un système distribué de traitement de données en streaming,

capable de traiter à la fois en temps réel et en micro-batch.



\## Solutions évaluées



| Techno | Avantages | Inconvénients pour notre projet |

|---|---|---|

| \*\*Apache Kafka\*\* | Standard industriel, très haute capacité, persistance des messages, rejouabilité | Nécessite un cluster (broker + Zookeeper), lourd à déployer et maintenir pour un projet étudiant, surdimensionné pour notre volume de données |

| \*\*RabbitMQ\*\* | Mature, bonnes garanties de livraison, gestion fine des files | Nécessite aussi un serveur dédié à administrer, complexité de configuration (exchanges, queues, routing) non justifiée à notre échelle |

| \*\*Redis (pub/sub)\*\* | Léger, rapide à déployer, hébergement managé gratuit disponible (Upstash), API simple | Pas de persistance des messages par défaut (si personne n'écoute, le message est perdu), moins de garanties qu'un vrai broker de message comme Kafka |



\## Choix retenu : Redis



Pour ce projet pédagogique, \*\*Redis (pub/sub)\*\* a été retenu car :



1\. \*\*Suffisant pour démontrer la compétence\*\* : il permet d'implémenter un vrai

&#x20;  système distribué — deux processus indépendants (producteur et consommateur)

&#x20;  communiquant via un broker réseau, sans avoir à gérer l'infrastructure d'un

&#x20;  cluster Kafka/Zookeeper.

2\. \*\*Hébergement managé gratuit\*\* : Upstash propose du Redis serverless dans le

&#x20;  cloud, ce qui évite d'avoir à administrer un serveur.

3\. \*\*Cohérent avec le reste du projet\*\* : on privilégie déjà des services managés

&#x20;  (Supabase, Render, Netlify) plutôt que de l'infrastructure auto-gérée.

4\. \*\*Conteneurisé en local\*\* : un Redis local (Docker) sert de secours, pour ne

&#x20;  pas dépendre uniquement d'une connexion réseau externe pendant la démo.



\## Limite assumée



Redis pub/sub ne garantit pas la persistance des messages (si le consommateur

est hors-ligne, les messages publiés pendant cette période sont perdus). Pour

un usage en production avec des exigences de fiabilité plus fortes, Kafka

resterait le choix recommandé — le compromis a été documenté en connaissance

de cause, pas par méconnaissance de l'alternative.



\## Implémentation



\- `streaming/air\_redis\_producer.py` — producteur (processus séparé)

\- `streaming/air\_redis\_consumer.py` — consommateur (processus séparé),

&#x20; traitement temps réel (par message) + micro-batch (fenêtre de 10 secondes)

\- Broker : Redis (Upstash en production, Redis local conteneurisé en secours)

