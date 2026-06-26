"""
Test de charge MongoDB -- C1.2 (preuve de performance NoSQL).
Envoie des requetes concurrentes sur la collection espaces_verts.
"""
import os
import time
import threading
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
NB_THREADS = 10
REQUETES_PAR_THREAD = 20

resultats = {"succes": 0, "erreurs": 0}
verrou = threading.Lock()


def worker():
    client = MongoClient(MONGODB_URL)
    collection = client["urban_data_explorer"]["espaces_verts"]
    for _ in range(REQUETES_PAR_THREAD):
        try:
            list(collection.find({}))
            with verrou:
                resultats["succes"] += 1
        except Exception:
            with verrou:
                resultats["erreurs"] += 1
    client.close()


def main():
    print(f"Test de charge MongoDB : {NB_THREADS} threads x {REQUETES_PAR_THREAD} requetes")
    debut = time.time()

    threads = [threading.Thread(target=worker) for _ in range(NB_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    duree = time.time() - debut
    total = resultats["succes"] + resultats["erreurs"]

    print(f"\nResultats :")
    print(f"  Requetes reussies : {resultats['succes']}/{total}")
    print(f"  Erreurs           : {resultats['erreurs']}")
    print(f"  Temps total        : {duree:.3f} s")
    print(f"  Debit              : {total/duree:.1f} req/s")


if __name__ == "__main__":
    main()