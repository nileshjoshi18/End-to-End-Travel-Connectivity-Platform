# nearest_station.py
import os
import requests
import googlemaps
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import the train-finding logic
from logic_test import find_trains

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


# ── Helpers ──────────────────────────────────────────────────────────────────

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
    """
    Map a Google Places station name to your DB stop_id.
    Extend this mapping as your network grows.
    """
    NAME_TO_STOP_ID: dict[str, str] = {
        "Churchgate":          "CHU_WR",
        "Marine Lines":        "MAR_WR",
        "Charni Road":         "CHA_WR",
        "Grant Road":          "GRA_WR",
        "Mumbai Central":      "MUC_WR",
        "Mahalaxmi":           "MAH_WR",
        "Lower Parel":         "LOP_WR",
        "Prabhadevi":          "PRA_WR",
        "Dadar":               "DAD_WR",
        "Matunga Road":        "MAT_WR",
        "Mahim Junction":      "MAI_WR",
        "Bandra":              "BAN_WR",
        "Khar Road":           "KHA_WR",
        "Santacruz":           "SAN_WR",
        "Vile Parle":          "VIL_WR",
        "Andheri":             "AND_WR",
        "Jogeshwari":          "JOG_WR",
        "Ram Mandir":          "RAM_WR",
        "Goregaon":            "GOR_WR",
        "Malad":               "MAL_WR",
        "Kandivali":           "KAN_WR",
        "Borivali":            "BOR_WR",
        # Add CR / Harbour line stops as needed …
    }
    # Try exact match first, then partial
    if station_name in NAME_TO_STOP_ID:
        return NAME_TO_STOP_ID[station_name]
    for key, val in NAME_TO_STOP_ID.items():
        if key.lower() in station_name.lower() or station_name.lower() in key.lower():
            return val
    return None


def get_nearest_station(address: str) -> dict | None:
    geocode_result = gmaps.geocode(address)
    if not geocode_result:
        return None

    location = geocode_result[0]['geometry']['location']

    places_result = gmaps.places_nearby(location=location, rank_by='distance', type='train_station')
    if not places_result.get('results'):
        places_result = gmaps.places_nearby(location=location, rank_by='distance', type='transit_station')
    if not places_result.get('results'):
        return None

    EXCLUDE_WORDS = ["bus", "hq", "headquarter", "hospital", "metro", "monorail", "taxi"]
    rail_stations = [
        p for p in places_result['results']
        if not any(x in p['name'].lower() for x in EXCLUDE_WORDS)
    ][:5]

    if not rail_stations:
        return None

    destinations = [s['geometry']['location'] for s in rail_stations]
    matrix = gmaps.distance_matrix(origins=[location], destinations=destinations, mode="walking")
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

    best = rail_stations[best_idx]
    stop_id = get_station_stop_id(best['name'])

    return {
        "station_name":        best['name'],
        "stop_id":             stop_id,
        "distance_to_station": elements[best_idx]['distance']['text'],
        "walking_time":        elements[best_idx]['duration']['text'],
        "location":            best['geometry']['location'],
    }


# ── Endpoint ─────────────────────────────────────────────────────────────────

@app.get("/get-connectivity")
async def get_connectivity(source: str, destination: str):
    start_info = get_nearest_station(source)
    end_info   = get_nearest_station(destination)

    if not start_info or not end_info:
        raise HTTPException(status_code=404, detail="Could not find railway stations for these locations.")

    # Fetch current IST time
    current_time = get_current_ist_time()

    # Look up trains if we have valid stop IDs
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
        "trains": trains,   # list of {train_id, departure, arrival, duration}
    }