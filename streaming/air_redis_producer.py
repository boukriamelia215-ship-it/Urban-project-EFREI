"""
Producteur DISTRIBUE - broker Redis -> qualite de l'air en direct - C2.2
Ce producteur tourne dans son propre processus, separe du consommateur. Il
interroge l'API WAQI (qualite de l'air reelle) pour 5 stations parisiennes,
toutes les POLL_INTERVAL secondes, et publie chaque mesure sur un canal
Redis. Si l'appel WAQI echoue, une mesure simulee est publiee a la place.

Lancer (1er terminal) : python streaming/air_redis_producer.py
Arreter avec Ctrl+C.
"""
import json
import os
import random
import time
import requests
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CHANNEL = os.getenv("REDIS_CHANNEL", "air-quality-events")
WAQI_TOKEN = os.getenv("WAQI_TOKEN", "demo")
POLL_INTERVAL = 30

STATIONS = ["paris", "paris-7eme", "paris-18eme", "paris-13eme", "neuilly-sur-seine"]


def _mesure_simulee(station):
    return {
        "station": station,
        "aqi": random.randint(20, 90),
        "no2": round(random.uniform(10, 60), 1),
        "pm10": round(random.uniform(10, 50), 1),
        "pm25": round(random.uniform(5, 40), 1),
        "o3": round(random.uniform(10, 70), 1),
        "source": "simule",
    }


def fetch_station(station):
    url = f"https://api.waqi.info/feed/{station}/?token={WAQI_TOKEN}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("status") != "ok":
            return _mesure_simulee(station)
        iaqi = data["data"].get("iaqi", {})
        return {
            "station": station,
            "aqi": data["data"].get("aqi"),
            "no2": iaqi.get("no2", {}).get("v"),
            "pm10": iaqi.get("pm10", {}).get("v"),
            "pm25": iaqi.get("pm25", {}).get("v"),
            "o3": iaqi.get("o3", {}).get("v"),
            "source": "waqi",
        }
    except (requests.RequestException, ValueError, KeyError):
        return _mesure_simulee(station)


def main():
    client = redis.from_url(REDIS_URL, decode_responses=True,
                            health_check_interval=15,
                            socket_keepalive=True,
                            socket_timeout=60)
    client.ping()
    print(f"[PRODUCTEUR] connecte au broker Redis, publie sur '{CHANNEL}'")
    print(f"[PRODUCTEUR] {len(STATIONS)} stations, intervalle {POLL_INTERVAL}s\n")

    while True:
        for station in STATIONS:
            mesure = fetch_station(station)
            client.publish(CHANNEL, json.dumps(mesure))
            print(f"[PRODUCTEUR] publie {station:<20} "
                  f"AQI={mesure.get('aqi')} NO2={mesure.get('no2')} ({mesure.get('source')})")
        print(f"\n[PRODUCTEUR] cycle termine, prochain dans {POLL_INTERVAL}s\n")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[PRODUCTEUR] arret.")
    except redis.exceptions.RedisError as exc:
        print(f"[ERREUR REDIS] {exc}\nVerifie REDIS_URL dans ton .env")