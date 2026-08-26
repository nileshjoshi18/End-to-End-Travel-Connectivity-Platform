# nearest_station.py  —  pure module, no FastAPI
#                  User input
#                      │
#                      ▼
#              get_routes(...)
#                      │
#                      ▼
#           get_nearest_station(...)
#                      │
#           ┌──────────┴──────────┐
#           │                     │
#           ▼                     ▼
#       Start stop             End stop
#           │                     │
#           ▼                     ▼
#       Nominatim               Nominatim
#           │                     │
#           ▼                     ▼
#       lat / lng               lat / lng
#           │                     │
#           ▼                     ▼
#       PostGIS                 PostGIS
#           │                     │
#           ▼                     ▼
#    nearest station      nearest station
#           │                     │
#           └──────────┬──────────┘
#                      │
#                station IDs
#                      │
#                      ▼
#                 Route logic
#                      │
#                      ▼
#                Final result

import os
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(DB_URL)


def get_current_ist_time() -> str:
    """Fetch current IST time from WorldTimeAPI and return as HH:MM string."""
    try:
        resp = requests.get("https://worldtimeapi.org/api/timezone/Asia/Kolkata", timeout=5)
        resp.raise_for_status()
        dt_str = resp.json()["datetime"]
        return dt_str[11:16]  # "HH:MM"
    except Exception:
        from datetime import datetime, timezone, timedelta
        ist = timezone(timedelta(hours=5, minutes=30))
        return datetime.now(ist).strftime("%H:%M")


def get_nearest_station(address: str) -> dict | None:
    encoded_address = quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1"
    headers = {"User-Agent": "MyAppName/1.0 (funnycornflakes174@gmail.com)"}

    response = requests.get(url, headers=headers)
    data = response.json()

    if not data:
        return _get_station_via_name_resolver(address)

    address_lat = float(data[0]["lat"])
    address_long = float(data[0]["lon"])
    query = text("""
        SELECT stop_id, name, lat, lng, mode,
        ST_DistanceSphere(geom, ST_SetSRID(ST_MakePoint(:input_lon, :input_lat), 4326)) AS distance_meters
        FROM stops
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:input_lon, :input_lat), 4326)
        LIMIT 1;
    """)

    df_nearest_station = pd.read_sql(
        query,
        engine,
        params={"input_lon": address_long, "input_lat": address_lat}
    )

    if df_nearest_station.empty:
        return _get_station_via_name_resolver(address)

    station = df_nearest_station.to_dict(orient='records')[0]
    return {
        "station_name":        station['name'],
        "station_type":        station['mode'],
        "stop_id":             station['stop_id'],
        "distance_to_station": station['distance_meters'],
        "lat":                 station['lat'],
        "lng":                 station['lng'],
    }


def _get_station_via_name_resolver(address: str) -> dict | None:
    from stationname_resolver import resolve_stop_id
    stop_id = resolve_stop_id(address)
    if not stop_id:
        return None

    query = text("""
        SELECT stop_id, name, lat, lng, mode
        FROM stops
        WHERE stop_id = :stop_id
        LIMIT 1;
    """)

    df_station = pd.read_sql(query, engine, params={"stop_id": stop_id})
    if df_station.empty:
        return None

    station = df_station.to_dict(orient='records')[0]
    return {
        "station_name":        station['name'],
        "station_type":        station['mode'],
        "stop_id":             station['stop_id'],
        "distance_to_station": 0,
        "lat":                 station['lat'],
        "lng":                 station['lng'],
    }


# if __name__ == "__main__":
