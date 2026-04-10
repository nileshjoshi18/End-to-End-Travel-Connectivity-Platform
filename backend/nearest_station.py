import googlemaps
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Check
API_KEY = os.getenv("NEXT_PUBLIC_GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise ValueError("Missing Google Maps API Key in environment variables.")

gmaps = googlemaps.Client(key=API_KEY)

def get_nearest_station(address):
    # 1. Geocode the address
    geocode_result = gmaps.geocode(address)
    if not geocode_result:
        return None
    
    location = geocode_result[0]['geometry']['location']

    # 2. Search for stations
    # Use rank_by='distance' to ensure we get the physically closest results first
    # Note: 'radius' cannot be used with 'rank_by=distance'
    places_result = gmaps.places_nearby(
        location=location,
        rank_by='distance',
        type='train_station'
    )

    # Fallback if no 'train_station' type is found
    if not places_result.get('results'):
        places_result = gmaps.places_nearby(
            location=location,
            rank_by='distance',
            type='transit_station'
        )

    if not places_result.get('results'):
        return None

    # 3. Filter for actual Rail Stations
    # Mumbai specific: Include 'terminus' but keep 'metro' excluded for local train focus
    EXCLUDE_WORDS = ["bus", "hq", "headquarter", "hospital", "metro", "monorail", "taxi"]
    
    rail_stations = [
        p for p in places_result['results']
        if not any(x in p['name'].lower() for x in EXCLUDE_WORDS)
    ][:5]  # Take top 5 closest to check walking distance

    if not rail_stations:
        return None

    # 4. Calculate actual walking distance
    destinations = [s['geometry']['location'] for s in rail_stations]
    matrix = gmaps.distance_matrix(
        origins=[location],
        destinations=destinations,
        mode="walking"
    )

    if matrix['status'] != 'OK':
        return None

    elements = matrix['rows'][0]['elements']
    
    best_idx = -1
    min_meters = float('inf')

    for i, e in enumerate(elements):
        if e['status'] == 'OK':
            dist_val = e['distance']['value']
            if dist_val < min_meters:
                min_meters = dist_val
                best_idx = i

    if best_idx == -1:
        return None

    best_station = rail_stations[best_idx]

    return {
        "station_name": best_station['name'],
        "distance_to_station": elements[best_idx]['distance']['text'],
        "walking_time": elements[best_idx]['duration']['text'],
        "location": best_station['geometry']['location']
    }

@app.get("/get-connectivity")
async def get_connectivity(source: str, destination: str):
    start_info = get_nearest_station(source)
    end_info = get_nearest_station(destination)
    
    if not start_info or not end_info:
        raise HTTPException(status_code=404, detail="Could not find railway connectivity for these locations.")
        
    return {
        "source_connectivity": start_info,
        "destination_connectivity": end_info
    }

# Running instructions:
# uvicorn main:app --reload