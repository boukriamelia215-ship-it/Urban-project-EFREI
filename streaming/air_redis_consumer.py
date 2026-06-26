"""
Consommateur DISTRIBUE - broker Redis -> traitement temps reel + micro-batch - C2.2
Ce consommateur tourne dans son propre processus, separe du producteur. Il
s'abonne au canal Redis et recoit les mesures de qualite de l'air publiees par
air_redis_producer.py via le broker, sur le reseau.

En plus du traitement temps reel + micro-batch, il ecrit la derniere valeur
recue de chaque station dans Redis (cle air:latest:<station>), pour que l'API
puisse l'exposer au dashboard -- C2.2 connecte au reste du projet, pas isole.

Lancer (2e terminal, APRES le producteur) : python streaming/air_redis_consumer.py
Arreter avec Ctrl+C.
"""
import json
import os
import threading
import time
from datetime import datetime, timezone
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CHANNEL = os.getenv("REDIS_CHANNEL", "air-quality-events")
WINDOW_SECONDS = 10

microbatch_buffer = []
running = True


def microbatch_aggregator():
    window_no = 0
    while running:
        time.sleep(WINDOW_SECONDS)
        window_no += 1
        batch = microbatch_buffer[:]
        microbatch_buffer.clear()
        if not batch:
            print(f"[MICRO-BATCH #{window_no}] fenetre {WINDOW_SECONDS}s - 0 mesure")
            continue
        aqi_vals = [e["aqi"] for e in batch if isinstance(e.get("aqi"), (int, float))]
        no2_vals = [e["no2"] for e in batch if isinstance(e.get("no2"), (int, float))]
        aqi_moy = round(sum(aqi_vals) / len(aqi_vals), 1) if aqi_vals else "n/a"
        no2_moy = round(sum(no2_vals) / len(no2_vals), 1) if no2_vals else "n/a"
        print(f"\n[MICRO-BATCH #{window_no}] fenetre {WINDOW_SECONDS}s - {len(batch)} mesures recues")
        print(f"   -> AQI moyen Paris : {aqi_moy}  .  NO2 moyen : {no2_moy} ug/m3\n")


def main():
    client = redis.from_url(REDIS_URL, decode_responses=True,
                            health_check_interval=15,
                            socket_keepalive=True,
                            socket_timeout=60)
    client.ping()
    pubsub = client.pubsub()
    pubsub.subscribe(CHANNEL)
    print(f"[CONSOMMATEUR] abonne au canal '{CHANNEL}' via le broker Redis")
    print("En attente de messages du producteur...\n")

    threading.Thread(target=microbatch_aggregator, daemon=True).start()

    for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            event = json.loads(message["data"])
        except (ValueError, TypeError):
            continue

        no2 = event.get("no2")
        no2_txt = f"{no2:>5}" if isinstance(no2, (int, float)) else "  n/a"
        print(f"[TEMPS REEL] {event.get('station',''):<20} "
              f"AQI={str(event.get('aqi')):>3}  NO2={no2_txt} ug/m3")

        station = event.get("station", "inconnue")
        snapshot = {
            "station": station,
            "aqi": event.get("aqi"),
            "no2": event.get("no2"),
            "pm10": event.get("pm10"),
            "pm25": event.get("pm25"),
            "o3": event.get("o3"),
            "derniere_maj": datetime.now(timezone.utc).isoformat(),
        }
        client.set(f"air:latest:{station}", json.dumps(snapshot))

        microbatch_buffer.append(event)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        running = False
        print("\n[CONSOMMATEUR] arret.")
    except redis.exceptions.RedisError as exc:
        print(f"[ERREUR REDIS] {exc}\nVerifie REDIS_URL dans ton .env")