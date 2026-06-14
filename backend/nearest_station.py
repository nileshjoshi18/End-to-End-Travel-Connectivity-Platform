# nearest_station.py
import os
import requests
import googlemaps
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from logic_test import find_trains
from stationname_resolver import resolve_stop_id
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from urllib.parse import quote

engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')
# load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API_KEY = os.getenv("NEXT_PUBLIC_GOOGLE_MAPS_API_KEY")
# if not API_KEY:
#     raise ValueError("Missing Google Maps API Key in environment variables.")

# gmaps = googlemaps.Client(key=API_KEY)

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

def get_station_stop_id(station_name: str) -> str | None:
    return resolve_stop_id(station_name)

def get_nearest_station(address: str) -> dict | None:
    encoded_address = quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1"
    headers = {
        "User-Agent": "MyAppName/1.0 (funnycornflakes174@gmail.com)"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if not data:
        return None

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
        return None

    station = df_nearest_station.to_dict(orient='records')[0]
    print(station)
    return {
        "station_name":        station['name'],
        "station_type":        station['mode'],
        "stop_id":             station['stop_id'],
        "distance_to_station": station['distance_meters'],
        "lat":                 station['lat'],
        "lng":                 station['lng'],
    }
    # return {
    #     "station_name":        best['name'],
    #     "station_type":        station_type_label,
    #     "stop_id":             stop_id,
    #     "distance_to_station": elements[best_idx]['distance']['text'],
    #     "walking_time":        elements[best_idx]['duration']['text'],
    #     "location":            best['geometry']['location'],
    # }


def singleRouteFare(source_stop: str, destination_stop: str, train_id: str):
    costs_by_sequence = [[0,3,5],[4,8,10],[9,15,15],[16,21,20],[22,30,25],[31,40,30]]

    df_stops_sequence = pd.read_sql("""
        SELECT rs.sequence_no, rs.stop_id FROM route_stops rs
        JOIN schedules s ON rs.route_id = s.route_id
        WHERE s.schedule_id = %(sid)s
        ORDER BY rs.sequence_no
    """, engine, params={"sid": train_id})

    stop_ids = df_stops_sequence['stop_id'].tolist()

    src_sequence = None
    des_sequence = None

    for i, stop in enumerate(stop_ids):
        if stop == source_stop:
            src_sequence = i
        elif stop == destination_stop and src_sequence is not None:
            des_sequence = i
            break

    if src_sequence is None or des_sequence is None:
        raise ValueError(f"Source or destination stop not found in route for train {train_id}")

    counts = des_sequence - src_sequence

    for list_cost_by_sequence in costs_by_sequence:
        if counts <= list_cost_by_sequence[1]:
            return list_cost_by_sequence[2]

    return costs_by_sequence[-1][2]  


@app.get("/get-connectivity")
def get_connectivity(source: str, destination: str):
    start_info = get_nearest_station(source)
    end_info = get_nearest_station(destination)

    if not start_info or not end_info:
        raise HTTPException(status_code=404, detail="Could not find railway stations for these locations.")

    current_time = get_current_ist_time()

    trains = []
    if start_info.get("stop_id") and end_info.get("stop_id"):
        trains = find_trains(start_info["stop_id"], end_info["stop_id"], current_time)
    fare = None
    if trains:
        fare = singleRouteFare(start_info["stop_id"], end_info["stop_id"], trains[0]['train_id'])

    return {
        "current_time": current_time,
        "source_connectivity": {
            "station_name":        start_info["station_name"],
            "distance_to_station": start_info["distance_to_station"],
            # "walking_time":        start_info["walking_time"],
        },
        "destination_connectivity": {
            "station_name":        end_info["station_name"],
            "distance_to_station": end_info["distance_to_station"],
            # "walking_time":        end_info["walking_time"],
        },
        "trains": trains,
        "fare": fare, 
    }


if __name__ == "__main__":
    # get_nearest_station("churchgate station")
    print(get_connectivity("seawoods hospital", "chembur station"))