from fastapi import FastAPI, Query, Header, HTTPException, Request, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import JWTError, jwt
import bcrypt
import os
import json
import redis
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Urban Data Explorer API", version="1.0.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
GOLD = DATA / "Gold"
SILVER = DATA / "Silver"

# ---------------------------------------------------------------------------
# AUTHENTIFICATION JWT -- C2.1
# ---------------------------------------------------------------------------
SECRET_KEY = "urban-data-explorer-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# Base utilisateurs (demo pedagogique -- en prod : table dans PostgreSQL)
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("urbanadmin2024"),
        "role": "admin",
    },
    "client": {
        "username": "client",
        "hashed_password": hash_password("urbanclient2024"),
        "role": "lecture",
    },
}


def authenticate_user(username: str, password: str):
    user = FAKE_USERS_DB.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token invalide ou expire",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = FAKE_USERS_DB.get(username)
    if user is None:
        raise credentials_exception
    return user


# ---------------------------------------------------------------------------
# Cache memoire -- C2.4
# ---------------------------------------------------------------------------
_cache: dict = {}


@app.on_event("startup")
def preload_gold_data():
    for csv_path in GOLD.glob("*.csv"):
        parquet_path = csv_path.with_suffix(".parquet")
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
        else:
            df = pd.read_csv(csv_path)
        df = df.astype(object).where(pd.notnull(df), None)
        _cache[csv_path.name] = df
    print(f"{len(_cache)} fichiers Gold precharges en memoire au demarrage (C2.4)")


def load_gold(name: str):
    if name not in _cache:
        df = pd.read_csv(GOLD / name)
        df = df.astype(object).where(pd.notnull(df), None)
        _cache[name] = df
    return _cache[name].copy()


# ---------------------------------------------------------------------------
# ROUTE DE LOGIN -- C2.1
# ---------------------------------------------------------------------------
@app.post("/login")
@limiter.limit("6/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Nom d'utilisateur ou mot de passe incorrect")
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
@limiter.limit("60/minute")
def home(request: Request):
    return {
        "status": "ok",
        "message": "API Urban Data Explorer fonctionne !",
        "version": "1.0.0",
        "auth": "POST /login avec username/password pour obtenir un token JWT",
        "endpoints": ["/login", "/prix_m2", "/logements_sociaux", "/delinquance", "/densite",
                      "/espaces_verts", "/qualite_air", "/qualite_air/live", "/typologie",
                      "/arrondissements", "/timeline", "/comparaison", "/admin/status", "/admin/cache"]
    }


@app.get("/admin/status")
@limiter.limit("6/minute")
def admin_status(request: Request, current_user: dict = Depends(get_current_user)):
    return {
        "status": "ok",
        "utilisateur": current_user["username"],
        "role": current_user["role"],
        "tables": len(_cache),
        "sources": ["DVF data.gouv", "OpenData Paris", "INSEE", "SSMSI", "Airparif"],
        "arrondissements": 20,
        "annees": "2020-2024"
    }


@app.get("/admin/cache")
@limiter.limit("6/minute")
def cache_status(request: Request, current_user: dict = Depends(get_current_user)):
    return {
        "utilisateur": current_user["username"],
        "fichiers_en_cache": list(_cache.keys()),
        "nb_fichiers": len(_cache),
        "lignes_par_fichier": {k: len(v) for k, v in _cache.items()}
    }


@app.get("/prix_m2")
@limiter.limit("30/minute")
def prix_m2(request: Request, annee: Optional[int] = None, arrondissement: Optional[int] = None):
    df = load_gold("prix_m2_par_arrondissement.csv")
    if annee:
        df = df[df["annee"] == annee]
    if arrondissement:
        df = df[df["arrondissement"] == arrondissement]
    return df.to_dict(orient="records")


@app.get("/typologie")
@limiter.limit("30/minute")
def typologie(request: Request, annee: Optional[int] = None):
    df = load_gold("typologie_logements.csv")
    if annee:
        df = df[df["annee"] == annee]
    return df.to_dict(orient="records")


@app.get("/logements_sociaux")
@limiter.limit("30/minute")
def logements_sociaux(request: Request, annee: Optional[int] = None):
    df = load_gold("logements_sociaux.csv")
    if annee:
        df = df[df["annee"] == annee]
    return df.to_dict(orient="records")


@app.get("/delinquance")
@limiter.limit("30/minute")
def delinquance(request: Request, annee: Optional[int] = None):
    df = load_gold("delinquance.csv")
    if annee:
        df = df[df["annee"] == annee]
    return df.to_dict(orient="records")


@app.get("/densite")
@limiter.limit("30/minute")
def densite(request: Request, annee: Optional[int] = None):
    df = load_gold("densite.csv")
    if annee:
        df = df[df["annee"] == annee]
    return df.to_dict(orient="records")


@app.get("/espaces_verts")
@limiter.limit("30/minute")
def espaces_verts(request: Request, arrondissement: Optional[int] = None):
    df = load_gold("espaces_verts.csv")
    if arrondissement:
        df = df[df["arrondissement"] == arrondissement]
    return df.to_dict(orient="records")


@app.get("/qualite_air")
@limiter.limit("30/minute")
def qualite_air(request: Request, arrondissement: Optional[int] = None):
    df = load_gold("qualite_air.csv")
    if arrondissement:
        df = df[df["arrondissement"] == arrondissement]
    return df.to_dict(orient="records")


@app.get("/qualite_air/live")
@limiter.limit("30/minute")
def qualite_air_live(request: Request):
    """Derniere valeur recue via le flux Redis (streaming temps reel) -- C2.2"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        r = redis.from_url(redis_url, decode_responses=True, socket_timeout=5)
        keys = r.keys("air:latest:*")
        resultats = []
        for k in keys:
            valeur = r.get(k)
            if valeur:
                resultats.append(json.loads(valeur))
        return {"stations": resultats, "nb_stations": len(resultats)}
    except Exception as e:
        return {"stations": [], "nb_stations": 0, "erreur": str(e)}


@app.get("/arrondissements")
@limiter.limit("30/minute")
def arrondissements(request: Request):
    df = pd.read_csv(SILVER / "arrondissements_clean.csv")
    return df.to_dict(orient="records")


@app.get("/timeline")
@limiter.limit("30/minute")
def timeline(request: Request, arr: int = Query(..., description="Code arrondissement (1-20)")):
    df = load_gold("prix_m2_par_arrondissement.csv")
    df_arr = df[df["arrondissement"] == arr].sort_values("annee")
    if df_arr.empty:
        return {"arrondissement": arr, "data": []}
    df_arr = df_arr.copy()
    df_arr["variation_pct"] = df_arr["prix_m2_median"].pct_change() * 100
    df_arr["variation_pct"] = df_arr["variation_pct"].round(1).fillna(0)
    return {
        "arrondissement": arr,
        "data": df_arr[["annee", "prix_m2_median", "nb_ventes", "variation_pct"]].to_dict(orient="records")
    }


@app.get("/comparaison")
@limiter.limit("30/minute")
def comparaison(
    request: Request,
    arr1: int = Query(...),
    arr2: int = Query(...),
    annee: Optional[int] = None
):
    def get_indicator(csv_name: str, arr_code: int, year: Optional[int]):
        try:
            df = load_gold(csv_name)
            df_f = df[df["arrondissement"] == arr_code]
            if year:
                df_f = df_f[df_f["annee"] == year]
            return df_f.to_dict(orient="records")
        except Exception:
            return []

    def build_arr_data(arr_code: int):
        prix = get_indicator("prix_m2_par_arrondissement.csv", arr_code, annee)
        social = get_indicator("logements_sociaux.csv", arr_code, annee)
        delin = get_indicator("delinquance.csv", arr_code, annee)
        dens = get_indicator("densite.csv", arr_code, annee)
        ev = get_indicator("espaces_verts.csv", arr_code, None)
        typo = get_indicator("typologie_logements.csv", arr_code, annee)
        air = get_indicator("qualite_air.csv", arr_code, None)

        try:
            df_all = load_gold("prix_m2_par_arrondissement.csv")
            timeline_data = df_all[df_all["arrondissement"] == arr_code].sort_values("annee")[["annee", "prix_m2_median"]].to_dict(orient="records")
        except Exception:
            timeline_data = []

        return {
            "arrondissement": arr_code,
            "prix": prix[0] if prix else None,
            "logements_sociaux": social[0] if social else None,
            "delinquance": delin[0] if delin else None,
            "densite": dens[0] if dens else None,
            "espaces_verts": ev[0] if ev else None,
            "qualite_air": air[0] if air else None,
            "typologie": typo[0] if typo else None,
            "timeline": timeline_data,
        }

    return {
        "annee": annee,
        "arrondissement_1": build_arr_data(arr1),
        "arrondissement_2": build_arr_data(arr2),
    }