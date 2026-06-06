# nearest_station.py
import os
import requests
import googlemaps
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Import the train-finding logic
from logic_test import find_trains
from stationname_resolver import resolve_stop_id
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("NEXT_PUBLIC_GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise ValueError("Missing Google Maps API Key in environment variables.")

gmaps = googlemaps.Client(key=API_KEY)

def get_current_ist_time() -> str:
    """Fetch current IST time from WorldTimeAPI and return as HH:MM string."""
    try:
        resp = requests.get("https://worldtimeapi.org/api/timezone/Asia/Kolkata", timeout=5)
        resp.raise_for_status()
        dt_str = resp.json()["datetime"]   # e.g. "2025-04-11T14:32:10.123456+05:30"
        time_part = dt_str[11:16]          # "HH:MM"
        return time_part
    except Exception:
        # Fallback: use server's local time (acceptable if server is in IST)
        from datetime import datetime, timezone, timedelta
        ist = timezone(timedelta(hours=5, minutes=30))
        return datetime.now(ist).strftime("%H:%M")


def get_station_stop_id(station_name: str) -> str | None:
    return resolve_stop_id(station_name)

def get_nearest_station(address: str) -> dict | None:
    geocode_result = gmaps.geocode(address)
    if not geocode_result:
        return None

    location = geocode_result[0]['geometry']['location']

    EXCLUDE_WORDS = ["bus", "hq", "headquarter", "hospital", "monorail", "taxi"]

    # ✅ Two separate calls — one for train, one for metro
    all_results = []
    for station_type in ['train_station', 'metro_station']:
        result = gmaps.places_nearby(
            location=location,
            radius=6000,
            type=station_type
        )
        if result.get('results'):
            all_results.extend(result['results'])

    if not all_results:
        return None

    # Deduplicate by place_id
    seen = set()
    unique_stations = []
    for p in all_results:
        if p['place_id'] not in seen:
            seen.add(p['place_id'])
            unique_stations.append(p)

    rail_stations = [
        p for p in unique_stations
        if not any(x in p['name'].lower() for x in EXCLUDE_WORDS)
    ]

    if not rail_stations:
        return None
    candidates = rail_stations[:10]
    destinations = [s['geometry']['location'] for s in candidates]

    matrix = gmaps.distance_matrix(
        origins=[location],
        destinations=destinations,
        mode="walking"
    )
    if matrix['status'] != 'OK':
        return None

    elements = matrix['rows'][0]['elements']
    best_idx, min_meters = -1, float('inf')

    for i, e in enumerate(elements):
        if e['status'] == 'OK' and e['distance']['value'] < min_meters:
            min_meters = e['distance']['value']
            best_idx = i

    if best_idx == -1:
        return None

    best = candidates[best_idx]
    name_lower = best['name'].lower()
    types = best.get('types', [])
    is_metro = 'subway_station' in types or 'metro' in name_lower
    station_type_label = 'metro' if is_metro else 'local_train'

    stop_id = get_station_stop_id(best['name'])

    return {
        "station_name":        best['name'],
        "station_type":        station_type_label,   # 'metro' or 'local_train'
        "stop_id":             stop_id,
        "distance_to_station": elements[best_idx]['distance']['text'],
        "walking_time":        elements[best_idx]['duration']['text'],
        "location":            best['geometry']['location'],
    }

#Endpoint

@app.get("/get-connectivity")
def get_connectivity(source: str, destination: str):
    start_info = get_nearest_station(source)
    end_info   = get_nearest_station(destination)
    print(f"source: name='{start_info.get('station_name')}' stop_id='{start_info.get('stop_id')}'")
    print(f"dest:   name='{end_info.get('station_name')}'   stop_id='{end_info.get('stop_id')}'") 
    if not start_info or not end_info:
        raise HTTPException(status_code=404, detail="Could not find railway stations for these locations.")
    current_time = get_current_ist_time()
    trains = []
    if start_info.get("stop_id") and end_info.get("stop_id"):
        trains = find_trains(start_info["stop_id"], end_info["stop_id"], current_time)
    return {
        "current_time": current_time,
        "source_connectivity": {
            "station_name":        start_info["station_name"],
            "distance_to_station": start_info["distance_to_station"],
            "walking_time":        start_info["walking_time"],
        },
        "destination_connectivity": {
            "station_name":        end_info["station_name"],
            "distance_to_station": end_info["distance_to_station"],
            "walking_time":        end_info["walking_time"],
        },
        "trains": trains,  
    }
if __name__ == "__main__":
    print(get_connectivity("dav public school, nerul", "chembur station"))