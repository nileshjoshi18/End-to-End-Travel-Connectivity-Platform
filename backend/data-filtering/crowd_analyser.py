"""
crowd_analyser.py

Batch job: enriches every station in the `stops` table with a crowd score,
based on nearby office / commercial / retail / industrial / university density
from OpenStreetMap (via Overpass API).

Run this whenever you want to refresh crowd scores (e.g. monthly, or after
adding new stations to the DB). It reads all stations from `stops` and writes
results into `station_crowd_profile` -- nothing else in your DB is touched.

Usage:
    python crowd_analyser.py
"""

import asyncio
import httpx
from sqlalchemy import create_engine, text

# -- DB connection -- same as nearest_station.py -----------------------------
engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')

# -- Overpass config -----------------------------------------------------------
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_FALLBACK_URL = "https://overpass.kumi.systems/api/interpreter"  # alternate public mirror
HEADERS = {
    "User-Agent": "travel-buddy-app/1.0 (contact: your@email.com)",
    "Accept": "application/json",
    "Referer": "https://github.com/",  # public instance has been 406ing based on missing/bad Referer
}

# Correct OSM tag/value pairs -- these actually exist in the data.
# None as value means "tag exists with any value" (e.g. office=*)
POI_CATEGORIES = {
    "office":      ('office', None),
    "commercial":  ('building', 'commercial'),
    "industrial":  ('building', 'industrial'),
    "retail":      ('shop', None),
    "university":  ('amenity', 'university'),
}

WEIGHTS = {
    "office":     0.35,
    "commercial": 0.20,
    "retail":     0.20,
    "university": 0.10,
    "industrial": 0.00,
}

MAX_COUNT = 50
RADIUS_M = 1500


def _tag_filter(key: str, val: str | None) -> str:
    return f'["{key}"="{val}"]' if val else f'["{key}"]'


async def count_one_category(client: httpx.AsyncClient, lat: float, lng: float,
                               key: str, val: str | None, radius_m: int) -> int:
    """
    Queries BOTH node and way -- buildings (building=commercial/industrial) and many
    offices are tagged on ways (building footprints), not just nodes. Node-only
    queries systematically undercount these categories.
    """
    tag = _tag_filter(key, val)
    query = f"""
    [out:json][timeout:25];
    (
      node{tag}(around:{radius_m},{lat},{lng});
      way{tag}(around:{radius_m},{lat},{lng});
    );
    out count;
    """
    try:
        r = await client.post(OVERPASS_URL, data={"data": query}, headers=HEADERS)
        r.raise_for_status()
    except httpx.HTTPStatusError:
        # Public instance is currently unstable / rejecting some clients -- try mirror
        r = await client.post(OVERPASS_FALLBACK_URL, data={"data": query}, headers=HEADERS)
        r.raise_for_status()

    data = r.json()
    elements = data.get("elements", [])
    if not elements:
        return 0
    return int(elements[0].get("tags", {}).get("total", "0"))


async def count_pois_overpass(lat: float, lng: float, radius_m: int = RADIUS_M) -> dict:
    counts = {}
    async with httpx.AsyncClient(timeout=30, headers=HEADERS) as client:
        for category, (key, val) in POI_CATEGORIES.items():
            counts[category] = await count_one_category(client, lat, lng, key, val, radius_m)
            await asyncio.sleep(1)  # be polite to the public Overpass instance
    return counts


def compute_crowd_score(counts: dict) -> float:
    raw = sum(
        counts.get(cat, 0) * weight
        for cat, weight in WEIGHTS.items()
    )
    return round(min(1.0, raw / MAX_COUNT), 4)


# -- DB read/write --------------------------------------------------------------

def ensure_table_exists():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS station_crowd_profile (
                stop_id           TEXT PRIMARY KEY REFERENCES stops(stop_id),
                office_count      INT,
                commercial_count  INT,
                industrial_count  INT,
                retail_count      INT,
                university_count  INT,
                crowd_score       FLOAT,
                last_updated      TIMESTAMPTZ DEFAULT now()
            );
        """))


def get_all_stations() -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT stop_id, name, lat, lng FROM stops"))
        return [dict(row._mapping) for row in result]


def upsert_crowd_profile(stop_id: str, counts: dict, score: float):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO station_crowd_profile
                (stop_id, office_count, commercial_count, industrial_count,
                 retail_count, university_count, crowd_score, last_updated)
            VALUES
                (:stop_id, :office, :commercial, :industrial,
                 :retail, :university, :score, now())
            ON CONFLICT (stop_id) DO UPDATE SET
                office_count      = EXCLUDED.office_count,
                commercial_count  = EXCLUDED.commercial_count,
                industrial_count  = EXCLUDED.industrial_count,
                retail_count      = EXCLUDED.retail_count,
                university_count  = EXCLUDED.university_count,
                crowd_score       = EXCLUDED.crowd_score,
                last_updated      = now();
        """), {
            "stop_id": stop_id,
            "office": counts.get("office", 0),
            "commercial": counts.get("commercial", 0),
            "industrial": counts.get("industrial", 0),
            "retail": counts.get("retail", 0),
            "university": counts.get("university", 0),
            "score": score,
        })


# -- Main batch job ---------------------------------------------------------------

async def enrich_all_stations():
    ensure_table_exists()
    stations = get_all_stations()
    print(f"Found {len(stations)} stations. Starting enrichment...")

    for i, station in enumerate(stations, 1):
        stop_id = station["stop_id"]
        lat, lng = station["lat"], station["lng"]

        try:
            counts = await count_pois_overpass(lat, lng)
            score = compute_crowd_score(counts)
            upsert_crowd_profile(stop_id, counts, score)
            print(f"[{i}/{len(stations)}] {stop_id} ({station['name']}) -> {counts} -> score={score}")
        except Exception as e:
            print(f"[{i}/{len(stations)}] {stop_id} FAILED: {e}")

        await asyncio.sleep(1)  # extra politeness buffer between stations


if __name__ == "__main__":
    result = asyncio.run(count_pois_overpass(19.021424800332400, 73.019748852744800))
    print(result)
    # asyncio.run(enrich_all_stations())